from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.allocation import Allocation
from app.models.order import Order
from app.models.pickup import Pickup, PickupStatus
from app.services import backend_client
from app.services.credits_service import restore_credit_after_failed_order_creation


@dataclass
class OrderReconciliationResult:
    credit_restored: bool
    credit_restore_error: str | None
    slot_release_attempted: bool
    slot_release_ok: bool
    slot_release_error: str | None
    allocation_id: str | None
    allocation_state: str | None


def restore_checkout_credit_if_needed(*, db: Session, order: Order) -> bool:
    return bool(
        restore_credit_after_failed_order_creation(
            db=db,
            order_metadata=getattr(order, "order_metadata", None),
        )
    )


def mark_allocation_released_locally(*, allocation: Allocation | None) -> str | None:
    if not allocation:
        return None
    allocation.mark_released()
    return allocation.state.value if allocation.state else None


def resolve_latest_allocation(db: Session, *, order: Order) -> Allocation | None:
    allocation = None
    if getattr(order, "allocation_id", None):
        allocation = db.query(Allocation).filter(Allocation.id == order.allocation_id).first()
    if allocation is None:
        allocation = (
            db.query(Allocation)
            .filter(Allocation.order_id == order.id)
            .order_by(Allocation.created_at.desc(), Allocation.id.desc())
            .first()
        )
    return allocation


def resolve_latest_pickup(db: Session, *, order: Order) -> Pickup | None:
    return (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )


def reconcile_order_compensation(
    *,
    db: Session,
    order: Order,
    allocation: Allocation | None,
    pickup: Pickup | None,
    cancel_reason: str = "public_order_cancelled",
    record_pending_on_failure: bool = True,
) -> OrderReconciliationResult:
    slot_release_ok = False
    slot_release_error: str | None = None
    slot_release_attempted = False

    if allocation:
        slot_release_attempted = True
        try:
            backend_client.locker_release(
                order.region,
                allocation.id,
                locker_id=order.totem_id,
            )
            mark_allocation_released_locally(allocation=allocation)
            slot_release_ok = True
        except Exception as exc:
            slot_release_error = str(exc)

    credit_restored = False
    credit_restore_error: str | None = None
    try:
        credit_restored = restore_checkout_credit_if_needed(db=db, order=order)
    except Exception as exc:
        credit_restore_error = str(exc)

    if pickup and pickup.status != PickupStatus.CANCELLED:
        pickup.mark_cancelled(cancel_reason)

    if record_pending_on_failure:
        try:
            from app.services.reconciliation_pending_service import (
                enqueue_reconciliation_pending,
            )

            common_payload = {
                "order_id": order.id,
                "region": getattr(order, "region", None),
                "locker_id": getattr(order, "totem_id", None),
                "allocation_id": allocation.id if allocation else None,
                "pickup_id": pickup.id if pickup else None,
            }
            if slot_release_error:
                enqueue_reconciliation_pending(
                    db=db,
                    order_id=order.id,
                    reason="slot_release_failed",
                    payload={
                        **common_payload,
                        "error": slot_release_error,
                    },
                )
            if credit_restore_error:
                enqueue_reconciliation_pending(
                    db=db,
                    order_id=order.id,
                    reason="credit_restore_failed",
                    payload={
                        **common_payload,
                        "error": credit_restore_error,
                    },
                )
        except Exception:
            # Falha de enfileiramento não deve interromper o fluxo síncrono.
            pass

    return OrderReconciliationResult(
        credit_restored=bool(credit_restored),
        credit_restore_error=credit_restore_error,
        slot_release_attempted=bool(slot_release_attempted),
        slot_release_ok=bool(slot_release_ok),
        slot_release_error=slot_release_error,
        allocation_id=allocation.id if allocation else None,
        allocation_state=allocation.state.value if allocation and allocation.state else None,
    )

