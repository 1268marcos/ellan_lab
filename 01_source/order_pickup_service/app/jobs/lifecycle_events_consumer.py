# 01_source/order_pickup_service/app/jobs/lifecycle_events_consumer.py
from __future__ import annotations

import logging
import os
from typing import Any

from sqlalchemy.orm import Session

from app.core.lifecycle_events_client import (
    LifecycleEventsClient,
    LifecycleEventsClientError,
)
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupStatus
from app.services import backend_client

logger = logging.getLogger(__name__)

LIFECYCLE_EVENTS_BATCH_SIZE = int(os.getenv("LIFECYCLE_EVENTS_BATCH_SIZE", "100"))


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
        if event_name != "order.prepayment_timed_out":
            continue

        event_key = item.get("event_key")
        payload = item.get("payload") or {}
        order_id = payload.get("order_id") or item.get("aggregate_id")

        if not event_key or not order_id:
            logger.warning(
                "lifecycle_event_missing_fields",
                extra={"event_key": event_key, "order_id": order_id},
            )
            continue

        try:
            handled = _handle_prepayment_timeout(db=db, order_id=order_id, payload=payload)
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
                extra={"event_key": event_key, "order_id": order_id},
            )
            db.rollback()

    if processed:
        logger.info("lifecycle_events_processed", extra={"processed": processed})

    return processed


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

    # Idempotência: se já saiu do pré-pagamento, o evento pode ser reconhecido
    if order.status != OrderStatus.PAYMENT_PENDING:
        logger.info(
            "prepayment_timeout_already_handled",
            extra={"order_id": order_id, "status": order.status.value},
        )
        return True

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    pickup = db.query(Pickup).filter(Pickup.order_id == order.id).first()

    region = payload.get("region_code") or order.region
    locker_id = _resolve_locker_id(order=order, allocation=allocation)

    if allocation and allocation.id:
        try:
            backend_client.locker_release(
                region,
                allocation.id,
                locker_id=locker_id,
            )

            # Pré-pagamento expirado: slot volta a ficar disponível
            if allocation.slot is not None:
                backend_client.locker_set_state(
                    region,
                    int(allocation.slot),
                    "AVAILABLE",
                    locker_id=locker_id,
                )
        except Exception:
            logger.exception(
                "prepayment_timeout_release_failed",
                extra={
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "slot": allocation.slot,
                    "region": region,
                    "locker_id": locker_id,
                },
            )
            raise

    order.status = OrderStatus.EXPIRED
    order.mark_payment_expired()

    if allocation:
        allocation.mark_released()

    if pickup and pickup.status == PickupStatus.ACTIVE:
        pickup.status = PickupStatus.CANCELLED

    db.commit()

    logger.info(
        "prepayment_timeout_applied",
        extra={
            "order_id": order.id,
            "region": region,
            "locker_id": locker_id,
            "allocation_id": allocation.id if allocation else None,
            "slot": allocation.slot if allocation else None,
        },
    )
    return True