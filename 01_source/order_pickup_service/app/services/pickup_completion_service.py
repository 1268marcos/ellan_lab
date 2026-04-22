# 01_source/order_pickup_service/app/services/pickup_completion_service.py
# 22/04/2026 - normaliza fechamento de pickup por evento door_closed

from __future__ import annotations

from datetime import datetime, timezone

from app.core.db import SessionLocal
from app.models.allocation import Allocation
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup, PickupLifecycleStage, PickupStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def finalize_pickup_after_door_closed(order_id: str) -> bool:
    db = SessionLocal()

    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return True

        pickup = (
            db.query(Pickup)
            .filter(Pickup.order_id == order_id)
            .order_by(Pickup.created_at.desc(), Pickup.id.desc())
            .first()
        )
        allocation = (
            db.query(Allocation)
            .filter(Allocation.order_id == order_id)
            .order_by(Allocation.created_at.desc(), Allocation.id.desc())
            .first()
        )

        now = _utc_now()

        if pickup:
            pickup.lifecycle_stage = PickupLifecycleStage.DOOR_CLOSED
            pickup.door_closed_at = pickup.door_closed_at or now

            # Sem evidência forte no fechamento puro de porta: manter unverified.
            if hasattr(pickup, "machine_state"):
                pickup.machine_state = "CLOSED_AFTER_OPEN"
            if hasattr(pickup, "pickup_phase"):
                pickup.pickup_phase = "COMPLETED_UNVERIFIED"
            if hasattr(pickup, "evidence_score"):
                pickup.evidence_score = max(int(getattr(pickup, "evidence_score", 0) or 0), 60)
            if hasattr(pickup, "evidence_strength"):
                pickup.evidence_strength = "MEDIUM"

            # Modelo legado continua consistente para consumidores atuais.
            pickup.status = PickupStatus.REDEEMED
            pickup.redeemed_at = pickup.redeemed_at or now
            pickup.current_token_id = None
            pickup.touch()

        order.picked_up_at = order.picked_up_at or now
        if order.status != OrderStatus.PICKED_UP:
            order.status = OrderStatus.DISPENSED
        order.updated_at = now

        if allocation:
            try:
                allocation.mark_released()
            except Exception:
                allocation.state = "RELEASED"
                if hasattr(allocation, "updated_at"):
                    allocation.updated_at = now

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

