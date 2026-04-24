from __future__ import annotations

import base64
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.fiscal_reconciliation_gap import FiscalReconciliationGap
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
    pdf_like = f"%PDF-1.4\n%ELLAN-DANFE-STUB\n1 0 obj\n<< /Type /Catalog >>\nendobj\n% {body}\n%%EOF\n"
    return base64.b64encode(pdf_like.encode("utf-8")).decode("ascii")


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
