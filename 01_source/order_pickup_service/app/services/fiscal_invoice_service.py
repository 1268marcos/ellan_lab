# 01_source/order_pickup_service/app/services/fiscal_invoice_service.py
from __future__ import annotations

from typing import Union

from sqlalchemy.orm import Session

from app.integrations.billing_fiscal_client import fetch_invoice_by_order_id
from app.models.fiscal_document import FiscalDocument
from app.services.fiscal_read_adapter import FiscalReadView, fiscal_read_view_from_billing_invoice


def ensure_invoice_for_order(db: Session, order_id: str) -> FiscalDocument | FiscalReadView:
    inv = fetch_invoice_by_order_id(order_id)
    if isinstance(inv, dict) and inv.get("id"):
        return fiscal_read_view_from_billing_invoice(inv)

    existing = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order_id)
        .first()
    )

    if existing:
        return existing

    from app.services.internal_invoice_generator import generate_invoice_core

    return generate_invoice_core(db=db, order_id=order_id)
