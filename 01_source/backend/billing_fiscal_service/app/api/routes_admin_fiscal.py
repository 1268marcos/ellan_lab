from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.fiscal_reconciliation_gap import FiscalReconciliationGap
from app.models.invoice_delivery_log import InvoiceDeliveryLog
from app.models.invoice_model import Invoice
from app.services.invoice_orchestrator import ensure_and_process_invoice, ensure_invoice_for_order
from app.services.fiscal_reconciliation_service import (
    list_reconciliation_gaps,
    scan_and_persist_reconciliation_gaps,
)
from app.api.routes_invoice import _to_invoice_response
from app.services.fiscal_reporting_service import (
    build_saft_pt_export_payload,
    build_sped_efd_export_payload,
    collect_dead_letter_summary,
    get_issued_invoices_for_period,
)
from app.services.fiscal_provider_ops_service import list_provider_status, test_provider_connectivity
from app.integrations.fiscal_real_provider_client import list_canonical_error_codes
from app.services.invoice_delivery_service import record_invoice_delivery
from app.services.invoice_email_service import send_danfe_email_stub
from app.services.invoice_issue_service import reset_invoice_for_retry
from app.services.sefaz_svrs_batch_stub_service import (
    query_svrs_issue_batch_stub,
    reset_svrs_issue_batch_stub_state,
    submit_svrs_issue_batch_stub,
)
from app.services.financial_pnl_service import (
    calculate_monthly_kpis,
    list_daily_kpis,
    list_monthly_pnl,
    list_revenue_recognition,
    recompute_daily_kpis,
    recompute_daily_revenue_recognition,
    recompute_monthly_pnl,
)

router = APIRouter(prefix="/admin/fiscal", tags=["admin-fiscal"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


def _build_danfe_pdf_stub_base64(invoice: Invoice) -> str:
    """
    DANFE simplificado (stub): gera conteúdo textual com envelope PDF-like e retorna em base64.
    Em F-3 avançado substituir por renderer PDF real.
    """
    payload = {
        "doc": "DANFE_SIMPLIFIED_STUB_V1",
        "invoice_id": invoice.id,
        "order_id": invoice.order_id,
        "country": invoice.country,
        "invoice_number": invoice.invoice_number,
        "invoice_series": invoice.invoice_series,
        "access_key": invoice.access_key,
        "amount_cents": int(invoice.amount_cents or 0),
        "issued_at": invoice.issued_at.isoformat() if invoice.issued_at else None,
        "status": str(getattr(invoice.status, "value", invoice.status)),
    }
    body = json.dumps(payload, ensure_ascii=False)
    safe_body = body.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    text = f"DANFE STUB V1 - order_id={invoice.order_id} - invoice_id={invoice.id}\\n{safe_body}"

    objects: list[bytes] = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        (
            "4 0 obj\n"
            f"<< /Length {len(('BT /F1 10 Tf 40 800 Td (' + text + ') Tj ET').encode('latin-1', errors='replace'))} >>\n"
            "stream\n"
            f"BT /F1 10 Tf 40 800 Td ({text}) Tj ET\n"
            "endstream\n"
            "endobj\n"
        ).encode("latin-1", errors="replace"),
        b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf))
        pdf.extend(obj)
    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        pdf.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n"
        ).encode("ascii")
    )
    return base64.b64encode(bytes(pdf)).decode("ascii")


@router.get("/gaps")
def get_reconciliation_gaps(
    date: str | None = Query(default=None, description="YYYY-MM-DD"),
    status: str = Query(default="OPEN", pattern="^(OPEN|RESOLVED)?$"),
    refresh: bool = Query(default=False),
    limit: int = Query(default=200, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    date_from = None
    if date:
        date_from = datetime.fromisoformat(date)
    if refresh:
        scan_and_persist_reconciliation_gaps(db)
    rows = list_reconciliation_gaps(db, status=status, date_from=date_from, limit=limit)
    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "dedupe_key": r.dedupe_key,
                "gap_type": r.gap_type,
                "severity": r.severity,
                "status": r.status,
                "order_id": r.order_id,
                "invoice_id": r.invoice_id,
                "details_json": r.details_json,
                "first_detected_at": r.first_detected_at.isoformat() if r.first_detected_at else None,
                "last_detected_at": r.last_detected_at.isoformat() if r.last_detected_at else None,
                "resolved_at": r.resolved_at.isoformat() if r.resolved_at else None,
            }
            for r in rows
        ],
    }


@router.post("/force-issue/{order_id}")
def force_issue_order_invoice(
    order_id: str,
    refresh_after: bool = Query(default=True),
    allow_missing_paid_event: bool = Query(default=True),
    skip_consumer_fiscal_gate: bool = Query(
        default=False,
        description="Operação: ignora gate de perfil fiscal mínimo (ex.: dados legados ou ambiente de teste).",
    ),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    normalized_order_id = str(order_id).strip()
    if not normalized_order_id:
        raise HTTPException(status_code=400, detail="order_id is required")
    try:
        invoice = ensure_and_process_invoice(
            db,
            normalized_order_id,
            allow_missing_paid_event=allow_missing_paid_event,
            skip_consumer_fiscal_gate=skip_consumer_fiscal_gate,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    now = datetime.now(timezone.utc)
    paid_gap_key = f"paid_without_invoice:{normalized_order_id}"
    open_gap = (
        db.query(FiscalReconciliationGap)
        .filter(FiscalReconciliationGap.dedupe_key == paid_gap_key)
        .filter(FiscalReconciliationGap.status == "OPEN")
        .first()
    )
    if open_gap is not None:
        open_gap.status = "RESOLVED"
        open_gap.resolved_at = now
        open_gap.last_detected_at = now
        open_gap.invoice_id = invoice.id
        detail = dict(open_gap.details_json or {})
        detail["resolved_by"] = "admin_force_issue"
        detail["resolved_invoice_id"] = invoice.id
        open_gap.details_json = detail
        db.commit()

    if refresh_after:
        recon = scan_and_persist_reconciliation_gaps(db)
    else:
        recon = None

    return {
        "ok": True,
        "order_id": normalized_order_id,
        "invoice": _to_invoice_response(invoice).model_dump(),
        "resolved_gap_key": paid_gap_key if open_gap is not None else None,
        "reconciliation_refresh": recon,
    }


@router.get("/dead-letters")
def get_dead_letters_monitor(
    threshold: int = Query(default=10, ge=1, le=100000),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    return collect_dead_letter_summary(db, threshold=threshold)


@router.get("/exports/sped-efd")
def export_sped_efd(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoices = get_issued_invoices_for_period(db, year=year, month=month, country="BR")
    return build_sped_efd_export_payload(year=year, month=month, invoices=invoices)


@router.get("/exports/saft-pt")
def export_saft_pt(
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoices = get_issued_invoices_for_period(db, year=year, month=month, country="PT")
    return build_saft_pt_export_payload(year=year, month=month, invoices=invoices)


@router.get("/danfe/{invoice_id}/pdf")
def get_danfe_pdf_stub(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    content_b64 = _build_danfe_pdf_stub_base64(inv)
    return {
        "format": "pdf_stub_base64_v1",
        "invoice_id": inv.id,
        "order_id": inv.order_id,
        "filename": f"danfe-{inv.order_id}.pdf",
        "mime_type": "application/pdf",
        "content_base64": content_b64,
        "note": "Stub simplificado para operação; substituir por renderer PDF real no F-3 final.",
    }


@router.get("/providers/status")
def get_provider_status(
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    return {
        "items": list_provider_status(db),
        "canonical_error_codes": list_canonical_error_codes(),
    }


@router.post("/providers/test-connectivity")
def post_test_provider_connectivity(
    country: str = Query(default="ALL", pattern="^(ALL|BR|PT)$"),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    c = country.upper()
    if c == "ALL":
        return {
            "items": [
                test_provider_connectivity(db, country="BR"),
                test_provider_connectivity(db, country="PT"),
            ]
        }
    return {"items": [test_provider_connectivity(db, country=c)]}


@router.post("/providers/stub/svrs/batch-submit")
def post_svrs_batch_submit_stub(
    payload: dict,
    _: None = Depends(validate_internal_token),
):
    """
    F3A-STUB-03: simulador de lote SVRS/SEFAZ (assíncrono).
    Retorna recibo e aplica idempotência por `idempotency_key`.
    """
    try:
        out = submit_svrs_issue_batch_stub(payload or {})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **out}


@router.get("/providers/stub/svrs/batch-query")
def get_svrs_batch_query_stub(
    receipt_number: str = Query(...),
    _: None = Depends(validate_internal_token),
):
    try:
        out = query_svrs_issue_batch_stub(receipt_number)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"ok": True, **out}


@router.post("/providers/stub/svrs/batch-reset")
def post_svrs_batch_reset_stub(
    _: None = Depends(validate_internal_token),
):
    return reset_svrs_issue_batch_stub_state()


@router.post("/providers/stub/svrs/smoke-issue/{order_id}")
def post_svrs_smoke_issue_by_order(
    order_id: str,
    ready_after_polls: int = Query(default=1, ge=1, le=20),
    stub_batch_poll_count: int = Query(default=1, ge=1, le=20),
    idempotency_key: str | None = Query(default=None),
    allow_missing_paid_event: bool = Query(default=True),
    force_reprocess: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    One-click smoke test:
    - garante/cria invoice por order_id
    - injeta payload_json para stub_scenario=svrs_batch_async
    - processa emissão imediatamente
    """
    normalized_order_id = str(order_id or "").strip()
    if not normalized_order_id:
        raise HTTPException(status_code=400, detail="order_id is required")

    invoice = ensure_invoice_for_order(
        db,
        normalized_order_id,
        allow_missing_paid_event=allow_missing_paid_event,
    )

    payload = dict(invoice.payload_json or {})
    payload["stub_scenario"] = "svrs_batch_async"
    payload["ready_after_polls"] = int(ready_after_polls)
    payload["stub_batch_poll_count"] = int(stub_batch_poll_count)
    payload["idempotency_key"] = str(idempotency_key or "").strip() or f"smoke:{invoice.id}"
    payload["smoke_svrs_batch_async"] = True
    invoice.payload_json = payload
    db.commit()
    db.refresh(invoice)

    if force_reprocess:
        # Força reprocessamento do mesmo pedido/invoice para validar smoke
        # mesmo quando a invoice já está em ISSUED.
        invoice = reset_invoice_for_retry(db, invoice, clear_identifiers=True)

    processed = ensure_and_process_invoice(
        db,
        normalized_order_id,
        allow_missing_paid_event=allow_missing_paid_event,
    )
    return {
        "ok": True,
        "order_id": normalized_order_id,
        "invoice": _to_invoice_response(processed).model_dump(),
        "smoke_config": {
            "stub_scenario": "svrs_batch_async",
            "ready_after_polls": ready_after_polls,
            "stub_batch_poll_count": stub_batch_poll_count,
            "idempotency_key": payload["idempotency_key"],
            "force_reprocess": force_reprocess,
        },
        "note": (
            "Smoke test aplicado. Se status não for ISSUED na primeira chamada, "
            "repita o endpoint para validar retries/idempotência."
        ),
    }


@router.post("/invoices/{invoice_id}/resend-email")
def resend_invoice_email(
    invoice_id: str,
    cooldown_sec: int = Query(default=600, ge=60, le=86400),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    inv = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    now = datetime.now(timezone.utc)
    latest = (
        db.query(InvoiceDeliveryLog)
        .filter(InvoiceDeliveryLog.invoice_id == inv.id)
        .filter(InvoiceDeliveryLog.channel == "EMAIL_DANFE")
        .order_by(InvoiceDeliveryLog.created_at.desc())
        .first()
    )
    if latest and latest.created_at:
        elapsed = (now - latest.created_at).total_seconds()
        if elapsed < cooldown_sec:
            wait_sec = int(cooldown_sec - elapsed)
            record_invoice_delivery(
                db,
                invoice_id=inv.id,
                channel="EMAIL_DANFE",
                status="RESEND_RATE_LIMITED",
                detail={"cooldown_sec": cooldown_sec, "wait_sec": wait_sec},
            )
            db.commit()
            raise HTTPException(
                status_code=429,
                detail=f"Reenvio em cooldown. Aguarde {wait_sec}s.",
            )

    record_invoice_delivery(
        db,
        invoice_id=inv.id,
        channel="EMAIL_DANFE",
        status="RESEND_REQUESTED",
        detail={"requested_at": now.isoformat(), "source": "admin_api"},
    )
    send_danfe_email_stub(db, invoice=inv, template="issued", extra_detail={"resend": True})
    db.commit()
    return {
        "ok": True,
        "invoice_id": inv.id,
        "order_id": inv.order_id,
        "status": "RESEND_QUEUED",
    }


@router.get("/ledger-compat/audit")
def get_ledger_compat_audit(
    external_reference: str | None = Query(default=None, description="dedupe_key/external_reference"),
    event_type: str | None = Query(default=None),
    only_mismatches: bool = Query(default=False),
    from_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    to_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    Auditoria operacional rápida:
    compara lado a lado journal_entries (fonte primária) vs financial_ledger (compat layer)
    usando external_reference == dedupe_key.
    """
    clauses = ["1=1"]
    params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
    if external_reference:
        clauses.append("fl.external_reference = :external_reference")
        params["external_reference"] = external_reference.strip()
    if event_type:
        clauses.append("COALESCE(fl.metadata->>'event_type', je.reference_type) = :event_type")
        params["event_type"] = event_type.strip().upper()
    if from_date:
        clauses.append("COALESCE(je.created_at, fl.created_at)::date >= :from_date")
        params["from_date"] = from_date
    if to_date:
        clauses.append("COALESCE(je.created_at, fl.created_at)::date <= :to_date")
        params["to_date"] = to_date
    if only_mismatches:
        clauses.append(
            """
            (
                je.id IS NULL
                OR COALESCE((SELECT SUM(jel.debit_amount) FROM journal_entry_lines jel WHERE jel.journal_entry_id = je.id), 0)
                   <> COALESCE((SELECT SUM(jel.credit_amount) FROM journal_entry_lines jel WHERE jel.journal_entry_id = je.id), 0)
                OR fl.amount_cents
                   <> CAST(
                       ROUND(
                           COALESCE((SELECT SUM(jel.debit_amount) FROM journal_entry_lines jel WHERE jel.journal_entry_id = je.id), 0)
                           * 100
                       ) AS BIGINT
                   )
            )
            """
        )

    rows = db.execute(
        text(
            f"""
            SELECT
                fl.external_reference,
                fl.entry_type AS ledger_entry_type,
                fl.amount_cents AS ledger_amount_cents,
                fl.currency AS ledger_currency,
                fl.status AS ledger_status,
                fl.metadata AS ledger_metadata,
                fl.created_at AS ledger_created_at,
                je.id AS journal_entry_id,
                je.reference_type AS journal_reference_type,
                je.description AS journal_description,
                je.currency AS journal_currency,
                je.created_at AS journal_created_at,
                COALESCE((
                    SELECT SUM(jel.debit_amount) FROM journal_entry_lines jel
                    WHERE jel.journal_entry_id = je.id
                ), 0) AS journal_debit_total,
                COALESCE((
                    SELECT SUM(jel.credit_amount) FROM journal_entry_lines jel
                    WHERE jel.journal_entry_id = je.id
                ), 0) AS journal_credit_total
            FROM financial_ledger fl
            LEFT JOIN journal_entries je
                ON je.dedupe_key = fl.external_reference
            WHERE {' AND '.join(clauses)}
            ORDER BY COALESCE(je.created_at, fl.created_at) DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    count_row = db.execute(
        text(
            f"""
            SELECT COUNT(*)
            FROM financial_ledger fl
            LEFT JOIN journal_entries je
                ON je.dedupe_key = fl.external_reference
            WHERE {' AND '.join(clauses)}
            """
        ),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).fetchone()

    items = []
    for r in rows:
        ledger_amount_cents = int(r.get("ledger_amount_cents") or 0)
        journal_debit_total = r.get("journal_debit_total")
        journal_credit_total = r.get("journal_credit_total")
        journal_balanced = (
            journal_debit_total is not None
            and journal_credit_total is not None
            and journal_debit_total == journal_credit_total
        )
        journal_amount_cents_derived = None
        if journal_debit_total is not None:
            journal_amount_cents_derived = int(round(float(journal_debit_total) * 100))
        amount_matches = (
            journal_amount_cents_derived is not None
            and ledger_amount_cents == journal_amount_cents_derived
        )

        items.append(
            {
                "external_reference": r.get("external_reference"),
                "event_type": (
                    (r.get("ledger_metadata") or {}).get("event_type")
                    if isinstance(r.get("ledger_metadata"), dict)
                    else None
                )
                or r.get("journal_reference_type"),
                "ledger": {
                    "entry_type": r.get("ledger_entry_type"),
                    "amount_cents": ledger_amount_cents,
                    "currency": r.get("ledger_currency"),
                    "status": r.get("ledger_status"),
                    "created_at": r.get("ledger_created_at").isoformat() if r.get("ledger_created_at") else None,
                    "metadata": r.get("ledger_metadata") or {},
                },
                "journal": {
                    "journal_entry_id": r.get("journal_entry_id"),
                    "reference_type": r.get("journal_reference_type"),
                    "description": r.get("journal_description"),
                    "currency": r.get("journal_currency"),
                    "created_at": r.get("journal_created_at").isoformat() if r.get("journal_created_at") else None,
                    "debit_total": str(journal_debit_total) if journal_debit_total is not None else None,
                    "credit_total": str(journal_credit_total) if journal_credit_total is not None else None,
                    "is_balanced": journal_balanced,
                    "amount_cents_derived": journal_amount_cents_derived,
                },
                "audit": {
                    "has_journal_entry": r.get("journal_entry_id") is not None,
                    "journal_balanced": journal_balanced,
                    "amount_matches_compat": amount_matches,
                },
            }
        )

    return {
        "count": len(items),
        "total": int(count_row[0] if count_row else 0),
        "limit": limit,
        "offset": offset,
        "only_mismatches": only_mismatches,
        "items": items,
    }


@router.post("/pnl/recompute")
def post_recompute_monthly_pnl(
    month: str | None = Query(default=None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    target = None
    if month:
        try:
            parts = month.strip().split("-")
            target = datetime(int(parts[0]), int(parts[1]), 1).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.") from exc
    return {"ok": True, **recompute_monthly_pnl(db, month=target)}


@router.get("/pnl/monthly")
def get_monthly_pnl(
    month: str | None = Query(default=None, description="YYYY-MM"),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    target = None
    if month:
        try:
            parts = month.strip().split("-")
            target = datetime(int(parts[0]), int(parts[1]), 1).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.") from exc
    return list_monthly_pnl(db, month=target, limit=limit, offset=offset)


@router.get("/kpi/monthly")
def get_monthly_financial_kpis(
    month: str | None = Query(default=None, description="YYYY-MM"),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    target = None
    if month:
        try:
            parts = month.strip().split("-")
            target = datetime(int(parts[0]), int(parts[1]), 1).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.") from exc
    return calculate_monthly_kpis(db, month=target)


@router.post("/revenue-recognition/recompute")
def post_recompute_daily_revenue_recognition(
    date_ref: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    target = None
    if date_ref:
        try:
            target = datetime.fromisoformat(date_ref).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from exc
    return {"ok": True, **recompute_daily_revenue_recognition(db, snapshot_date=target)}


@router.get("/revenue-recognition")
def get_revenue_recognition(
    from_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    to_date: str | None = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    start = None
    end = None
    if from_date:
        try:
            start = datetime.fromisoformat(from_date).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use YYYY-MM-DD.") from exc
    if to_date:
        try:
            end = datetime.fromisoformat(to_date).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid to_date format. Use YYYY-MM-DD.") from exc
    return list_revenue_recognition(db, from_date=start, to_date=end, limit=limit, offset=offset)


@router.post("/kpi/daily/recompute")
def post_recompute_daily_kpis(
    date_ref: str | None = Query(default=None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    target = None
    if date_ref:
        try:
            target = datetime.fromisoformat(date_ref).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from exc
    return {"ok": True, **recompute_daily_kpis(db, snapshot_date=target)}


@router.get("/kpi/daily")
def get_daily_kpis(
    date_ref: str | None = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    target = None
    if date_ref:
        try:
            target = datetime.fromisoformat(date_ref).date()
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from exc
    return list_daily_kpis(db, snapshot_date=target, limit=limit, offset=offset)


@router.get("/timescale/status")
def get_timescale_status(
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    ext_row = db.execute(
        text(
            """
            SELECT extname, extversion
            FROM pg_extension
            WHERE extname = 'timescaledb'
            """
        )
    ).mappings().first()
    ext_ok = bool(ext_row)

    hypertable_rows = (
        db.execute(
            text(
                """
                SELECT hypertable_schema, hypertable_name
                FROM timescaledb_information.hypertables
                WHERE hypertable_schema = 'public'
                  AND hypertable_name IN (
                      'ellanlab_revenue_recognition',
                      'financial_kpi_daily',
                      'ellanlab_monthly_pnl'
                  )
                ORDER BY hypertable_name
                """
            )
        ).mappings().all()
        if ext_ok
        else []
    )
    job_rows = (
        db.execute(
            text(
                """
                SELECT hypertable_name, proc_name, schedule_interval
                FROM timescaledb_information.jobs
                WHERE hypertable_schema = 'public'
                  AND hypertable_name IN (
                      'ellanlab_revenue_recognition',
                      'financial_kpi_daily',
                      'ellanlab_monthly_pnl'
                  )
                  AND proc_name IN ('policy_compression', 'policy_retention')
                ORDER BY hypertable_name, proc_name
                """
            )
        ).mappings().all()
        if ext_ok
        else []
    )
    dedupe_count = (
        int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)::INT
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname IN ('ux_err_dedupe_key_time', 'ux_fkd_dedupe_key_time')
                    """
                )
            ).scalar_one()
        )
        if ext_ok
        else 0
    )

    hypertable_count = len(hypertable_rows)
    policy_count = len(job_rows)
    smoke_ok = ext_ok and hypertable_count == 3 and policy_count == 6 and dedupe_count == 2
    return {
        "ext_ok": ext_ok,
        "extension": dict(ext_row) if ext_row else None,
        "hypertable_count": hypertable_count,
        "policy_count": policy_count,
        "dedupe_index_count": dedupe_count,
        "smoke_result": "SMOKE_OK" if smoke_ok else "SMOKE_FAIL",
        "hypertables": [dict(r) for r in hypertable_rows],
        "jobs": [
            {
                **dict(r),
                "schedule_interval": str(r.get("schedule_interval")) if r.get("schedule_interval") is not None else None,
            }
            for r in job_rows
        ],
    }
