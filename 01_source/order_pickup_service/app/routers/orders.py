# 01_source/order_pickup_service/app/routers/orders.py
# Router: /orders (ONLINE)
# Aqui faz pedido ONLINE
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from requests import HTTPError
from sqlalchemy.orm import Session

from app.core.auth_dev import get_current_user_or_dev
from app.core.db import get_db
from app.core.lifecycle_client import LifecycleClientError
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.pickup import Pickup
from app.schemas.orders import CreateOrderIn, OrderListItemOut, OrderListOut, OrderOut
from app.services import backend_client
from app.services.lifecycle_integration import register_prepayment_timeout_deadline

router = APIRouter(prefix="/orders", tags=["orders"])

ALLOC_TTL_SEC = 120


@router.post("", response_model=OrderOut)
def create_order(
    payload: CreateOrderIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    amount_cents = None

    if payload.amount_cents is not None:
        if int(payload.amount_cents) <= 0:
            raise HTTPException(status_code=400, detail="amount_cents must be > 0")
        amount_cents = int(payload.amount_cents)

    if amount_cents is None:
        try:
            pricing = backend_client.get_sku_pricing(payload.region, payload.sku_id)
        except HTTPError as e:
            if (
                e.response is not None
                and e.response.status_code == 404
                and os.getenv("DEV_ALLOW_UNKNOWN_SKU", "false").lower() == "true"
            ):
                pricing = {"amount_cents": int(os.getenv("DEV_DEFAULT_PRICE_CENTS", "1000"))}
            else:
                raise

        amount_cents = pricing.get("amount_cents") or pricing.get("price_cents")
        if amount_cents is None:
            raise HTTPException(
                status_code=502,
                detail="pricing missing amount_cents/price_cents from backend",
            )

    request_id = str(uuid.uuid4())

    try:
        alloc = backend_client.locker_allocate(
            payload.region,
            payload.sku_id,
            ALLOC_TTL_SEC,
            request_id,
            payload.desired_slot,
        )
    except HTTPError as e:
        status = e.response.status_code if e.response is not None else 502

        backend_detail = None
        if e.response is not None:
            try:
                backend_detail = e.response.json()
            except Exception:
                backend_detail = e.response.text

        if status == 409:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "DESIRED_SLOT_UNAVAILABLE",
                    "message": "A gaveta escolhida não está disponível para reserva.",
                    "desired_slot": payload.desired_slot,
                    "backend_detail": backend_detail,
                },
            )

        raise HTTPException(
            status_code=502,
            detail={
                "type": "LOCKER_ALLOCATE_FAILED",
                "message": "Falha ao alocar gaveta no backend.",
                "backend_status": status,
                "backend_detail": backend_detail,
            },
        )

    allocation_id = alloc.get("allocation_id")
    slot = alloc.get("slot")
    ttl_sec = int(alloc.get("ttl_sec", ALLOC_TTL_SEC))

    if not allocation_id or slot is None:
        raise HTTPException(status_code=502, detail="locker allocate missing allocation_id/slot")

    order = Order(
        id=str(uuid.uuid4()),
        user_id=user.id,
        channel=OrderChannel.ONLINE,
        region=payload.region,
        totem_id=payload.totem_id,
        sku_id=payload.sku_id,
        amount_cents=int(amount_cents),
        status=OrderStatus.PAYMENT_PENDING,
        payment_method=None,
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
    db.refresh(order)
    db.refresh(allocation)

    try:
        register_prepayment_timeout_deadline(
            order_id=order.id,
            order_channel=order.channel.value,
            region_code=order.region,
            slot_id=str(allocation.slot),
            machine_id=order.totem_id,
            created_at=order.created_at,
        )
    except LifecycleClientError:
        raise HTTPException(
            status_code=503,
            detail={
                "type": "LIFECYCLE_DEADLINE_REGISTER_FAILED",
                "message": "Pedido criado localmente, mas falhou ao registrar o deadline de pré-pagamento.",
                "order_id": order.id,
                "channel": order.channel.value,
                "region": order.region,
            },
        )

    return OrderOut(
        order_id=order.id,
        channel=order.channel.value,
        status=order.status.value,
        amount_cents=order.amount_cents,
        payment_method=order.payment_method,
        allocation={
            "allocation_id": allocation.id,
            "slot": allocation.slot,
            "ttl_sec": ttl_sec,
        },
    )


@router.get("", response_model=OrderListOut)
def list_orders(
    region: str | None = None,
    status: str | None = None,
    channel: str | None = None,
    scope: str | None = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    q = db.query(Order)

    if scope != "ops" and getattr(user, "id", None):
        q = q.filter(Order.user_id == user.id)

    if region:
        q = q.filter(Order.region == region)

    if status:
        try:
            status_enum = OrderStatus(status)
            q = q.filter(Order.status == status_enum)
        except Exception:
            raise HTTPException(status_code=400, detail=f"invalid status: {status}")

    if channel:
        try:
            channel_enum = OrderChannel(channel)
            q = q.filter(Order.channel == channel_enum)
        except Exception:
            raise HTTPException(status_code=400, detail=f"invalid channel: {channel}")

    total = q.count()

    orders = (
        q.order_by(Order.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    items = []
    for order in orders:
        allocation = (
            db.query(Allocation)
            .filter(Allocation.order_id == order.id)
            .order_by(Allocation.created_at.desc(), Allocation.id.desc())
            .first()
        )

        pickup = (
            db.query(Pickup)
            .filter(Pickup.order_id == order.id)
            .order_by(Pickup.created_at.desc(), Pickup.id.desc())
            .first()
        )

        items.append(
            OrderListItemOut(
                order_id=order.id,
                user_id=order.user_id,
                region=order.region,
                channel=order.channel.value,
                status=order.status.value,
                sku_id=order.sku_id,
                totem_id=order.totem_id,
                amount_cents=order.amount_cents,
                payment_method=order.payment_method,
                allocation_id=allocation.id if allocation else None,
                slot=allocation.slot if allocation else None,
                allocation_state=allocation.state.value if allocation and allocation.state else None,
                pickup_id=pickup.id if pickup else None,
                pickup_status=pickup.status.value if pickup and pickup.status else None,
                expires_at=pickup.expires_at if pickup else None,
                created_at=order.created_at,
                paid_at=order.paid_at,
                pickup_deadline_at=order.pickup_deadline_at,
                picked_up_at=order.picked_up_at,
            )
        )

    has_prev = page > 1
    has_next = offset + len(items) < total

    return OrderListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_prev=has_prev,
    )