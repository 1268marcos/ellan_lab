from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.allocation import Allocation
from app.models.order import Order
from app.models.pickup import Pickup

router = APIRouter(prefix="/api/v1/support", tags=["Suporte N1/N2 MVP"])


def _enum_value(value) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def _dt_iso(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return str(value)


def _event(kind: str, status: str | None, timestamp: str | None, detail: dict) -> dict:
    return {
        "kind": kind,
        "status": status,
        "timestamp": timestamp,
        "detail": detail,
    }


@router.get("/health")
async def health():
    return {"status": "ok", "service": "support-n1-n2"}


@router.get("/orders/{order_id}/timeline")
async def get_order_timeline(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Order not found for support timeline.",
                "order_id": order_id,
            },
        )

    allocation = db.query(Allocation).filter(Allocation.order_id == order_id).first()
    pickup = db.query(Pickup).filter(Pickup.order_id == order_id).first()

    events = [
        _event(
            "order",
            _enum_value(order.status),
            _dt_iso(getattr(order, "created_at", None)),
            {
                "order_id": order.id,
                "channel": _enum_value(getattr(order, "channel", None)),
                "region": getattr(order, "region", None),
                "payment_method": _enum_value(getattr(order, "payment_method", None)),
            },
        )
    ]

    if allocation:
        events.append(
            _event(
                "allocation",
                _enum_value(allocation.state),
                _dt_iso(getattr(allocation, "updated_at", None)),
                {
                    "allocation_id": allocation.id,
                    "locker_id": allocation.locker_id,
                    "slot": allocation.slot,
                },
            )
        )

    if pickup:
        events.append(
            _event(
                "pickup",
                _enum_value(pickup.status),
                _dt_iso(getattr(pickup, "updated_at", None)),
                {
                    "pickup_id": pickup.id,
                    "lifecycle_stage": _enum_value(pickup.lifecycle_stage),
                    "locker_id": pickup.locker_id,
                    "slot": pickup.slot,
                    "expires_at": _dt_iso(pickup.expires_at),
                },
            )
        )

    next_action = "review_order_state"
    if pickup and _enum_value(pickup.status) == "ACTIVE":
        next_action = "guide_customer_to_pickup"
    elif allocation and _enum_value(allocation.state) in {"ERROR", "MAINTENANCE"}:
        next_action = "escalate_to_n2"

    return {
        "status": "ok",
        "service": "support-n1-n2",
        "order_id": order_id,
        "summary": {
            "order_status": _enum_value(order.status),
            "allocation_state": _enum_value(allocation.state) if allocation else None,
            "pickup_status": _enum_value(pickup.status) if pickup else None,
            "next_action": next_action,
        },
        "events": events,
    }
