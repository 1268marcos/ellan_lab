# 01_source/order_pickup_service/app/routers/orders.py
# Router: /orders (ONLINE)
# Aqui faz pedido ONLINE
# 13/04/2026 - inclusão da função def resolve_operational_status()

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth_dev import get_current_user_or_dev
from app.core.db import get_db
from app.models.allocation import Allocation
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.pickup import Pickup
from app.schemas.orders import CreateOrderIn, OrderListItemOut, OrderListOut, OrderOut
from app.services.order_creation_service import create_order_core

from datetime import datetime
from datetime import timezone

from app.services import backend_client


router = APIRouter(prefix="/orders", tags=["orders"])


def resolve_operational_status(order: Order, allocation: Allocation | None) -> str:
    
    if order.status == OrderStatus.FAILED:
        return "FAILED"

    # 🔥 sem allocation → expirado
    if not allocation:
        return "EXPIRED"

    # 🔥 runtime
    try:
        state = backend_client.get_allocation_state(
            allocation.id,
            locker_id=order.totem_id
        )
    except Exception:
        return "UNKNOWN"

    if state in ["RELEASED", "EXPIRED", "NOT_FOUND"]:
        return "EXPIRED"

    # 🔥 deadline
    if order.pickup_deadline_at:
        if order.pickup_deadline_at < datetime.now(timezone.utc):
            return "EXPIRED"

    return order.status.value






@router.post("", response_model=OrderOut)
def create_order(
    payload: CreateOrderIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    """
    CREATE ORDER (ONLINE)

    Corrigido para:
    - Usar capability profile (sem if / sem hardcoded)
    - Passar TODOS os campos necessários para o service
    - Não perder payment_interface / wallet_provider
    """

    resolved_user_id = getattr(user, "id", None)
    resolved_user_id = str(resolved_user_id) if resolved_user_id is not None else None

    result = create_order_core(
        db=db,
        region=payload.region.value,
        sku_id=payload.sku_id,
        totem_id=payload.totem_id,
        desired_slot=payload.desired_slot,

        # 🔴 IMPORTANTE: valor direto do payload (será resolvido via DB)
        payment_method_value=payload.payment_method.value,

        # 🔴 NOVO: card_type suportado corretamente
        card_type_value=payload.card_type.value if payload.card_type else None,

        # 🔴 IMPORTANTE: não confiar no frontend (service resolve se None)
        amount_cents_input=payload.amount_cents,

        guest_phone=payload.customer_phone,
        user_id=resolved_user_id,

        # 🔴 NOVOS CAMPOS (antes ignorados)
        payment_interface=payload.payment_interface,
        wallet_provider=payload.wallet_provider,
        customer_email=payload.customer_email,
        device_id=payload.device_id,
        ip_address=payload.ip_address,
    )

    order = result.order
    allocation = result.allocation

    return OrderOut(
        order_id=order.id,
        channel=order.channel.value,
        status=order.status.value,
        amount_cents=order.amount_cents,
        payment_method=order.payment_method.value if order.payment_method else None,
        allocation={
            "allocation_id": allocation.id,
            "slot": allocation.slot,
            "ttl_sec": result.ttl_sec,
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
    """
    LIST ORDERS

    Mantido (já estava correto)
    """

    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size

    q = db.query(Order)

    if scope != "ops" and getattr(user, "id", None):
        q = q.filter(Order.user_id == str(user.id))

    if region:
        q = q.filter(Order.region == region)

    if status:
        try:
            status_enum = OrderStatus(status)
            q = q.filter(Order.status == status_enum)
        except Exception:
            raise ValueError(f"invalid status: {status}")

    if channel:
        try:
            channel_enum = OrderChannel(channel)
            q = q.filter(Order.channel == channel_enum)
        except Exception:
            raise ValueError(f"invalid channel: {channel}")

    total = q.count()

    orders = q.order_by(Order.created_at.desc()).offset(offset).limit(page_size).all()

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

        normalized_user_id = str(order.user_id) if order.user_id is not None else None

        items.append(
            OrderListItemOut(
                order_id=order.id,
                user_id=normalized_user_id,
                region=order.region,
                channel=order.channel.value,
                # status=order.status.value,
                status=resolve_operational_status(order, allocation),
                sku_id=order.sku_id,
                totem_id=order.totem_id,
                locker_id=allocation.locker_id if allocation and allocation.locker_id else order.totem_id,
                amount_cents=order.amount_cents,
                payment_method=order.payment_method.value if order.payment_method else None,
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

