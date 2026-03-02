# QR: /orders/{id}/pickup-token + /pickup/redeem
import uuid
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth_dep import get_current_user
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.models.pickup_token import PickupToken
from app.schemas.pickup import RedeemIn
from app.services import backend_client

router = APIRouter(tags=["pickup"])

TOKEN_TTL_SEC = 600  # 10 min

def _hash_token(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()

@router.post("/orders/{order_id}/pickup-token")
def generate_pickup_token(order_id: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id,
        Order.channel == OrderChannel.ONLINE
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    now = datetime.now(timezone.utc)
    if not order.pickup_deadline_at or now > order.pickup_deadline_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=409, detail="pickup window expired")

    raw = "pk_" + uuid.uuid4().hex
    tok = PickupToken(
        id=str(uuid.uuid4()),
        order_id=order.id,
        token_hash=_hash_token(raw),
        expires_at=(now + timedelta(seconds=TOKEN_TTL_SEC)).replace(tzinfo=None),
        used_at=None
    )
    db.add(tok)
    db.commit()

    return {
        "order_id": order.id,
        "pickup_token": raw,
        "expires_in_sec": TOKEN_TTL_SEC,
        "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None
    }

@router.post("/pickup/redeem")
def redeem_pickup(payload: RedeemIn, db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    token_hash = _hash_token(payload.pickup_token)

    tok = db.query(PickupToken).filter(
        PickupToken.token_hash == token_hash,
        PickupToken.used_at.is_(None),
        PickupToken.expires_at > now.replace(tzinfo=None)
    ).first()
    if not tok:
        raise HTTPException(status_code=401, detail="invalid or expired pickup token")

    order = db.query(Order).filter(Order.id == tok.order_id, Order.channel == OrderChannel.ONLINE).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    # valida totem/region
    if order.region != payload.region or order.totem_id != payload.totem_id:
        raise HTTPException(status_code=403, detail="token not valid for this totem/region")

    # valida janela 2h
    if not order.pickup_deadline_at or now > order.pickup_deadline_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=409, detail="pickup window expired")

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail="allocation not found")

    # consome token
    tok.used_at = now.replace(tzinfo=None)

    # abre e ilumina
    backend_client.locker_light_on(order.region, allocation.slot)
    backend_client.locker_open(order.region, allocation.slot)
    backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    #⚠️ Mas como você ainda vai decidir (A) ou (B) para o “cinza”, eu recomendo por enquanto deixar somente no job de expiração e depois ajustamos conforme tua regra.

    # opcional: marcar status como PICKED_UP (ou aguardar sensor futuro)
    order.status = OrderStatus.PICKED_UP
    allocation.state = AllocationState.OPENED_FOR_PICKUP

    db.commit()

    return {
        "ok": True,
        "order_id": order.id,
        "slot": allocation.slot,
        "message": f"Espere a porta abrir e pegue o seu bolo na gaveta {allocation.slot}"
    }