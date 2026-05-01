from __future__ import annotations

import base64
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query
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
from app.services.fiscal_provider_ops_service import (
    build_br_go_no_go_checklist,
    build_pt_go_no_go_checklist,
    list_provider_status,
    test_provider_connectivity,
)
from app.services.fiscal_global_catalog_service import (
    build_fiscal_fg1_wave_scope,
    build_fiscal_global_catalog,
    build_fiscal_global_scenario_matrix,
)
from app.services.fiscal_fg1_stub_service import (
    build_fg1_coverage_gate,
    validate_fg1_envelope_contract,
    build_fg1_stub_wave_readiness,
    build_fg1_fixture_inventory,
    build_fg1_fixtures_matrix,
    build_fg1_stub_adapters_catalog,
    read_fg1_fixture_document,
    simulate_fg1_stub,
)
from app.services.fiscal_fg1_readiness_service import (
    build_fg1_readiness_action_plan,
    build_fg1_readiness_gate,
)
from app.integrations.fiscal_real_provider_client import list_canonical_error_codes
from app.services.invoice_delivery_service import record_invoice_delivery
from app.services.invoice_email_service import send_danfe_email_stub
from app.services.invoice_issue_service import reset_invoice_for_retry
from app.services.sefaz_svrs_batch_stub_service import (
    query_svrs_issue_batch_stub,
    reset_svrs_issue_batch_stub_state,
    submit_svrs_issue_batch_stub,
)
from app.services.at_pt_stub_gateway_service import (
    reset_at_pt_stub_gateway_state,
    submit_at_pt_stub_cancel,
    submit_at_pt_stub_issue,
)
from app.services.fiscal_a1_dry_run_service import (
    build_a1_dry_run_status_payload,
    verify_a1_dry_run_signature,
)
from app.services.fiscal_release_gate_service import build_fiscal_release_gate_payload
from app.services.accounting_partner_settlement_reconcile_service import build_partner_settlement_reconcile_report
from app.services.accounting_revenue_credits_delta_service import build_revenue_credits_delta_report
from app.services.financial_pnl_service import (
    calculate_monthly_kpis,
    list_daily_kpis,
    list_monthly_pnl,
    list_revenue_recognition,
    recompute_daily_kpis,
    recompute_daily_revenue_recognition,
    recompute_monthly_pnl,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/fiscal", tags=["admin-fiscal"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


def _safe_client_error(message: str = "Invalid request payload.") -> HTTPException:
    return HTTPException(status_code=400, detail=message)


def _compute_accounting_approval_changed(current_payload: object, previous_payload: object) -> list[dict[str, object]]:
    """Same field-level diff as compare_accounting_approval_snapshots (D15/D17)."""
    cur = current_payload if isinstance(current_payload, dict) else {}
    prev = previous_payload if isinstance(previous_payload, dict) else {}
    cur_approval = cur.get("approval") if isinstance(cur.get("approval"), dict) else {}
    prev_approval = prev.get("approval") if isinstance(prev.get("approval"), dict) else {}
    cur_d13 = cur.get("d13_critical_checklist") if isinstance(cur.get("d13_critical_checklist"), dict) else {}
    prev_d13 = prev.get("d13_critical_checklist") if isinstance(prev.get("d13_critical_checklist"), dict) else {}
    changed: list[dict[str, object]] = []
    if str(cur_approval.get("owner") or "") != str(prev_approval.get("owner") or ""):
        changed.append({"field": "approval.owner", "current": cur_approval.get("owner"), "previous": prev_approval.get("owner")})
    if str(cur_approval.get("status") or "") != str(prev_approval.get("status") or ""):
        changed.append({"field": "approval.status", "current": cur_approval.get("status"), "previous": prev_approval.get("status")})
    if str(cur_approval.get("eta") or "") != str(prev_approval.get("eta") or ""):
        changed.append({"field": "approval.eta", "current": cur_approval.get("eta"), "previous": prev_approval.get("eta")})
    if int(cur_d13.get("done_items") or 0) != int(prev_d13.get("done_items") or 0):
        changed.append(
            {
                "field": "d13_critical_checklist.done_items",
                "current": int(cur_d13.get("done_items") or 0),
                "previous": int(prev_d13.get("done_items") or 0),
            }
        )
    if int(cur_d13.get("total_items") or 0) != int(prev_d13.get("total_items") or 0):
        changed.append(
            {
                "field": "d13_critical_checklist.total_items",
                "current": int(cur_d13.get("total_items") or 0),
                "previous": int(prev_d13.get("total_items") or 0),
            }
        )
    return changed


def _fingerprint_accounting_diff(changed: list[dict[str, object]]) -> str:
    if not changed:
        return ""
    keyable = sorted(
        (
            str(c.get("field")),
            json.dumps(c.get("current"), sort_keys=True, default=str),
            json.dumps(c.get("previous"), sort_keys=True, default=str),
        )
        for c in changed
    )
    return json.dumps(keyable, separators=(",", ":"))


def _ensure_accounting_approvals_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS fiscal_accounting_approvals (
                id VARCHAR(80) PRIMARY KEY,
                owner VARCHAR(160) NOT NULL,
                eta TIMESTAMPTZ NULL,
                status VARCHAR(80) NOT NULL,
                payload_json JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_created_at
                ON fiscal_accounting_approvals (created_at DESC);
            """
        )
    )
    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS ix_fiscal_accounting_approvals_status
                ON fiscal_accounting_approvals (status);
            """
        )
    )
    db.commit()


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


@router.post("/gaps/seed")
def seed_reconciliation_gaps_for_ops(
    batch_id: str = Query(default="batch_ops_d11_001"),
    partner_id: str = Query(default="partner_demo_001"),
    keep_existing_open: bool = Query(default=True),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    Seed operacional para testes de Sprint 2 D11.
    Cria gaps sintéticos com order_id/invoice_id e metadados de partner/batch
    para validar triagem e export por lote no painel OPS.
    """
    now = datetime.now(timezone.utc)
    normalized_batch = str(batch_id or "").strip() or "batch_ops_d11_001"
    normalized_partner = str(partner_id or "").strip() or "partner_demo_001"

    if not keep_existing_open:
        db.execute(
            text(
                """
                UPDATE fiscal_reconciliation_gaps
                   SET status = 'RESOLVED',
                       resolved_at = :now
                 WHERE status = 'OPEN'
                """
            ),
            {"now": now},
        )

    created: list[str] = []
    templates = [
        {
            "gap_type": "PAID_WITHOUT_INVOICE",
            "severity": "ERROR",
            "order_suffix": "001",
            "invoice_id": None,
            "amount_delta_cents": 1590,
            "message": "Pagamento confirmado sem invoice emitida.",
        },
        {
            "gap_type": "ISSUED_WITHOUT_PAID",
            "severity": "ERROR",
            "order_suffix": "002",
            "invoice_id": "inv_ops_d11_002",
            "amount_delta_cents": -780,
            "message": "Invoice emitida sem evento de pagamento correspondente.",
        },
        {
            "gap_type": "FISCAL_PROVIDER_MISMATCH",
            "severity": "WARN",
            "order_suffix": "003",
            "invoice_id": "inv_ops_d11_003",
            "amount_delta_cents": 240,
            "message": "Divergência de payload entre provider e trilha local.",
        },
    ]

    for item in templates:
        order_id = f"ord_ops_d11_{item['order_suffix']}"
        dedupe_key = f"ops_seed:{normalized_batch}:{item['gap_type']}:{order_id}"
        existing = (
            db.query(FiscalReconciliationGap)
            .filter(FiscalReconciliationGap.dedupe_key == dedupe_key)
            .first()
        )
        if existing:
            existing.status = "OPEN"
            existing.severity = item["severity"]
            existing.order_id = order_id
            existing.invoice_id = item["invoice_id"]
            existing.last_detected_at = now
            existing.resolved_at = None
            existing.details_json = {
                "message": item["message"],
                "partner_id": normalized_partner,
                "batch_id": normalized_batch,
                "country": "BR",
                "amount_delta_cents": item["amount_delta_cents"],
                "seed": True,
                "seed_version": "d11_v1",
            }
            created.append(existing.id)
            continue

        gap = FiscalReconciliationGap(
            id=f"frg_seed_{uuid.uuid4().hex[:20]}",
            dedupe_key=dedupe_key,
            gap_type=item["gap_type"],
            severity=item["severity"],
            status="OPEN",
            order_id=order_id,
            invoice_id=item["invoice_id"],
            details_json={
                "message": item["message"],
                "partner_id": normalized_partner,
                "batch_id": normalized_batch,
                "country": "BR",
                "amount_delta_cents": item["amount_delta_cents"],
                "seed": True,
                "seed_version": "d11_v1",
            },
            first_detected_at=now,
            last_detected_at=now,
        )
        db.add(gap)
        created.append(gap.id)

    db.commit()
    return {
        "ok": True,
        "seed_batch_id": normalized_batch,
        "seed_partner_id": normalized_partner,
        "created_or_updated": len(created),
        "ids": created,
    }


def _as_trace_value(value: object, fallback: str) -> str:
    text_value = str(value or "").strip()
    return text_value if text_value else fallback


@router.get("/global/sprint3/e2e-audit-trail")
def get_sprint3_e2e_audit_trail(
    date: str | None = Query(default=None, description="YYYY-MM-DD"),
    status: str = Query(default="OPEN", pattern="^(OPEN|RESOLVED)?$"),
    limit: int = Query(default=200, ge=1, le=1000),
    refresh: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    Sprint 3 P0-1:
    trilha ponta a ponta com materialização completa de chaves de auditoria
    (order_id, invoice_id, partner_id, batch_id) para handoff operacional.
    """
    date_from = None
    if date:
        date_from = datetime.fromisoformat(date)
    if refresh:
        scan_and_persist_reconciliation_gaps(db)

    rows = list_reconciliation_gaps(db, status=status, date_from=date_from, limit=limit)
    raw_complete = 0
    materialized_complete = 0
    items: list[dict[str, object]] = []
    latest_seen_at = None
    for row in rows:
        details = row.details_json if isinstance(row.details_json, dict) else {}
        raw_order = str(row.order_id or "").strip()
        raw_invoice = str(row.invoice_id or details.get("invoice_id") or "").strip()
        raw_partner = str(details.get("partner_id") or "").strip()
        raw_batch = str(details.get("batch_id") or "").strip()
        raw_ok = bool(raw_order and raw_invoice and raw_partner and raw_batch)
        if raw_ok:
            raw_complete += 1

        trace_order_id = _as_trace_value(raw_order, f"UNKNOWN_ORDER::{row.id}")
        trace_invoice_id = _as_trace_value(raw_invoice, f"PENDING_INVOICE::{trace_order_id}")
        trace_partner_id = _as_trace_value(raw_partner, "UNKNOWN_PARTNER")
        trace_batch_id = _as_trace_value(raw_batch, f"BATCH_UNSPECIFIED::{status}")
        materialized_ok = bool(trace_order_id and trace_invoice_id and trace_partner_id and trace_batch_id)
        if materialized_ok:
            materialized_complete += 1

        seen_at = row.last_detected_at.isoformat() if row.last_detected_at else None
        latest_seen_at = max(latest_seen_at or seen_at, seen_at) if seen_at else latest_seen_at
        items.append(
            {
                "id": row.id,
                "gap_type": row.gap_type,
                "severity": row.severity,
                "status": row.status,
                "trace": {
                    "order_id": trace_order_id,
                    "invoice_id": trace_invoice_id,
                    "partner_id": trace_partner_id,
                    "batch_id": trace_batch_id,
                },
                "trace_quality": {
                    "raw_complete": raw_ok,
                    "materialized_complete": materialized_ok,
                },
                "last_detected_at": seen_at,
            }
        )

    total = len(items)
    raw_rate = (raw_complete / total) if total > 0 else 1.0
    materialized_rate = (materialized_complete / total) if total > 0 else 1.0
    decision = "GO" if materialized_rate >= 1.0 else "NO_GO"
    generated_at = datetime.now(timezone.utc).isoformat()
    handoff_evidence_id = f"sprint3-e2e-audit::{generated_at}::{status}::{total}"
    return {
        "scope": "SPRINT3_P0_1_E2E_AUDIT_TRAIL",
        "audit_version": "sprint3-e2e-audit-v1",
        "generated_at": generated_at,
        "decision": decision,
        "coverage": {
            "total": total,
            "raw_complete": raw_complete,
            "materialized_complete": materialized_complete,
            "raw_rate": round(raw_rate, 4),
            "materialized_rate": round(materialized_rate, 4),
            "target_rate": 1.0,
        },
        "handoff_evidence": {
            "evidence_id": handoff_evidence_id,
            "latest_seen_at": latest_seen_at,
            "status_filter": status,
            "date_filter": date,
            "limit": int(limit),
        },
        "items": items,
    }


@router.post("/accounting-approvals")
def post_accounting_approval(
    payload: dict,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    _ensure_accounting_approvals_table(db)
    body = payload if isinstance(payload, dict) else {}
    approval = body.get("approval") if isinstance(body.get("approval"), dict) else {}
    owner = str(approval.get("owner") or "").strip() or "UNASSIGNED"
    status = str(approval.get("status") or "PENDING_REVIEW").strip() or "PENDING_REVIEW"
    eta_raw = str(approval.get("eta") or "").strip()
    eta_value = None
    if eta_raw:
        try:
            eta_value = datetime.fromisoformat(eta_raw.replace("Z", "+00:00"))
        except Exception as exc:
            raise _safe_client_error("Invalid approval.eta datetime format.") from exc

    row_id = f"faa_{uuid.uuid4().hex[:24]}"
    now = datetime.now(timezone.utc)
    db.execute(
        text(
            """
            INSERT INTO fiscal_accounting_approvals (
                id, owner, eta, status, payload_json, created_at, updated_at
            )
            VALUES (
                :id, :owner, :eta, :status, CAST(:payload_json AS JSONB), :created_at, :updated_at
            )
            """
        ),
        {
            "id": row_id,
            "owner": owner,
            "eta": eta_value,
            "status": status,
            "payload_json": json.dumps(body),
            "created_at": now,
            "updated_at": now,
        },
    )
    db.commit()
    return {
        "ok": True,
        "id": row_id,
        "owner": owner,
        "status": status,
        "eta": eta_value.isoformat() if eta_value else None,
        "created_at": now.isoformat(),
    }


@router.get("/accounting-approvals/latest")
def get_latest_accounting_approval(
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    _ensure_accounting_approvals_table(db)
    row = db.execute(
        text(
            """
            SELECT id, owner, eta, status, payload_json, created_at, updated_at
              FROM fiscal_accounting_approvals
             ORDER BY created_at DESC
             LIMIT 1
            """
        )
    ).mappings().first()
    if not row:
        return {"ok": True, "item": None}
    return {
        "ok": True,
        "item": {
            "id": row.get("id"),
            "owner": row.get("owner"),
            "eta": row.get("eta").isoformat() if row.get("eta") else None,
            "status": row.get("status"),
            "payload_json": row.get("payload_json") or {},
            "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
            "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
        },
    }


@router.get("/accounting-approvals")
def list_accounting_approvals(
    owner: str | None = Query(default=None),
    status: str | None = Query(default=None),
    date_from: str | None = Query(default=None, description="YYYY-MM-DD"),
    date_to: str | None = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    _ensure_accounting_approvals_table(db)
    where_parts = ["1=1"]
    params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
    if owner and str(owner).strip():
        where_parts.append("LOWER(owner) LIKE LOWER(:owner)")
        params["owner"] = f"%{str(owner).strip()}%"
    if status and str(status).strip():
        where_parts.append("status = :status")
        params["status"] = str(status).strip()
    if date_from and str(date_from).strip():
        where_parts.append("created_at::date >= :date_from")
        params["date_from"] = str(date_from).strip()
    if date_to and str(date_to).strip():
        where_parts.append("created_at::date <= :date_to")
        params["date_to"] = str(date_to).strip()

    where_sql = " AND ".join(where_parts)
    rows = db.execute(
        text(
            f"""
            SELECT id, owner, eta, status, payload_json, created_at, updated_at
              FROM fiscal_accounting_approvals
             WHERE {where_sql}
             ORDER BY created_at DESC
             LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()
    total_row = db.execute(
        text(
            f"""
            SELECT COUNT(*)::INT AS total
              FROM fiscal_accounting_approvals
             WHERE {where_sql}
            """
        ),
        {k: v for k, v in params.items() if k not in ("limit", "offset")},
    ).mappings().first()

    items = [
        {
            "id": row.get("id"),
            "owner": row.get("owner"),
            "eta": row.get("eta").isoformat() if row.get("eta") else None,
            "status": row.get("status"),
            "payload_json": row.get("payload_json") or {},
            "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
            "updated_at": row.get("updated_at").isoformat() if row.get("updated_at") else None,
        }
        for row in rows
    ]
    return {
        "ok": True,
        "count": len(items),
        "total": int((total_row or {}).get("total") or 0),
        "limit": int(limit),
        "offset": int(offset),
        "items": items,
    }


@router.get("/accounting-approvals/compare")
def compare_accounting_approval_snapshots(
    current_id: str | None = Query(default=None),
    previous_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    _ensure_accounting_approvals_table(db)

    def _fetch_snapshot(sid: str | None, *, nth_latest: int = 1):
        if sid and str(sid).strip():
            return db.execute(
                text(
                    """
                    SELECT id, owner, eta, status, payload_json, created_at
                      FROM fiscal_accounting_approvals
                     WHERE id = :id
                     LIMIT 1
                    """
                ),
                {"id": str(sid).strip()},
            ).mappings().first()
        return db.execute(
            text(
                """
                SELECT id, owner, eta, status, payload_json, created_at
                  FROM fiscal_accounting_approvals
                 ORDER BY created_at DESC
                 LIMIT 1 OFFSET :offset
                """
            ),
            {"offset": max(0, nth_latest - 1)},
        ).mappings().first()

    current = _fetch_snapshot(current_id, nth_latest=1)
    previous = _fetch_snapshot(previous_id, nth_latest=2)
    if not current:
        return {"ok": True, "current": None, "previous": None, "diff": {"summary": "Sem snapshots para comparar."}}
    if not previous:
        return {
            "ok": True,
            "current": {
                "id": current.get("id"),
                "owner": current.get("owner"),
                "eta": current.get("eta").isoformat() if current.get("eta") else None,
                "status": current.get("status"),
                "created_at": current.get("created_at").isoformat() if current.get("created_at") else None,
            },
            "previous": None,
            "diff": {"summary": "Apenas um snapshot disponível.", "changed": []},
        }

    current_payload = current.get("payload_json") if isinstance(current.get("payload_json"), dict) else {}
    previous_payload = previous.get("payload_json") if isinstance(previous.get("payload_json"), dict) else {}
    changed = _compute_accounting_approval_changed(current_payload, previous_payload)
    return {
        "ok": True,
        "current": {
            "id": current.get("id"),
            "owner": current.get("owner"),
            "eta": current.get("eta").isoformat() if current.get("eta") else None,
            "status": current.get("status"),
            "created_at": current.get("created_at").isoformat() if current.get("created_at") else None,
        },
        "previous": {
            "id": previous.get("id"),
            "owner": previous.get("owner"),
            "eta": previous.get("eta").isoformat() if previous.get("eta") else None,
            "status": previous.get("status"),
            "created_at": previous.get("created_at").isoformat() if previous.get("created_at") else None,
        },
        "diff": {
            "summary": "Mudanças detectadas entre snapshots." if changed else "Sem diferenças relevantes.",
            "changed": changed,
        },
    }


def _payload_json_as_dict(raw: object) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


@router.get("/accounting-approvals/divergence-health")
def get_accounting_approvals_divergence_health(
    window: int = Query(default=8, ge=3, le=30),
    prolonged_edges: int = Query(
        default=3,
        ge=2,
        le=15,
        description="Mínimo de bordas consecutivas (par snapshot i vs i+1) com o mesmo diff não vazio.",
    ),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    D17: detecta se o mesmo diff de governança se repete em vários snapshots seguidos (divergência prolongada).
    """
    _ensure_accounting_approvals_table(db)
    rows = db.execute(
        text(
            """
            SELECT id, owner, eta, status, payload_json, created_at
              FROM fiscal_accounting_approvals
             ORDER BY created_at DESC
             LIMIT :lim
            """
        ),
        {"lim": int(window)},
    ).mappings().all()
    if len(rows) < 2:
        return {
            "ok": True,
            "snapshots_considered": len(rows),
            "edges": [],
            "latest_pair_has_diff": False,
            "prolonged_identical_diff": False,
            "prolonged_detail": None,
            "note": "Menos de dois snapshots; nada a correlacionar.",
        }

    edges: list[dict[str, object]] = []
    fingerprints: list[str] = []
    for i in range(len(rows) - 1):
        newer = rows[i]
        older = rows[i + 1]
        cur_p = _payload_json_as_dict(newer.get("payload_json"))
        prev_p = _payload_json_as_dict(older.get("payload_json"))
        changed = _compute_accounting_approval_changed(cur_p, prev_p)
        fp = _fingerprint_accounting_diff(changed)
        fingerprints.append(fp)
        edges.append(
            {
                "newer_id": newer.get("id"),
                "older_id": older.get("id"),
                "changed_count": len(changed),
                "fields": [str(c.get("field")) for c in changed],
            }
        )

    latest_fp = fingerprints[0] if fingerprints else ""
    latest_pair_has_diff = bool(latest_fp)
    prolonged_identical_diff = False
    prolonged_detail: dict[str, object] | None = None
    if latest_fp and len(fingerprints) >= int(prolonged_edges):
        run = 1
        for j in range(1, len(fingerprints)):
            if fingerprints[j] == latest_fp:
                run += 1
            else:
                break
        if run >= int(prolonged_edges):
            prolonged_identical_diff = True
            prolonged_detail = {
                "consecutive_edges_with_same_diff": run,
                "fingerprint": latest_fp,
                "threshold_edges": int(prolonged_edges),
            }

    return {
        "ok": True,
        "snapshots_considered": len(rows),
        "edges": edges,
        "latest_pair_has_diff": latest_pair_has_diff,
        "prolonged_identical_diff": prolonged_identical_diff,
        "prolonged_detail": prolonged_detail,
        "policy": {"window": int(window), "prolonged_edges": int(prolonged_edges)},
    }


@router.post("/accounting-approvals/retention")
def post_accounting_approvals_retention(
    payload: dict | None = Body(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """
    D17: remove snapshots mais antigos que o cutoff, respeitando keep_minimum de linhas na tabela (compactação por poda).
    """
    _ensure_accounting_approvals_table(db)
    body = payload if isinstance(payload, dict) else {}
    older_than_days = int(body.get("older_than_days") or 90)
    keep_minimum = int(body.get("keep_minimum") or 25)
    dry_run = bool(body.get("dry_run"))
    if older_than_days < 7 or older_than_days > 3650:
        raise _safe_client_error("older_than_days must be between 7 and 3650.")
    if keep_minimum < 1 or keep_minimum > 10_000:
        raise _safe_client_error("keep_minimum must be between 1 and 10000.")

    total_row = db.execute(text("SELECT COUNT(*)::INT AS c FROM fiscal_accounting_approvals")).mappings().first()
    total = int((total_row or {}).get("c") or 0)
    max_deletable = max(0, total - int(keep_minimum))
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(older_than_days))

    count_old_row = db.execute(
        text(
            """
            SELECT COUNT(*)::INT AS c
              FROM fiscal_accounting_approvals
             WHERE created_at < :cutoff
            """
        ),
        {"cutoff": cutoff},
    ).mappings().first()
    count_old = int((count_old_row or {}).get("c") or 0)
    delete_limit = min(count_old, max_deletable)

    id_rows = db.execute(
        text(
            """
            SELECT id
              FROM fiscal_accounting_approvals
             WHERE created_at < :cutoff
             ORDER BY created_at ASC
             LIMIT :lim
            """
        ),
        {"cutoff": cutoff, "lim": int(delete_limit)},
    ).mappings().all()
    ids = [str(r.get("id")) for r in id_rows if r.get("id")]

    deleted = 0
    if not dry_run and ids:
        for row_id in ids:
            db.execute(text("DELETE FROM fiscal_accounting_approvals WHERE id = :id"), {"id": row_id})
        db.commit()
        deleted = len(ids)
    elif dry_run:
        deleted = 0

    return {
        "ok": True,
        "dry_run": dry_run,
        "older_than_days": int(older_than_days),
        "keep_minimum": int(keep_minimum),
        "cutoff_utc": cutoff.isoformat(),
        "total_rows_before": total,
        "rows_matching_age_before_cutoff": count_old,
        "max_deletable_respecting_keep_minimum": max_deletable,
        "selected_for_delete": len(ids),
        "deleted": deleted if not dry_run else 0,
        "would_delete_ids_sample": ids[:5],
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
        raise _safe_client_error("Unable to process invoice request.") from exc

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


@router.get("/providers/br-go-no-go")
def get_br_provider_go_no_go(
    run_connectivity: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    return build_br_go_no_go_checklist(db, run_connectivity=run_connectivity)


@router.get("/providers/pt-go-no-go")
def get_pt_provider_go_no_go(
    run_connectivity: bool = Query(default=False),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    return build_pt_go_no_go_checklist(db, run_connectivity=run_connectivity)


@router.get("/global/catalog")
def get_fiscal_global_catalog(
    _: None = Depends(validate_internal_token),
):
    return build_fiscal_global_catalog()


@router.get("/global/scenario-matrix")
def get_fiscal_global_scenario_matrix(
    _: None = Depends(validate_internal_token),
):
    return build_fiscal_global_scenario_matrix()


@router.get("/global/fg1-wave-scope")
def get_fiscal_fg1_wave_scope(
    _: None = Depends(validate_internal_token),
):
    return build_fiscal_fg1_wave_scope()


@router.get("/global/fg1/stub-adapters")
def get_fiscal_fg1_stub_adapters(
    _: None = Depends(validate_internal_token),
):
    return build_fg1_stub_adapters_catalog()


@router.get("/global/fg1/fixtures-matrix")
def get_fiscal_fg1_fixtures_matrix(
    _: None = Depends(validate_internal_token),
):
    return build_fg1_fixtures_matrix()


@router.get("/global/fg1/fixture-inventory")
def get_fiscal_fg1_fixture_inventory(
    _: None = Depends(validate_internal_token),
):
    """Lista arquivos em fixtures/fiscal/fg1/ e valida contagem esperada (onda 1)."""
    return build_fg1_fixture_inventory()


@router.get("/global/fg1/fixture-document")
def get_fiscal_fg1_fixture_document(
    country: str = Query(...),
    operation: str = Query(..., pattern="^(authorize|cancel|correct|status)$"),
    scenario: str | None = Query(default=None),
    _: None = Depends(validate_internal_token),
):
    """Retorna o JSON canônico da fixture (disco se existir; caso contrário sintético alinhado ao simulate)."""
    try:
        return read_fg1_fixture_document(country=country, operation=operation, scenario=scenario)
    except ValueError as exc:
        raise _safe_client_error("Invalid FG-1 fixture parameters.") from exc


@router.get("/global/fg1/envelope-check")
def get_fiscal_fg1_envelope_check(
    _: None = Depends(validate_internal_token),
):
    return validate_fg1_envelope_contract()


@router.get("/global/fg1/stub-wave-readiness")
def get_fiscal_fg1_stub_wave_readiness(
    _: None = Depends(validate_internal_token),
):
    return build_fg1_stub_wave_readiness()


@router.post("/global/fg1/simulate")
def post_fiscal_fg1_stub_simulate(
    country: str = Query(...),
    operation: str = Query(..., pattern="^(authorize|cancel|correct|status)$"),
    scenario: str | None = Query(default=None),
    region: str | None = Query(default=None),
    _: None = Depends(validate_internal_token),
):
    try:
        return simulate_fg1_stub(country=country, operation=operation, scenario=scenario, region=region)
    except ValueError as exc:
        logger.info(
            "fiscal_fg1_stub_simulate_rejected",
            extra={
                "country_code": country,
                "operation": operation,
                "scenario": scenario,
                "region": region,
                "error": str(exc)[:240],
            },
        )
        raise _safe_client_error("Invalid FG-1 simulation parameters.") from exc


@router.get("/global/fg1/coverage-gate")
def get_fiscal_fg1_coverage_gate(
    _: None = Depends(validate_internal_token),
):
    return build_fg1_coverage_gate()


@router.get("/global/fg1/readiness-gate")
def get_fiscal_fg1_readiness_gate(
    _: None = Depends(validate_internal_token),
):
    return build_fg1_readiness_gate()


@router.get("/global/fg1/readiness-action-plan")
def get_fiscal_fg1_readiness_action_plan(
    _: None = Depends(validate_internal_token),
):
    return build_fg1_readiness_action_plan()


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
        raise _safe_client_error("Invalid batch submit payload.") from exc
    return {"ok": True, **out}


@router.get("/providers/stub/svrs/batch-query")
def get_svrs_batch_query_stub(
    receipt_number: str = Query(...),
    _: None = Depends(validate_internal_token),
):
    try:
        out = query_svrs_issue_batch_stub(receipt_number)
    except ValueError as exc:
        raise _safe_client_error("Invalid receipt_number for batch query.") from exc
    return {"ok": True, **out}


@router.post("/providers/stub/svrs/batch-reset")
def post_svrs_batch_reset_stub(
    _: None = Depends(validate_internal_token),
):
    return reset_svrs_issue_batch_stub_state()


@router.post("/providers/stub/at-pt/issue")
def post_at_pt_stub_gateway_issue(
    payload: dict,
    wire_mode: str = Query(default="rest", pattern="^(rest|soap|soap12|xml)$"),
    _: None = Depends(validate_internal_token),
):
    """
    F3B-STUB-01: simulador AT PT com fachada REST vs SOAP (memória local, idempotência).
    Útil para testes de contrato e painel OPS sem credenciais AT.
    """
    try:
        out = submit_at_pt_stub_issue(payload or {}, wire_mode=wire_mode)
    except ValueError as exc:
        raise _safe_client_error(str(exc)) from exc
    return {"ok": True, **out}


@router.post("/providers/stub/at-pt/cancel")
def post_at_pt_stub_gateway_cancel(
    payload: dict,
    wire_mode: str = Query(default="rest", pattern="^(rest|soap|soap12|xml)$"),
    _: None = Depends(validate_internal_token),
):
    try:
        out = submit_at_pt_stub_cancel(payload or {}, wire_mode=wire_mode)
    except ValueError as exc:
        raise _safe_client_error(str(exc)) from exc
    return {"ok": True, **out}


@router.post("/providers/stub/at-pt/reset")
def post_at_pt_stub_gateway_reset(
    _: None = Depends(validate_internal_token),
):
    return reset_at_pt_stub_gateway_state()


@router.get("/a1-dry-run/status")
def get_fiscal_a1_dry_run_status(
    _: None = Depends(validate_internal_token),
):
    """F3C-STUB-01: estado das flags A1 dry-run (sem segredos)."""
    return {"ok": True, **build_a1_dry_run_status_payload()}


@router.post("/a1-dry-run/verify")
def post_fiscal_a1_dry_run_verify(
    body: dict,
    _: None = Depends(validate_internal_token),
):
    """F3C-STUB-01: valida assinatura dry-run (HMAC) contra `xml_preview` + bloco `signature`."""
    xml_preview = str((body or {}).get("xml_preview") or "")
    sig = (body or {}).get("signature")
    if not xml_preview.strip():
        raise _safe_client_error("xml_preview is required.")
    if not isinstance(sig, dict):
        raise _safe_client_error("signature must be an object with dry_run_signature_b64.")
    verified = verify_a1_dry_run_signature(xml_preview=xml_preview, signature_block=sig)
    return {"ok": True, "verified": verified}


@router.get("/release-gate/status")
def get_fiscal_release_gate_status(
    _: None = Depends(validate_internal_token),
):
    """RELEASE-GATE-01: snapshot de flags fiscais (stub vs real) para go/no-go por ambiente."""
    return {"ok": True, **build_fiscal_release_gate_payload()}


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
    params: dict[str, object] = {"limit": int(limit), "offset": int(offset)}
    params["external_reference"] = external_reference.strip() if external_reference else None
    params["event_type"] = event_type.strip().upper() if event_type else None
    params["from_date"] = from_date
    params["to_date"] = to_date
    params["only_mismatches"] = bool(only_mismatches)

    rows = db.execute(
        text(
            """
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
            WHERE (:external_reference IS NULL OR fl.external_reference = :external_reference)
              AND (:event_type IS NULL OR COALESCE(fl.metadata->>'event_type', je.reference_type) = :event_type)
              AND (:from_date IS NULL OR COALESCE(je.created_at, fl.created_at)::date >= :from_date)
              AND (:to_date IS NULL OR COALESCE(je.created_at, fl.created_at)::date <= :to_date)
              AND (
                    :only_mismatches = false
                    OR (
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
                  )
            ORDER BY COALESCE(je.created_at, fl.created_at) DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        params,
    ).mappings().all()

    count_row = db.execute(
        text(
            """
            SELECT COUNT(*)
            FROM financial_ledger fl
            LEFT JOIN journal_entries je
                ON je.dedupe_key = fl.external_reference
            WHERE (:external_reference IS NULL OR fl.external_reference = :external_reference)
              AND (:event_type IS NULL OR COALESCE(fl.metadata->>'event_type', je.reference_type) = :event_type)
              AND (:from_date IS NULL OR COALESCE(je.created_at, fl.created_at)::date >= :from_date)
              AND (:to_date IS NULL OR COALESCE(je.created_at, fl.created_at)::date <= :to_date)
              AND (
                    :only_mismatches = false
                    OR (
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
                  )
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


@router.get("/accounting/revenue-credits-delta")
def get_accounting_revenue_credits_delta(
    date: str = Query(..., description="YYYY-MM-DD"),
    currency: str | None = Query(default=None),
    ledger_sample_limit: int = Query(default=40, ge=1, le=200),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """Sprint 2 D15: receita reconhecida vs movimentos de estorno/crédito no `financial_ledger` (mesmo dia)."""
    try:
        snapshot_date = datetime.fromisoformat(date.strip()).date()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from exc
    payload = build_revenue_credits_delta_report(
        db,
        snapshot_date=snapshot_date,
        currency=currency,
        ledger_sample_limit=ledger_sample_limit,
    )
    return {"ok": True, **payload}


@router.get("/accounting/partner-settlement-reconcile")
def get_accounting_partner_settlement_reconcile(
    date: str = Query(..., description="YYYY-MM-DD"),
    currency: str | None = Query(default=None),
    partner_limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    """Sprint 2 P0 Contábil Partners: ciclos computados no dia vs ledger BILLING_REVENUE ligado ao ciclo."""
    try:
        snapshot_date = datetime.fromisoformat(date.strip()).date()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.") from exc
    payload = build_partner_settlement_reconcile_report(
        db,
        snapshot_date=snapshot_date,
        currency=currency,
        partner_limit=partner_limit,
    )
    return {"ok": True, **payload}


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
