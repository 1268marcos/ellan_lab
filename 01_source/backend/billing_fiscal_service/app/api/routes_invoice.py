# 01_source/backend/billing_fiscal_service/app/api/routes_invoice.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.invoice_service import generate_invoice
from app.schemas.invoice_schema import InvoiceResponse
from app.core.config import settings
from app.models.invoice_model import Invoice

router = APIRouter(prefix="/internal/invoices", tags=["invoices"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


def _to_invoice_response(invoice: Invoice) -> InvoiceResponse:
    return InvoiceResponse(
        id=invoice.id,
        order_id=invoice.order_id,
        country=invoice.country,
        invoice_type=invoice.invoice_type,
        status=str(getattr(invoice.status, "value", invoice.status)),
        invoice_number=invoice.invoice_number,
        invoice_series=invoice.invoice_series,
        access_key=invoice.access_key,
        error_message=invoice.error_message,
    )


@router.post("/generate/{order_id}", response_model=InvoiceResponse)
def create_invoice(
    order_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    try:
        invoice = generate_invoice(db, order_id)
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