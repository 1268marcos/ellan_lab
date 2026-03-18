# 01_source/order_pickup_service/app/routers/public_orders.py
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user
from app.core.db import get_db
from app.models.order import Order
from app.models.user import User

router = APIRouter(prefix="/public/orders", tags=["public-orders"])


def _dt_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _serialize_order(order: Order) -> dict:
    return {
        "id": order.id,
        "user_id": order.user_id,
        "channel": order.channel,
        "region": order.region,
        "totem_id": order.totem_id,
        "sku_id": order.sku_id,
        "amount_cents": order.amount_cents,
        "status": order.status,
        "gateway_transaction_id": order.gateway_transaction_id,
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "card_type": order.card_type,
        "payment_updated_at": _dt_iso(order.payment_updated_at),
        "paid_at": _dt_iso(order.paid_at),
        "pickup_deadline_at": _dt_iso(order.pickup_deadline_at),
        "picked_up_at": _dt_iso(order.picked_up_at),
        "guest_session_id": order.guest_session_id,
        "receipt_email": order.receipt_email,
        "receipt_phone": order.receipt_phone,
        "consent_marketing": order.consent_marketing,
        "guest_phone": order.guest_phone,
        "guest_email": order.guest_email,
        "created_at": _dt_iso(order.created_at),
        "updated_at": _dt_iso(order.updated_at),
    }


@router.get("")
def list_my_public_orders(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_public_user),
    db: Session = Depends(get_db),
):
    query = db.query(Order).filter(Order.user_id == current_user.id)

    if status:
        query = query.filter(Order.status == status)

    total = query.count()

    items = (
        query.order_by(Order.created_at.desc(), Order.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": [_serialize_order(order) for order in items],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
        "filters": {
            "status": status,
        },
    }


@router.get("/{order_id}")
def get_my_public_order(
    order_id: str,
    current_user: User = Depends(get_current_public_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .filter(Order.user_id == current_user.id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")

    return _serialize_order(order)