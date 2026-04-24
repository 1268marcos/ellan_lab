from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.fiscal_reconciliation_gap import FiscalReconciliationGap
from app.models.invoice_delivery_log import InvoiceDeliveryLog
from app.models.invoice_model import Invoice
from app.services.invoice_orchestrator import ensure_and_process_invoice
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
from app.services.invoice_delivery_service import record_invoice_delivery
from app.services.invoice_email_service import send_danfe_email_stub

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
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    normalized_order_id = str(order_id).strip()
    if not normalized_order_id:
        raise HTTPException(status_code=400, detail="order_id is required")
    try:
        invoice = ensure_and_process_invoice(db, normalized_order_id)
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
