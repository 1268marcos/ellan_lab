# 01_source/order_pickup_service/app/jobs/lifecycle_events_consumer.py
# 21/04/2026 - correção crítica:
# - resolve order_id corretamente para eventos de pickup
# - grava order.picked_up_at no pickup.door_opened
# - sincroniza pickup REDEEMED/COMPLETED
# - mantém pipeline de pickup.expired
# 22/04/2026 - uso de finalize_pickup_after_door_closed()

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.lifecycle_events_client import (
    LifecycleEventsClient,
    LifecycleEventsClientError,
)
from app.models.allocation import Allocation
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupLifecycleStage, PickupStatus
from app.services.pickup_expiration_handler import handle_pickup_expired

from app.services.pickup_completion_service import finalize_pickup_after_door_closed


logger = logging.getLogger(__name__)

LIFECYCLE_EVENTS_BATCH_SIZE = settings.lifecycle_events_batch_size


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_occurred_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if value is None:
        return _utc_now()

    text = str(value).strip()
    if not text:
        return _utc_now()

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        logger.warning(
            "pickup_event_invalid_occurred_at",
            extra={"raw_value": value},
        )
        return _utc_now()


def _resolve_order_id_from_event(
    *,
    db: Session,
    item: dict[str, Any],
    payload: dict[str, Any],
) -> str | None:
    order_id = payload.get("order_id")
    if order_id:
        return str(order_id)

    aggregate_id = item.get("aggregate_id")
    if not aggregate_id:
        return None

    aggregate_type = str(item.get("aggregate_type") or "").strip().lower()

    if aggregate_type == "order":
        return str(aggregate_id)

    if aggregate_type == "pickup":
        pickup = db.query(Pickup).filter(Pickup.id == str(aggregate_id)).first()
        if pickup and pickup.order_id:
            return str(pickup.order_id)

    order = db.query(Order).filter(Order.id == str(aggregate_id)).first()
    if order:
        return str(order.id)

    pickup = db.query(Pickup).filter(Pickup.id == str(aggregate_id)).first()
    if pickup and pickup.order_id:
        return str(pickup.order_id)

    return None


def run_lifecycle_events_consumer_once(db: Session) -> int:
    client = LifecycleEventsClient()

    try:
        response = client.list_pending_events(limit=LIFECYCLE_EVENTS_BATCH_SIZE)
    except LifecycleEventsClientError:
        logger.exception("lifecycle_events_list_failed")
        return 0

    items = response.get("items", []) or []
    if not items:
        return 0

    processed = 0

    for item in items:
        event_name = item.get("event_name")
        event_key = item.get("event_key")
        payload = item.get("payload") or {}

        order_id = _resolve_order_id_from_event(
            db=db,
            item=item,
            payload=payload,
        )

        if not event_key or not order_id:
            logger.warning(
                "lifecycle_event_missing_fields",
                extra={
                    "event_key": event_key,
                    "event_name": event_name,
                    "aggregate_id": item.get("aggregate_id"),
                    "aggregate_type": item.get("aggregate_type"),
                    "payload": payload,
                },
            )
            continue

        try:
            handled = False

            if event_name == "order.prepayment_timed_out":
                handled = _handle_prepayment_timeout(
                    db=db,
                    order_id=order_id,
                    payload=payload,
                )

            elif event_name == "pickup.door_opened":
                handled = _handle_pickup_door_opened(
                    db=db,
                    order_id=order_id,
                    payload=payload,
                )

            elif event_name == "pickup.door_closed":
                handled = finalize_pickup_after_door_closed(order_id)

            elif event_name in {
                "pickup.expired",
                "pickup.timed_out",
                "pickup.pickup_timed_out",
            }:
                handled = handle_pickup_expired(
                    db=db,
                    order_id=order_id,
                    payload=payload,
                )

            if handled:
                client.ack_event(event_key=event_key)
                processed += 1

        except LifecycleEventsClientError:
            logger.exception(
                "lifecycle_event_ack_failed",
                extra={"event_key": event_key, "order_id": order_id},
            )
            db.rollback()

        except Exception:
            logger.exception(
                "lifecycle_event_process_failed",
                extra={
                    "event_key": event_key,
                    "event_name": event_name,
                    "order_id": order_id,
                    "payload": payload,
                },
            )
            db.rollback()

    if processed:
        logger.info("lifecycle_events_processed", extra={"processed": processed})

    return processed


def _handle_pickup_door_opened(
    *,
    db: Session,
    order_id: str,
    payload: dict[str, Any],
) -> bool:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning(
            "pickup_door_opened_order_not_found",
            extra={"order_id": order_id},
        )
        return True

    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )

    occurred_at = _parse_occurred_at(payload.get("occurred_at"))
    redeemed_via = payload.get("redeemed_via") or "MANUAL"

    # Estado do pedido:
    # DISPENSED = máquina liberou / retirada concluída operacionalmente no fluxo atual
    order.status = OrderStatus.DISPENSED
    order.picked_up_at = occurred_at
    order.updated_at = _utc_now()

    if pickup:
        pickup.status = PickupStatus.REDEEMED
        pickup.lifecycle_stage = PickupLifecycleStage.COMPLETED

        if getattr(pickup, "redeemed_at", None) is None:
            pickup.redeemed_at = occurred_at

        if getattr(pickup, "item_removed_at", None) is None:
            pickup.item_removed_at = occurred_at

        if getattr(pickup, "door_closed_at", None) is None:
            pickup.door_closed_at = occurred_at

        pickup.redeemed_via = redeemed_via
        pickup.current_token_id = None
        pickup.touch()

    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .order_by(Allocation.created_at.desc(), Allocation.id.desc())
        .first()
    )

    if allocation:
        try:
            allocation.mark_picked_up()
        except Exception:
            if hasattr(allocation, "state"):
                allocation.state = "PICKED_UP"
            if hasattr(allocation, "updated_at"):
                allocation.updated_at = _utc_now()

    db.commit()

    logger.info(
        "pickup_door_opened_applied",
        extra={
            "order_id": order.id,
            "pickup_id": pickup.id if pickup else None,
            "allocation_id": allocation.id if allocation else None,
            "picked_up_at": occurred_at.isoformat(),
            "order_status": order.status.value if hasattr(order.status, "value") else str(order.status),
        },
    )

    return True


def _handle_prepayment_timeout(
    *,
    db: Session,
    order_id: str,
    payload: dict[str, Any],
) -> bool:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning(
            "prepayment_timeout_order_not_found",
            extra={"order_id": order_id},
        )
        return True

    if order.status != OrderStatus.PAYMENT_PENDING:
        logger.info(
            "prepayment_timeout_already_handled",
            extra={
                "order_id": order_id,
                "status": order.status.value if hasattr(order.status, "value") else str(order.status),
            },
        )
        return True

    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .order_by(Allocation.created_at.desc(), Allocation.id.desc())
        .first()
    )

    order.status = OrderStatus.CANCELLED
    order.updated_at = _utc_now()

    if allocation:
        if hasattr(allocation, "locked_until"):
            allocation.locked_until = None
        try:
            allocation.mark_released()
        except Exception:
            if hasattr(allocation, "state"):
                allocation.state = "RELEASED"
            if hasattr(allocation, "updated_at"):
                allocation.updated_at = _utc_now()

    db.commit()

    logger.info(
        "prepayment_timeout_applied",
        extra={"order_id": order.id},
    )

    return True