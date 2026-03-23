# 01_source/backend/biling_fiscal_service/app/services/invoice_orchestrator.py
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.integrations.lifecycle_client import has_order_paid_event
from app.integrations.order_pickup_client import (
    OrderPickupClientError,
    get_order_snapshot,
)
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.fiscal_router_service import route_issue_invoice

logger = logging.getLogger(__name__)


def _utc_now():
    return datetime.now(timezone.utc)


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
        status=InvoiceStatus.PENDING,
        retry_count=0,
        order_snapshot=snapshot,
    )

    db.add(invoice)
    db.flush()

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


def process_invoice(db: Session, invoice: Invoice) -> Invoice:
    if invoice.status == InvoiceStatus.ISSUED:
        return invoice

    invoice.status = InvoiceStatus.PROCESSING
    invoice.processing_started_at = _utc_now()
    invoice.last_attempt_at = _utc_now()

    try:
        result = route_issue_invoice(invoice)

        invoice.status = InvoiceStatus.ISSUED
        invoice.invoice_number = result.get("invoice_number")
        invoice.invoice_series = result.get("invoice_series")
        invoice.access_key = result.get("access_key")
        invoice.tax_details = result.get("tax_details")
        invoice.xml_content = result.get("xml_content")
        invoice.government_response = result.get("government_response")
        invoice.payload_json = result
        invoice.error_message = None
        invoice.last_error_code = None
        invoice.issued_at = _utc_now()
        invoice.next_retry_at = None

        logger.info(
            "invoice_issued",
            extra={
                "order_id": invoice.order_id,
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "country": invoice.country,
            },
        )

    except Exception as exc:
        invoice.status = InvoiceStatus.FAILED
        invoice.error_message = str(exc)
        invoice.last_error_code = "ISSUE_FAILED"
        invoice.retry_count = int(invoice.retry_count or 0) + 1

        logger.exception(
            "invoice_issue_failed",
            extra={
                "order_id": invoice.order_id,
                "invoice_id": invoice.id,
                "retry_count": invoice.retry_count,
            },
        )

    return invoice


def ensure_and_process_invoice(db: Session, order_id: str) -> Invoice:
    invoice = ensure_invoice_for_order(db, order_id)
    invoice = process_invoice(db, invoice)
    db.commit()
    db.refresh(invoice)
    return invoice
