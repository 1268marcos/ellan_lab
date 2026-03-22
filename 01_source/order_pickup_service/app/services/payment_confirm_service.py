# 01_source/order_pickup_service/app/services/payment_confirm_service.py
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.domain_event_outbox import DomainEventOutbox
from app.models.order import Order
from app.services.domain_event_outbox_service import enqueue_order_paid_event

logger = logging.getLogger(__name__)


def _utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _enum_value_or_raw(value) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def confirm_payment_and_emit_event(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
    pickup,
    amount_cents: int | None,
    currency: str | None,
    source: str,
) -> None:
    """
    Serviço canônico para a parte financeira da confirmação de pagamento.

    IMPORTANTE:
    - não decide fluxo ONLINE/KIOSK
    - não decide status operacional do pedido
    - não usa order.status como idempotência
    - usa o próprio outbox como fonte canônica de deduplicação
    """

    if order is None:
        raise ValueError("order obrigatório")

    if allocation is None:
        raise ValueError("allocation obrigatório")

    if not order.amount_cents or int(order.amount_cents) <= 0:
        raise ValueError("amount_cents do pedido inválido")

    if amount_cents is None or int(amount_cents) <= 0:
        raise ValueError("amount_cents informado inválido")

    if int(amount_cents) != int(order.amount_cents):
        raise ValueError(
            f"amount mismatch: order={order.amount_cents} payload={amount_cents}"
        )

    if not currency or not str(currency).strip():
        raise ValueError("currency obrigatória")

    if not order.gateway_transaction_id:
        order.gateway_transaction_id = f"{source}-{order.id}"

    if not getattr(order, "paid_at", None):
        order.paid_at = _utc_now_naive()

    event_key = f"order.paid:{order.id}"

    existing = (
        db.query(DomainEventOutbox)
        .filter(DomainEventOutbox.event_key == event_key)
        .first()
    )

    if existing:
        logger.info(
            "payment_confirm_event_already_exists",
            extra={
                "order_id": order.id,
                "event_key": event_key,
                "event_status": existing.status,
                "source": source,
            },
        )
        return

    enqueue_order_paid_event(
        db,
        order_id=order.id,
        region=order.region,
        channel=_enum_value_or_raw(order.channel),
        payment_method=_enum_value_or_raw(order.payment_method),
        transaction_id=order.gateway_transaction_id,
        amount_cents=order.amount_cents,
        currency=str(currency).strip().upper(),
        locker_id=(pickup.locker_id if pickup else order.totem_id),
        machine_id=(pickup.machine_id if pickup else order.totem_id),
        slot=(pickup.slot if pickup else allocation.slot),
        allocation_id=allocation.id,
        pickup_id=(pickup.id if pickup else None),
        tenant_id=None,
        operator_id=None,
        site_id=None,
        source_service="order_pickup_service",
    )

    logger.info(
        "payment_confirm_event_enqueued",
        extra={
            "order_id": order.id,
            "event_key": event_key,
            "source": source,
            "channel": _enum_value_or_raw(order.channel),
            "amount_cents": order.amount_cents,
        },
    )