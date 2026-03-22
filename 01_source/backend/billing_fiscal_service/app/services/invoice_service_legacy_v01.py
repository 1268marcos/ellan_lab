# 01_source/backend/billing_fiscal_service/app/services/invoice_service.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.lifecycle_client import has_invoice_trigger_event
from app.models.invoice_model import Invoice, InvoiceStatus
from app.utils.id_generator import generate_invoice_id


def generate_invoice(db: Session, order_id: str) -> Invoice:
    normalized_order_id = str(order_id).strip()

    existing = db.execute(
        select(Invoice).where(Invoice.order_id == normalized_order_id)
    ).scalar_one_or_none()

    if existing:
        return existing

    if not has_invoice_trigger_event(db, normalized_order_id):
        raise ValueError(
            f"Evento gatilho não encontrado para order_id={normalized_order_id}. "
            f"Esperado: pickup.ready_for_pickup em domain_events."
        )

    now = datetime.now(timezone.utc)

    invoice = Invoice(
        id=generate_invoice_id(),
        order_id=normalized_order_id,
        tenant_id=None,
        country="BR",
        invoice_type="NFE",
        status=InvoiceStatus.PENDING,
        xml_content=None,
        payload_json={
            "source": "manual_generate_endpoint",
            "trigger_event": "pickup.ready_for_pickup",
        },
        error_message=None,
        created_at=now,
        updated_at=now,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice