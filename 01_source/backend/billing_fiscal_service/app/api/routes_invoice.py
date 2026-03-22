# 01_source/backend/billing_fiscal_service/app/api/routes_invoice.py
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.invoice_service import generate_invoice
from app.schemas.invoice_schema import InvoiceResponse
from app.core.config import settings

router = APIRouter(prefix="/internal/invoices", tags=["invoices"])


def validate_internal_token(internal_token: str = Header(..., alias="X-Internal-Token")):
    if internal_token != settings.internal_token:
        raise HTTPException(status_code=403, detail="Invalid internal token")


@router.post("/generate/{order_id}", response_model=InvoiceResponse)
def create_invoice(
    order_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(validate_internal_token),
):
    try:
        invoice = generate_invoice(db, order_id)
        return {
            "id": invoice.id,
            "order_id": invoice.order_id,
            "status": invoice.status,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))