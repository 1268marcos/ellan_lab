# 01_source/order_pickup_service/app/routers/orders.py
# Router: /orders (ONLINE)
# Aqui faz pedido ONLINE
# 13/04/2026 - inclusão da função def resolve_operational_status()

from datetime import datetime
from datetime import timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.auth_dev import get_current_user_or_dev
from app.core.db import get_db
from app.models.allocation import Allocation
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.pickup import Pickup
from app.schemas.orders import CreateOrderIn, OrderListItemOut, OrderListOut, OrderOut
from app.services.order_creation_service import create_order_core

from app.services import backend_client
from app.schemas.integration_ops import (
    OrderEventOutboxItemOut,
    OrderEventOutboxListOut,
    OrderEventOutboxReplayOut,
    OrderFulfillmentTrackingItemOut,
)


router = APIRouter(prefix="/orders", tags=["orders"])


def resolve_operational_status(order: Order, allocation: Allocation | None) -> str:
    
    # if order.status == OrderStatus.FAILED:
    #     return "FAILED"

    # 🔒 estados finais/canônicos do pedido não devem ser sobrescritos
    if order.status in {
        OrderStatus.DISPENSED,
        OrderStatus.PICKED_UP,
        OrderStatus.CANCELLED,
        OrderStatus.REFUNDED,
        OrderStatus.FAILED,
        OrderStatus.EXPIRED,
        OrderStatus.EXPIRED_CREDIT_50,
    }:
        return order.status.value

    # 🔥 sem allocation → expirado,  sem allocation só é problema para pedidos não finais
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

    # if state in ["RELEASED", "EXPIRED", "NOT_FOUND"]:
    #    return "EXPIRED"
   
    # 🔥 NOT_FOUND não pode derrubar KIOSK já dispensado
    if state in ["RELEASED", "EXPIRED"]:
        return "EXPIRED"


    # 🔥 deadline
    # if order.pickup_deadline_at:
    #     if order.pickup_deadline_at < datetime.now(timezone.utc):
    #         return "EXPIRED"
        
    if order.pickup_deadline_at:
        now_utc = datetime.now(timezone.utc)
        deadline = order.pickup_deadline_at
        if getattr(deadline, "tzinfo", None) is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if deadline < now_utc:
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
        order_line_ncm=payload.ncm,
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


def _to_iso_utc(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


@router.get("/{order_id}/fulfillment", response_model=OrderFulfillmentTrackingItemOut)
def get_order_fulfillment(
    order_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    _ = user
    row = db.execute(
        text(
            """
            SELECT id, order_id, fulfillment_type, partner_id, status, last_event_type, last_outbox_status, updated_at
            FROM order_fulfillment_tracking
            WHERE order_id = :order_id
            """
        ),
        {"order_id": str(order_id).strip()},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"type": "ORDER_FULFILLMENT_NOT_FOUND", "message": "Fulfillment tracking não encontrado para o pedido."},
        )
    return OrderFulfillmentTrackingItemOut(
        id=str(row.get("id") or ""),
        order_id=str(row.get("order_id") or ""),
        fulfillment_type=str(row.get("fulfillment_type") or ""),
        partner_id=(str(row.get("partner_id")) if row.get("partner_id") is not None else None),
        status=str(row.get("status") or ""),
        last_event_type=(str(row.get("last_event_type")) if row.get("last_event_type") is not None else None),
        last_outbox_status=(str(row.get("last_outbox_status")) if row.get("last_outbox_status") is not None else None),
        updated_at=_to_iso_utc(row.get("updated_at")),
    )


@router.get("/{order_id}/partner-events", response_model=OrderEventOutboxListOut)
def get_order_partner_events(
    order_id: str,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    _ = user
    normalized_order_id = str(order_id).strip()
    total_row = db.execute(
        text("SELECT COUNT(*) AS total FROM partner_order_events_outbox WHERE order_id = :order_id"),
        {"order_id": normalized_order_id},
    ).mappings().first()
    total = int((total_row or {}).get("total") or 0)
    rows = db.execute(
        text(
            """
            SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
            FROM partner_order_events_outbox
            WHERE order_id = :order_id
            ORDER BY created_at DESC, id DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {"order_id": normalized_order_id, "limit": int(limit), "offset": int(offset)},
    ).mappings().all()
    items = [
        OrderEventOutboxItemOut(
            id=str(row.get("id") or ""),
            partner_id=str(row.get("partner_id") or ""),
            order_id=str(row.get("order_id") or ""),
            event_type=str(row.get("event_type") or ""),
            status=str(row.get("status") or ""),
            attempt_count=int(row.get("attempt_count") or 0),
            max_attempts=int(row.get("max_attempts") or 0),
            next_retry_at=(_to_iso_utc(row.get("next_retry_at")) if row.get("next_retry_at") else None),
            delivered_at=(_to_iso_utc(row.get("delivered_at")) if row.get("delivered_at") else None),
            created_at=_to_iso_utc(row.get("created_at")),
        )
        for row in rows
    ]
    return OrderEventOutboxListOut(ok=True, total=total, limit=limit, offset=offset, items=items)


@router.post("/{order_id}/partner-events/retry", response_model=OrderEventOutboxReplayOut)
def retry_order_partner_event(
    order_id: str,
    outbox_id: str | None = Query(default=None),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    _ = user
    normalized_order_id = str(order_id).strip()
    normalized_outbox_id = str(outbox_id or "").strip()
    if normalized_outbox_id:
        row = db.execute(
            text(
                """
                SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
                FROM partner_order_events_outbox
                WHERE id = :id AND order_id = :order_id
                """
            ),
            {"id": normalized_outbox_id, "order_id": normalized_order_id},
        ).mappings().first()
    else:
        row = db.execute(
            text(
                """
                SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
                FROM partner_order_events_outbox
                WHERE order_id = :order_id
                  AND status IN ('FAILED','DEAD_LETTER','SKIPPED')
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """
            ),
            {"order_id": normalized_order_id},
        ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=404,
            detail={"type": "OUTBOX_ITEM_NOT_FOUND", "message": "Nenhum evento elegível encontrado para retry neste pedido."},
        )
    previous_status = str(row.get("status") or "").upper()
    replayed = False
    reason: str | None = None
    row_id = str(row.get("id") or "")
    if previous_status == "DELIVERED" and not force:
        reason = "ITEM_ALREADY_DELIVERED_USE_FORCE"
    else:
        db.execute(
            text(
                """
                UPDATE partner_order_events_outbox
                SET status = 'PENDING',
                    attempt_count = 0,
                    next_retry_at = NOW(),
                    last_error = NULL,
                    updated_at = NOW()
                WHERE id = :id
                """
            ),
            {"id": row_id},
        )
        db.commit()
        replayed = True
    latest = db.execute(
        text(
            """
            SELECT id, partner_id, order_id, event_type, status, attempt_count, max_attempts, next_retry_at, delivered_at, created_at
            FROM partner_order_events_outbox
            WHERE id = :id
            """
        ),
        {"id": row_id},
    ).mappings().first()
    item = OrderEventOutboxItemOut(
        id=str(latest.get("id") or ""),
        partner_id=str(latest.get("partner_id") or ""),
        order_id=str(latest.get("order_id") or ""),
        event_type=str(latest.get("event_type") or ""),
        status=str(latest.get("status") or ""),
        attempt_count=int(latest.get("attempt_count") or 0),
        max_attempts=int(latest.get("max_attempts") or 0),
        next_retry_at=(_to_iso_utc(latest.get("next_retry_at")) if latest.get("next_retry_at") else None),
        delivered_at=(_to_iso_utc(latest.get("delivered_at")) if latest.get("delivered_at") else None),
        created_at=_to_iso_utc(latest.get("created_at")),
    )
    return OrderEventOutboxReplayOut(ok=True, replayed=replayed, reason=reason, item=item)

