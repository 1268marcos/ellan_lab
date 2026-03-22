# 01_source/backend/billing_fiscal_service/app/services/invoice_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.invoice_model import Invoice
from app.utils.id_generator import generate_invoice_id
from app.integrations.lifecycle_client import has_payment_approved


def generate_invoice(db: Session, order_id: str):

    existing = db.execute(
        select(Invoice).where(Invoice.order_id == order_id)
    ).scalar_one_or_none()

    if existing:
        return existing

    if not has_payment_approved(db, order_id):
        raise Exception("Pagamento não aprovado")

    invoice = Invoice(
        id=generate_invoice_id(),
        order_id=order_id,
        status="PENDING",
        payload_json={"source": "auto"},
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice