# 01_source/backend/billing_fiscal_service/app/services/invoice_service.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.lifecycle_client import has_order_paid_event
from app.models.invoice_model import Invoice, InvoiceStatus
from app.utils.id_generator import generate_invoice_id


def _resolve_country_from_order_id(order_id: str) -> str:
    # Nesta fase, default Brasil.
    # Evolução posterior: lookup em facts/order service.
    return "BR"


def _resolve_invoice_type(country: str) -> str:
    mapping = {
        "BR": "NFE",
        "PT": "SAFT",
        "ES": "FACTURAE",
    }
    return mapping.get(country, "NFE")


def generate_invoice(db: Session, order_id: str) -> Invoice:
    normalized_order_id = str(order_id).strip()

    existing = db.execute(
        select(Invoice).where(Invoice.order_id == normalized_order_id)
    ).scalar_one_or_none()

    if existing:
        return existing

    if not has_order_paid_event(db, normalized_order_id):
        raise ValueError(
            f"Evento financeiro oficial não encontrado para order_id={normalized_order_id}. "
            f"Esperado: order.paid em domain_events."
        )

    now = datetime.now(timezone.utc)
    country = _resolve_country_from_order_id(normalized_order_id)
    invoice_type = _resolve_invoice_type(country)

    invoice = Invoice(
        id=generate_invoice_id(),
        order_id=normalized_order_id,
        tenant_id=None,
        country=country,
        invoice_type=invoice_type,
        payment_method=None,
        currency="BRL" if country == "BR" else "EUR",
        status=InvoiceStatus.PENDING,
        invoice_number=None,
        invoice_series=None,
        access_key=None,
        xml_content=None,
        payload_json={
            "source": "manual_generate_endpoint",
            "trigger_event": "order.paid",
        },
        tax_details=None,
        government_response=None,
        error_message=None,
        issued_at=None,
        processing_started_at=None,
        created_at=now,
        updated_at=now,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice