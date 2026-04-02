# 01_source/backend/biling_fiscal_service/app/services/invoice_orchestrator.py
# Arquivo preserva o endpoint manual como fallback, mas agora ele usa o mesmo mecanismo de lock/processamento dos workers.
from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.integrations.lifecycle_client import has_order_paid_event
from app.integrations.order_pickup_client import (
    OrderPickupClientError,
    get_order_snapshot,
)
from app.models.invoice_model import Invoice
from app.services.invoice_processing_service import claim_and_process_invoice_by_id

logger = logging.getLogger(__name__)


def _resolve_country_from_snapshot(snapshot: dict) -> str:
    order = snapshot.get("order") or {}
    region = str(order.get("region") or "").strip().upper()

    if region == "SP":
        return "BR"
    if region == "PT":
        return "PT"

    return "BR"


def _resolve_invoice_type(country: str) -> str:
    normalized = str(country or "").strip().upper()

    if normalized == "BR":
        return "NFE"
    if normalized == "PT":
        return "FT"

    return "INVOICE"


def ensure_invoice_for_order(db: Session, order_id: str) -> Invoice:
    normalized_order_id = str(order_id).strip()

    existing = (
        db.query(Invoice)
        .filter(Invoice.order_id == normalized_order_id)
        .first()
    )
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
        raise ValueError(str(exc)) from exc

    order = snapshot.get("order") or {}
    country = _resolve_country_from_snapshot(snapshot)
    invoice_type = _resolve_invoice_type(country)

    invoice = Invoice(
        id=f"inv_{uuid.uuid4().hex}",
        order_id=normalized_order_id,
        tenant_id=order.get("tenant_id"),
        region=order.get("region"),
        country=country,
        invoice_type=invoice_type,
        payment_method=order.get("payment_method"),
        currency=order.get("currency") or ("BRL" if country == "BR" else "EUR"),
        amount_cents=order.get("amount_cents"),
        order_snapshot=snapshot,
    )

    db.add(invoice)
    db.commit()
    db.refresh(invoice)

    logger.info(
        "invoice_created_from_order_paid",
        extra={
            "order_id": normalized_order_id,
            "invoice_id": invoice.id,
            "country": country,
            "invoice_type": invoice_type,
        },
    )

    return invoice


def ensure_and_process_invoice(db: Session, order_id: str) -> Invoice:
    invoice = ensure_invoice_for_order(db, order_id)

    processed = claim_and_process_invoice_by_id(
        db,
        invoice_id=invoice.id,
    )

    if processed is None:
        invoice = db.query(Invoice).filter(Invoice.id == invoice.id).first()
        return invoice

    return processed