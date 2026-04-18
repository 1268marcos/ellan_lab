# 01_source/order_pickup_service/app/services/pickup_expiration_handler.py
# 18/04/2026 - novo
# 18/04/2026 - handler de expiração de retirada

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupLifecycleStage, PickupStatus
from app.services import backend_client
from app.services.pickup_event_publisher import publish_pickup_expired

logger = logging.getLogger(__name__)

MAX_RETRIES = 3

# REGRA OPERACIONAL:
# - pedido expira
# - alocação é liberada
# - runtime fica OUT_OF_STOCK por padrão, pois o item físico continua ocupando a gaveta
# Se sua regra de negócio for recolocar imediatamente à venda, troque para "AVAILABLE".
# RUNTIME_STATE_ON_PICKUP_EXPIRED = "OUT_OF_STOCK"
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


def _apply_internal_state(
    *,
    db: Session,
    order: Order,
    pickup: Pickup | None,
    allocation: Allocation | None,
) -> dict[str, Any]:
    now = _utc_now()

    # idempotência / terminal states
    if order.status in {
        OrderStatus.EXPIRED,
        OrderStatus.EXPIRED_CREDIT_50,
        OrderStatus.PICKED_UP,
        OrderStatus.CANCELLED,
    }:
        return {
            "already_terminal": True,
            "order_id": order.id,
            "allocation_id": allocation.id if allocation else None,
            "slot": allocation.slot if allocation else None,
            "region": order.region,
            "locker_id": _resolve_locker_id(order=order, allocation=allocation),
            "pickup_id": pickup.id if pickup else None,
        }

    order.mark_as_expired(credit_50=False)
    # IMPORTANTE:
    # pagamento já foi aprovado; não chamar mark_payment_expired() aqui.
    if hasattr(order, "pickup_deadline_at") and order.pickup_deadline_at:
        pass
    _touch(order)

    pickup_id: str | None = None
    if pickup:
        pickup_id = pickup.id

        if pickup.status not in {PickupStatus.REDEEMED, PickupStatus.CANCELLED, PickupStatus.EXPIRED}:
            pickup.status = PickupStatus.EXPIRED

        if hasattr(PickupLifecycleStage, "EXPIRED"):
            pickup.lifecycle_stage = PickupLifecycleStage.EXPIRED

        if hasattr(pickup, "expired_at"):
            pickup.expired_at = now

        if getattr(order, "pickup_deadline_at", None):
            pickup.expires_at = order.pickup_deadline_at
        elif hasattr(pickup, "expires_at") and pickup.expires_at is None:
            pickup.expires_at = now

        _touch(pickup)

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
            "order_status": str(order.status),
            "pickup_status": str(pickup.status) if pickup else None,
            "allocation_state": str(allocation.state) if allocation else None,
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
                break
            except Exception as exc:
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
                    "deadline_type": payload.get("deadline_type", "pickup_timeout"),
                    "order_status": str(order.status.value if hasattr(order.status, "value") else order.status),
                    "runtime_state": RUNTIME_STATE_ON_PICKUP_EXPIRED,
                },
            )
        except Exception:
            logger.exception(
                "pickup_expired_publish_event_failed",
                extra={"order_id": order.id, "pickup_id": result.get("pickup_id")},
            )

    _apply_external_effects(
        order_id=order.id,
        allocation_id=result.get("allocation_id"),
        slot=result.get("slot"),
        region=result["region"],
        locker_id=result.get("locker_id"),
    )

    return True


