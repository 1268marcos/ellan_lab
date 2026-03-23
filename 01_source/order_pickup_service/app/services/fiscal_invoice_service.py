# 01_source/order_pickup_service/app/services/fiscal_invoice_service.py
from sqlalchemy.orm import Session

from app.models.fiscal_document import FiscalDocument


def ensure_invoice_for_order(db: Session, order_id: str) -> FiscalDocument:
    existing = (
        db.query(FiscalDocument)
        .filter(FiscalDocument.order_id == order_id)
        .first()
    )

    if existing:
        return existing

    # IMPORTANTE:
    # aqui você chama a MESMA lógica do endpoint generate
    # ou extrai ela para cá

    from app.services.internal_invoice_generator import generate_invoice_core

    return generate_invoice_core(db=db, order_id=order_id)