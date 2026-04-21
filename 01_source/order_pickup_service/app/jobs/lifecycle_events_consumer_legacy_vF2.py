# 01_source/order_pickup_service/app/jobs/lifecycle_events_consumer.py
# 21/04/2026 - hardening para expiração de pickup
# - resolve order_id corretamente mesmo quando aggregate_id vier como pickup_id
# - logs mais explícitos
# - mantém compatibilidade com pickup.expired / pickup.timed_out
# 21/04/2026 - correção crítica para pickup.expired com aggregate_id = pickup_id


from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.lifecycle_events_client import (
    LifecycleEventsClient,
    LifecycleEventsClientError,
)
from app.models.allocation import Allocation
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupStatus
from app.services.pickup_expiration_handler import handle_pickup_expired

logger = logging.getLogger(__name__)

LIFECYCLE_EVENTS_BATCH_SIZE = settings.lifecycle_events_batch_size


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
        logger.warning("pickup_door_opened_order_not_found", extra={"order_id": order_id})
        return True

    pickup = db.query(Pickup).filter(Pickup.order_id == order.id).first()

    order.status = OrderStatus.DISPENSED
    order.picked_up_at = payload.get("occurred_at")

    if pickup:
        pickup.status = PickupStatus.REDEEMED

    db.commit()

    logger.info(
        "pickup_door_opened_applied",
        extra={"order_id": order.id},
    )

    return True


def _resolve_locker_id(*, order: Order, allocation: Allocation | None) -> str | None:
    if allocation and getattr(allocation, "locker_id", None):
        return allocation.locker_id
    if getattr(order, "totem_id", None):
        return order.totem_id
    return None


def _handle_prepayment_timeout(*, db: Session, order_id: str, payload: dict[str, Any]) -> bool:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning("prepayment_timeout_order_not_found", extra={"order_id": order_id})
        return True

    if order.status != OrderStatus.PAYMENT_PENDING:
        logger.info(
            "prepayment_timeout_already_handled",
            extra={"order_id": order_id, "status": order.status.value},
        )
        return True

    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .order_by(Allocation.created_at.desc())
        .first()
    )

    order.status = OrderStatus.CANCELLED

    if allocation:
        allocation.locked_until = None

    db.commit()

    logger.info(
        "prepayment_timeout_applied",
        extra={"order_id": order.id},
    )

    return True

