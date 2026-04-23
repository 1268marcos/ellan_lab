"""
Resolve leitura fiscal: billing_fiscal_service (canônico) com fallback em fiscal_documents.
"""

from __future__ import annotations

from typing import TypeAlias, Union

from sqlalchemy.orm import Session

from app.integrations.billing_fiscal_client import fetch_invoice_by_order_id
from app.models.fiscal_document import FiscalDocument
from app.services.fiscal_read_adapter import FiscalReadView, fiscal_read_view_from_billing_invoice

FiscalReadable: TypeAlias = Union[FiscalDocument, FiscalReadView]


def resolve_fiscal_for_order(db: Session, order_id: str) -> FiscalReadable | None:
    """
    1) Se BILLING_FISCAL_SERVICE_URL estiver definida e existir invoice no billing → FiscalReadView.
    2) Caso contrário → último FiscalDocument local (attempt desc).
    """
    inv = fetch_invoice_by_order_id(order_id)
    if isinstance(inv, dict) and inv.get("id"):
        return fiscal_read_view_from_billing_invoice(inv)

    return (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order_id)
        .order_by(FiscalDocument.attempt.desc())
        .first()
    )


def latest_local_fiscal_document(db: Session, order_id: str) -> FiscalDocument | None:
    """Último documento local (tentativas / reimpressão) — escrita e attempt."""
    return (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order_id)
        .order_by(FiscalDocument.attempt.desc())
        .first()
    )
