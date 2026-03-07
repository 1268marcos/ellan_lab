# Router: /internal/* (protegido por X-Internal-Token)
from __future__ import annotations

import os
import uuid
import hashlib
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.internal_auth import require_internal_token

from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.models.pickup_token import PickupToken

from app.schemas.internal import InternalPaymentApprovedIn as PaymentConfirmIn
from app.services import backend_client

router = APIRouter(prefix="/internal", tags=["internal"])

PICKUP_WINDOW_HOURS = 2
QR_ROTATE_SEC = int(os.getenv("QR_ROTATE_SEC", "600"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_allocation(db: Session, order_id: str) -> Allocation:
    allocation = db.query(Allocation).filter(Allocation.order_id == order_id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail="allocation not found")
    return allocation


def _ensure_order(db: Session, order_id: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _generate_manual_code() -> str:
    return f"{uuid.uuid4().int % 1_000_000:06d}"


def _create_pickup_token(db: Session, *, order_id: str, expires_at_utc: datetime) -> dict:
    manual_code = _generate_manual_code()
    tok = PickupToken(
        id=str(uuid.uuid4()),
        order_id=order_id,
        token_hash=_sha256(manual_code),
        expires_at=expires_at_utc.replace(tzinfo=None),
        used_at=None,
    )
    db.add(tok)
    return {"token_id": tok.id, "manual_code": manual_code}


def _reallocate_if_needed(db: Session, *, order: Order, allocation: Allocation) -> Allocation:
    request_id = str(uuid.uuid4())
    alloc = backend_client.locker_allocate(order.region, order.sku_id, ttl_sec=120, request_id=request_id)

    new_allocation_id = alloc.get("allocation_id")
    new_slot = alloc.get("slot")

    if not new_allocation_id or new_slot is None:
        raise HTTPException(status_code=502, detail="reallocate failed: missing allocation_id/slot")

    try:
        allocation.state = AllocationState.RELEASED
        allocation.locked_until = None
    except Exception:
        pass

    new_alloc = Allocation(
        id=new_allocation_id,
        order_id=order.id,
        slot=int(new_slot),
        state=AllocationState.RESERVED_PENDING_PAYMENT,
        locked_until=None,
    )
    db.add(new_alloc)
    db.flush()
    return new_alloc


@router.get("/health")
def internal_health(_=Depends(require_internal_token)):
    return {"ok": True, "service": "order_pickup_service", "time": _utc_now().isoformat()}


@router.post("/orders/{order_id}/payment-confirm")
def payment_confirm(
    order_id: str,
    payload: PaymentConfirmIn,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    order = _ensure_order(db, order_id)

    if order.status != OrderStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    if getattr(payload, "region", None) and order.region != payload.region:
        raise HTTPException(status_code=409, detail=f"region mismatch: order={order.region} payload={payload.region}")

    allocation = _ensure_allocation(db, order.id)
    now = _utc_now()

    order.gateway_transaction_id = payload.transaction_id
    order.payment_method = getattr(payload, "provider", None)
    order.paid_at = now

    token_id: Optional[str] = None
    manual_code: Optional[str] = None

    if order.channel == OrderChannel.ONLINE:
        deadline = now + timedelta(hours=PICKUP_WINDOW_HOURS)

        order.pickup_deadline_at = deadline
        order.status = OrderStatus.PAID_PENDING_PICKUP

        allocation.state = AllocationState.RESERVED_PAID_PENDING_PICKUP
        allocation.locked_until = deadline.replace(tzinfo=None)

        try:
            backend_client.locker_commit(order.region, allocation.id, deadline.isoformat())
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 409:
                allocation = _reallocate_if_needed(db, order=order, allocation=allocation)

                allocation.state = AllocationState.RESERVED_PAID_PENDING_PICKUP
                allocation.locked_until = deadline.replace(tzinfo=None)

                backend_client.locker_commit(order.region, allocation.id, deadline.isoformat())
            else:
                raise

        backend_client.locker_set_state(order.region, allocation.slot, "PAID_PENDING_PICKUP")

        tok = _create_pickup_token(db, order_id=order.id, expires_at_utc=deadline)
        token_id = tok["token_id"]
        manual_code = tok["manual_code"]

    else:
        order.pickup_deadline_at = None
        order.mark_as_picked_up()
        allocation.state = AllocationState.OPENED_FOR_PICKUP

        try:
            backend_client.locker_commit(order.region, allocation.id, None)
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 409:
                allocation = _reallocate_if_needed(db, order=order, allocation=allocation)

                allocation.state = AllocationState.OPENED_FOR_PICKUP
                allocation.locked_until = None

                backend_client.locker_commit(order.region, allocation.id, None)
            else:
                raise

        backend_client.locker_light_on(order.region, allocation.slot)
        backend_client.locker_open(order.region, allocation.slot)

    db.commit()

    return {
        "ok": True,
        "order_id": order.id,
        "channel": order.channel.value,
        "status": order.status.value,
        "slot": allocation.slot,
        "payment_method": order.payment_method,
        "picked_up_at": order.picked_up_at.isoformat() if order.picked_up_at else None,
        "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
        "pickup_id": order.id if order.channel == OrderChannel.ONLINE else None,
        "token_id": token_id,
        "manual_code": manual_code,
        "qr_rotate_sec": QR_ROTATE_SEC if order.channel == OrderChannel.ONLINE else None,
    }


@router.post("/orders/{order_id}/release")
def release_order(
    order_id: str,
    reason: Optional[str] = None,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    order = _ensure_order(db, order_id)
    allocation = _ensure_allocation(db, order.id)

    if order.status in (OrderStatus.PICKED_UP,):
        raise HTTPException(status_code=409, detail=f"cannot release in state: {order.status.value}")

    try:
        backend_client.locker_release(order.region, allocation.id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"backend release failed: {str(e)}")

    order.status = OrderStatus.EXPIRED
    allocation.state = AllocationState.RELEASED
    allocation.locked_until = None

    db.commit()
    return {"ok": True, "order_id": order.id, "status": order.status.value, "reason": reason}


@router.post("/slots/{slot}/set-state")
def internal_set_slot_state(
    slot: int,
    state: str,
    region: str,
    _=Depends(require_internal_token),
):
    if slot < 1 or slot > 24:
        raise HTTPException(status_code=400, detail="slot must be between 1 and 24")
    if region not in ("SP", "PT"):
        raise HTTPException(status_code=400, detail="region must be SP or PT")

    try:
        resp = backend_client.locker_set_state(region, slot, state)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"backend set-state failed: {str(e)}")

    return {"ok": True, "region": region, "slot": slot, "state": state, "backend_response": resp}


@router.get("/orders/{order_id}/status")
def internal_order_status(
    order_id: str,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    order = _ensure_order(db, order_id)
    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()

    return {
        "ok": True,
        "order": {
            "id": order.id,
            "channel": order.channel.value,
            "region": order.region,
            "totem_id": order.totem_id,
            "sku_id": getattr(order, "sku_id", None),
            "status": order.status.value,
            "amount_cents": getattr(order, "amount_cents", None),
            "payment_method": getattr(order, "payment_method", None),
            "paid_at": order.paid_at.isoformat() if getattr(order, "paid_at", None) else None,
            "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
            "picked_up_at": order.picked_up_at.isoformat() if order.picked_up_at else None,
            "gateway_transaction_id": getattr(order, "gateway_transaction_id", None),
        },
        "allocation": None if not allocation else {
            "id": allocation.id,
            "slot": allocation.slot,
            "state": allocation.state.value,
            "locked_until": allocation.locked_until.isoformat() if allocation.locked_until else None,
        }
    }