# 01_source/backend/billing_fiscal_service/app/services/invoice_service.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.integrations.lifecycle_client import has_order_paid_event
from app.integrations.order_pickup_client import OrderPickupClientError, get_order_snapshot
from app.models.invoice_model import Invoice, InvoiceStatus
from app.utils.id_generator import generate_invoice_id


def _country_from_region(region: str | None) -> str:
    normalized = str(region or "").strip().upper()
    mapping = {
        "SP": "BR",
        "BR": "BR",
        "PT": "PT",
        "ES": "ES",
    }
    return mapping.get(normalized, "BR")


def _currency_from_country(country: str) -> str:
    mapping = {
        "BR": "BRL",
        "PT": "EUR",
        "ES": "EUR",
    }
    return mapping.get(country, "BRL")


def _invoice_type_from_country(country: str) -> str:
    mapping = {
        "BR": "NFE",
        "PT": "SAFT",
        "ES": "FACTURAE",
    }
    return mapping.get(country, "NFE")


def _extract_order_snapshot_fields(snapshot: dict) -> dict:
    order = snapshot.get("order") or {}
    allocation = snapshot.get("allocation") or {}
    pickup = snapshot.get("pickup") or {}

    region = order.get("region")
    country = _country_from_region(region)

    return {
        "tenant_id": None,
        "region": region,
        "country": country,
        "currency": _currency_from_country(country),
        "payment_method": order.get("payment_method"),
        "amount_cents": order.get("amount_cents"),
        "invoice_type": _invoice_type_from_country(country),
        "order_snapshot": {
            "order": order,
            "allocation": allocation,
            "pickup": pickup,
        },
        "payload_json": {
            "source": "manual_generate_endpoint",
            "trigger_event": "order.paid",
            "lookup_source": "order_pickup_service",
        },
    }


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

    try:
        snapshot = get_order_snapshot(normalized_order_id)
    except OrderPickupClientError as exc:
        raise ValueError(f"Não foi possível enriquecer invoice com dados canônicos do pedido: {exc}") from exc

    fields = _extract_order_snapshot_fields(snapshot)
    now = datetime.now(timezone.utc)

    invoice = Invoice(
        id=generate_invoice_id(),
        order_id=normalized_order_id,
        tenant_id=fields["tenant_id"],
        region=fields["region"],
        country=fields["country"],
        invoice_type=fields["invoice_type"],
        invoice_number=None,
        invoice_series=None,
        access_key=None,
        payment_method=fields["payment_method"],
        currency=fields["currency"],
        amount_cents=fields["amount_cents"],
        status=InvoiceStatus.PENDING,
        xml_content=None,
        payload_json=fields["payload_json"],
        tax_details=None,
        government_response=None,
        order_snapshot=fields["order_snapshot"],
        error_message=None,
        last_error_code=None,
        retry_count=0,
        next_retry_at=None,
        last_attempt_at=None,
        dead_lettered_at=None,
        processing_started_at=None,
        locked_by=None,
        locked_at=None,
        issued_at=None,
        created_at=now,
        updated_at=now,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    return invoice