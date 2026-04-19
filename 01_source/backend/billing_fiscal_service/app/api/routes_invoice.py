# 01_source/backend/billing_fiscal_service/app/api/routes_invoice.py
# 01_source/backend/billing_fiscal_service/app/routers/internal_invoices.py (NUNCA FOI CRIADO)
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.invoice_model import Invoice
from app.schemas.invoice_schema import InvoiceResponse

# from app.services.invoice_issue_service import reset_invoice_for_retry
# from app.services.invoice_service import generate_invoice
from app.services.invoice_issue_service import reset_invoice_for_retry
from app.services.invoice_orchestrator import ensure_and_process_invoice

from app.core.datetime_utils import to_iso_utc



router = APIRouter(prefix="/internal/invoices", tags=["invoices"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


def _iso_or_none(value):
    return to_iso_utc(value)


def _to_invoice_response(invoice: Invoice) -> InvoiceResponse:
    return InvoiceResponse(
        id=invoice.id,
        order_id=invoice.order_id,
        tenant_id=invoice.tenant_id,
        region=invoice.region,
        country=invoice.country,
        invoice_type=invoice.invoice_type,
        payment_method=invoice.payment_method,
        currency=invoice.currency,
        amount_cents=invoice.amount_cents,
        status=str(getattr(invoice.status, "value", invoice.status)),
        retry_count=int(invoice.retry_count or 0),
        next_retry_at=_iso_or_none(invoice.next_retry_at),
        invoice_number=invoice.invoice_number,
        invoice_series=invoice.invoice_series,
        access_key=invoice.access_key,
        error_message=invoice.error_message,
        last_error_code=invoice.last_error_code,
        government_response=invoice.government_response,
        tax_details=invoice.tax_details,
        xml_content=invoice.xml_content,
        order_snapshot=invoice.order_snapshot,
    )


@router.post("/generate/{order_id}", response_model=InvoiceResponse)
def create_invoice(
    order_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    try:
        invoice = ensure_and_process_invoice(db, order_id)
        return _to_invoice_response(invoice)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return _to_invoice_response(invoice)


@router.get("/by-order/{order_id}", response_model=InvoiceResponse)
def get_invoice_by_order(
    order_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.order_id == order_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found for order")
    return _to_invoice_response(invoice)


@router.post("/{invoice_id}/retry", response_model=InvoiceResponse)
def retry_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = reset_invoice_for_retry(db, invoice, clear_identifiers=False)
    return _to_invoice_response(invoice)


@router.post("/{invoice_id}/reissue", response_model=InvoiceResponse)
def reissue_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice = reset_invoice_for_retry(db, invoice, clear_identifiers=True)
    return _to_invoice_response(invoice)