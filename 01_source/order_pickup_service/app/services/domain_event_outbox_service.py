# 01_source/order_pickup_service/app/services/domain_event_outbox_service.py
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.domain_event_outbox import DomainEventOutbox

logger = logging.getLogger("order_paid_outbox")


# def _utc_now_naive() -> datetime:
#     return datetime.now(timezone.utc).replace(tzinfo=None)

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def enqueue_order_paid_event(
    db: Session,
    *,
    order_id: str,
    region: str,
    channel: str,
    payment_method: str | None,
    transaction_id: str | None,
    amount_cents: int | None,
    currency: str | None,
    locker_id: str | None,
    machine_id: str | None,
    slot: int | str | None,
    allocation_id: str | None,
    pickup_id: str | None,
    tenant_id: str | None = None,
    operator_id: str | None = None,
    site_id: str | None = None,
    source_service: str = "order_pickup_service",
) -> DomainEventOutbox:

    # 🔒 VALIDAÇÃO CANÔNICA (NOVA)
    if not order_id:
        raise ValueError("order_id obrigatório")

    if not amount_cents or amount_cents <= 0:
        raise ValueError(f"amount_cents inválido: {amount_cents}")

    if not currency:
        raise ValueError("currency obrigatório")

    if not channel:
        raise ValueError("channel obrigatório")

    if not transaction_id:
        logger.warning(
            "order_paid_event_missing_transaction_id",
            extra={"order_id": order_id},
        )

    if not payment_method:
        logger.warning(
            "order_paid_event_missing_payment_method",
            extra={"order_id": order_id},
        )

    event_key = f"order.paid:{order_id}"

    # 🔒 IDEMPOTÊNCIA FORTE
    existing = (
        db.query(DomainEventOutbox)
        .filter(DomainEventOutbox.event_key == event_key)
        .first()
    )

    if existing:
        logger.info(
            "order_paid_event_already_exists",
            extra={
                "order_id": order_id,
                "event_key": event_key,
                "status": existing.status,
            },
        )
        return existing

    occurred_at = _utc_now() # _utc_now_naive()

    payload: dict[str, Any] = {
        "order_id": order_id,
        "region": region,
        "channel": channel,
        "payment_method": payment_method,
        "transaction_id": transaction_id,
        "amount_cents": amount_cents,
        "currency": currency,
        "locker_id": locker_id,
        "machine_id": machine_id,
        "slot": str(slot) if slot is not None else None,
        "allocation_id": allocation_id,
        "pickup_id": pickup_id,
        "tenant_id": tenant_id,
        "operator_id": operator_id,
        "site_id": site_id,
        "source_service": source_service,
    }

    row = DomainEventOutbox(
        id=f"deo_{uuid.uuid4().hex}",
        event_key=event_key,
        aggregate_type="order",
        aggregate_id=order_id,
        event_name="order.paid",
        event_version="1",
        status="PENDING",
        payload_json=payload,
        occurred_at=occurred_at,
        published_at=None,
        last_error=None,
        created_at=occurred_at,
        updated_at=occurred_at,
    )

    db.add(row)
    db.flush()

    logger.info(
        "order_paid_event_enqueued",
        extra={
            "order_id": order_id,
            "event_key": event_key,
            "amount_cents": amount_cents,
            "channel": channel,
            "payment_method": payment_method,
        },
    )

    return row