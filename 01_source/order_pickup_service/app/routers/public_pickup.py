# 01_source/order_pickup_service/app/routers/public_pickup.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user
from app.core.db import get_db
from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup
from app.models.pickup_token import PickupToken
from app.models.user import User
from app.schemas.public_pickup import PublicPickupOut
from app.services.pickup_qr_service import build_public_pickup_qr_value

router = APIRouter(prefix="/public/orders", tags=["public-pickup"])


def _mask_manual_code(token_id: str) -> str:
    return f"token:{token_id[-6:]}"


@router.get("/{order_id}/pickup", response_model=PublicPickupOut)
def get_public_pickup(
    order_id: str,
    current_user: User = Depends(get_current_public_user),
    db: Session = Depends(get_db),
):
    # 1. ORDER
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .filter(Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="order_not_found")

    if order.status not in {
        OrderStatus.PAID_PENDING_PICKUP,
        OrderStatus.PICKED_UP,
    }:
        raise HTTPException(status_code=409, detail="pickup_not_available_for_order_status")

    # 2. PICKUP (AQUI ESTAVA FALTANDO)
    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc())
        .first()
    )

    if not pickup:
        raise HTTPException(status_code=404, detail="pickup_not_found")

    # 3. TOKEN (AGORA CORRETO)
    token = (
        db.query(PickupToken)
        .filter(PickupToken.pickup_id == pickup.id)
        .order_by(PickupToken.expires_at.desc(), PickupToken.id.desc())
        .first()
    )

    if not token:
        raise HTTPException(status_code=404, detail="pickup_token_not_found")

    expires_at_iso = token.expires_at.isoformat() if token.expires_at else None

    qr_value = build_public_pickup_qr_value(
        order_id=order.id,
        token_id=token.id,
        expires_at_iso=expires_at_iso,
    )

    return PublicPickupOut(
        order_id=order.id,
        status=order.status.value,
        expires_at=expires_at_iso,
        token_id=token.id,
        qr_value=qr_value,
        manual_code_masked=_mask_manual_code(token.id),
    )