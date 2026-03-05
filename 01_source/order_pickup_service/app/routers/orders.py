# Router: /orders (ONLINE)
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth_dev import get_current_user_or_dev
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.services import backend_client
from app.schemas.orders import CreateOrderIn, OrderOut

from requests import HTTPError
import os

router = APIRouter(prefix="/orders", tags=["orders"])

ALLOC_TTL_SEC = 120

@router.post("", response_model=OrderOut)
def create_order(payload: CreateOrderIn, db: Session = Depends(get_db), user=Depends(get_current_user_or_dev)):
    # 1) preço no backend (fonte de verdade)
    # pricing = backend_client.get_sku_pricing(payload.region, payload.sku_id)
    try:
        pricing = backend_client.get_sku_pricing(payload.region, payload.sku_id)
    except HTTPError as e:
        if e.response is not None and e.response.status_code == 404 and os.getenv("DEV_ALLOW_UNKNOWN_SKU", "false").lower() == "true":
            pricing = {"amount_cents": int(os.getenv("DEV_DEFAULT_PRICE_CENTS", "1000"))}
        else:
            raise

    amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")
    if amount_cents is None:
        raise HTTPException(status_code=502, detail="pricing missing amount_cents/price_cents from backend")

    # 2) allocate
    request_id = str(uuid.uuid4())
    alloc = backend_client.locker_allocate(payload.region, payload.sku_id, ALLOC_TTL_SEC, request_id)

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    ttl_sec = alloc.get("ttl_sec", ALLOC_TTL_SEC)

    if not allocation_id or not slot:
        raise HTTPException(status_code=502, detail="locker allocate missing allocation_id/slot")

    # 3) persist
    order = Order(
        id=str(uuid.uuid4()),
        user_id=user.id,
        channel=OrderChannel.ONLINE,
        region=payload.region,
        totem_id=payload.totem_id,
        sku_id=payload.sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
    )
    db.add(order)
    db.flush()

    allocation = Allocation(
        id=allocation_id,
        order_id=order.id,
        slot=int(slot),
        state=AllocationState.RESERVED_PENDING_PAYMENT,
        locked_until=None,
    )
    db.add(allocation)
    db.commit()

    return OrderOut(
        order_id=order.id,
        channel=order.channel.value,
        status=order.status.value,
        amount_cents=order.amount_cents,
        allocation={"allocation_id": allocation.id, "slot": allocation.slot, "ttl_sec": ttl_sec},
    )