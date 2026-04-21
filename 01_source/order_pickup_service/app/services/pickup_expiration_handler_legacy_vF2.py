# 01_source/order_pickup_service/app/services/pickup_expiration_handler.py
# 21/04/2026 - hardening expiração de retirada
# - expira order/pickup/allocation
# - invalida tokens ativos
# - runtime -> AVAILABLE
# - idempotente

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupLifecycleStage, PickupStatus
from app.models.pickup_token import PickupToken
from app.services import backend_client
from app.services.pickup_event_publisher import publish_pickup_expired

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RUNTIME_STATE_ON_PICKUP_EXPIRED = "AVAILABLE"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_locker_id(*, order: Order, allocation: Allocation | None) -> str | None:
    if allocation and getattr(allocation, "locker_id", None):
        return allocation.locker_id
    if getattr(order, "totem_id", None):
        return order.totem_id
    return None


def _touch(model: Any) -> None:
    if hasattr(model, "touch") and callable(model.touch):
        model.touch()
    elif hasattr(model, "updated_at"):
        model.updated_at = _utc_now()


def _invalidate_active_tokens(
    *,
    db: Session,
    pickup: Pickup | None,
    now: datetime,
) -> int:
    if not pickup:
        return 0

    updated = (
        db.query(PickupToken)
        .filter(
            PickupToken.pickup_id == pickup.id,
            PickupToken.used_at.is_(None),
        )
        .update(
            {"used_at": now.replace(tzinfo=None)},
            synchronize_session=False,
        )
    )
    return int(updated or 0)


def _apply_internal_state(
    *,
    db: Session,
    order: Order,
    pickup: Pickup | None,
    allocation: Allocation | None,
) -> dict[str, Any]:
    now = _utc_now()

    if order.status in {
        OrderStatus.EXPIRED,
        OrderStatus.EXPIRED_CREDIT_50,
        OrderStatus.PICKED_UP,
        OrderStatus.CANCELLED,
        OrderStatus.REFUNDED,
        OrderStatus.FAILED,
    }:
        return {
            "already_terminal": True,
            "order_id": order.id,
            "allocation_id": allocation.id if allocation else None,
            "slot": allocation.slot if allocation else None,
            "region": order.region,
            "locker_id": _resolve_locker_id(order=order, allocation=allocation),
            "pickup_id": pickup.id if pickup else None,
            "invalidated_tokens": 0,
        }

    order.status = OrderStatus.EXPIRED
    _touch(order)

    pickup_id: str | None = None
    invalidated_tokens = 0

    if pickup:
        pickup_id = pickup.id
        pickup.status = PickupStatus.EXPIRED
        pickup.lifecycle_stage = PickupLifecycleStage.EXPIRED
        pickup.expired_at = now

        if getattr(order, "pickup_deadline_at", None):
            pickup.expires_at = order.pickup_deadline_at
        elif getattr(pickup, "expires_at", None) is None:
            pickup.expires_at = now

        _touch(pickup)

        invalidated_tokens = _invalidate_active_tokens(
            db=db,
            pickup=pickup,
            now=now,
        )

    alloc_id: str | None = None
    slot: int | None = None

    if allocation:
        alloc_id = allocation.id
        slot = allocation.slot
        allocation.state = AllocationState.RELEASED
        if hasattr(allocation, "released_at"):
            allocation.released_at = now
        allocation.locked_until = None
        _touch(allocation)

    db.flush()
    db.commit()

    locker_id = _resolve_locker_id(order=order, allocation=allocation)

    logger.info(
        "pickup_expired_internal_state_applied",
        extra={
            "order_id": order.id,
            "pickup_id": pickup_id,
            "allocation_id": alloc_id,
            "slot": slot,
            "region": order.region,
            "locker_id": locker_id,
            "order_status": getattr(order.status, "value", order.status),
            "pickup_status": getattr(pickup.status, "value", None) if pickup else None,
            "allocation_state": getattr(allocation.state, "value", None) if allocation else None,
            "invalidated_tokens": invalidated_tokens,
        },
    )

    return {
        "already_terminal": False,
        "order_id": order.id,
        "pickup_id": pickup_id,
        "allocation_id": alloc_id,
        "slot": slot,
        "region": order.region,
        "locker_id": locker_id,
        "invalidated_tokens": invalidated_tokens,
    }


def _apply_external_effects(
    *,
    order_id: str,
    allocation_id: str | None,
    slot: int | None,
    region: str,
    locker_id: str | None,
) -> None:
    if slot is not None:
        for attempt in range(MAX_RETRIES):
            try:
                backend_client.locker_set_state(
                    region=region,
                    slot=int(slot),
                    state=RUNTIME_STATE_ON_PICKUP_EXPIRED,
                    locker_id=locker_id,
                )
                logger.info(
                    "pickup_expired_set_state_succeeded",
                    extra={
                        "order_id": order_id,
                        "slot": slot,
                        "region": region,
                        "locker_id": locker_id,
                        "runtime_state": RUNTIME_STATE_ON_PICKUP_EXPIRED,
                    },
                )
                break
            except Exception:
                if attempt == MAX_RETRIES - 1:
                    logger.exception(
                        "pickup_expired_set_state_failed",
                        extra={
                            "order_id": order_id,
                            "slot": slot,
                            "region": region,
                            "locker_id": locker_id,
                            "runtime_state": RUNTIME_STATE_ON_PICKUP_EXPIRED,
                        },
                    )
                else:
                    logger.warning(
                        "pickup_expired_set_state_retry",
                        extra={
                            "attempt": attempt + 1,
                            "order_id": order_id,
                            "slot": slot,
                            "region": region,
                            "locker_id": locker_id,
                        },
                    )

    if allocation_id:
        for attempt in range(MAX_RETRIES):
            try:
                backend_client.locker_release(
                    region=region,
                    allocation_id=allocation_id,
                    locker_id=locker_id,
                )
                logger.info(
                    "pickup_expired_locker_release_succeeded",
                    extra={
                        "order_id": order_id,
                        "allocation_id": allocation_id,
                        "region": region,
                        "locker_id": locker_id,
                    },
                )
                break
            except Exception:
                if attempt == MAX_RETRIES - 1:
                    logger.exception(
                        "pickup_expired_locker_release_failed",
                        extra={
                            "order_id": order_id,
                            "allocation_id": allocation_id,
                            "region": region,
                            "locker_id": locker_id,
                        },
                    )
                else:
                    logger.warning(
                        "pickup_expired_locker_release_retry",
                        extra={
                            "attempt": attempt + 1,
                            "order_id": order_id,
                            "allocation_id": allocation_id,
                            "region": region,
                            "locker_id": locker_id,
                        },
                    )


def handle_pickup_expired(
    *,
    db: Session,
    order_id: str,
    payload: dict[str, Any] | None = None,
) -> bool:
    payload = payload or {}

    logger.info(
        "handle_pickup_expired_started",
        extra={"order_id": order_id, "payload": payload},
    )

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        logger.warning("pickup_expired_order_not_found", extra={"order_id": order_id})
        return True

    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order_id)
        .order_by(Pickup.created_at.desc())
        .first()
    )

    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order_id)
        .order_by(Allocation.created_at.desc())
        .first()
    )

    result = _apply_internal_state(
        db=db,
        order=order,
        pickup=pickup,
        allocation=allocation,
    )

    if not result["already_terminal"] and result.get("pickup_id"):
        try:
            publish_pickup_expired(
                order_id=order.id,
                pickup_id=result["pickup_id"],
                channel=getattr(order, "channel", None).value if getattr(order, "channel", None) else None,
                region=order.region,
                locker_id=result["locker_id"],
                machine_id=result["locker_id"],
                slot=str(result["slot"]) if result["slot"] is not None else None,
                correlation_id=payload.get("correlation_id"),
                payload={
                    "reason": payload.get("reason", "pickup_not_redeemed_before_deadline"),
                    "deadline_type": payload.get("deadline_type", "PICKUP_TIMEOUT"),
                    "order_status": getattr(order.status, "value", order.status),
                    "runtime_state": RUNTIME_STATE_ON_PICKUP_EXPIRED,
                    "invalidated_tokens": result.get("invalidated_tokens", 0),
                },
            )
        except Exception:
            logger.exception(
                "pickup_expired_publish_event_failed",
                extra={"order_id": order.id, "pickup_id": result.get("pickup_id")},
            )

    logger.info(
        "pickup_expired_external_effects_started",
        extra={
            "order_id": order.id,
            "allocation_id": result.get("allocation_id"),
            "slot": result.get("slot"),
            "region": result.get("region"),
            "locker_id": result.get("locker_id"),
            "runtime_state": RUNTIME_STATE_ON_PICKUP_EXPIRED,
        },
    )

    _apply_external_effects(
        order_id=order.id,
        allocation_id=result.get("allocation_id"),
        slot=result.get("slot"),
        region=result["region"],
        locker_id=result.get("locker_id"),
    )

    return True


