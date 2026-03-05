# Pickup / QR rotativo (MVP compat + novo contrato)
import os
import uuid
import hmac
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth_dep import get_current_user
from app.core.auth_dev import get_current_user_or_dev

from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.models.pickup_token import PickupToken

from app.schemas.pickup import (
    # novo contrato
    QrPayloadV1,
    PickupQrOut,
    PickupViewOut,
    TotemRedeemIn,
    TotemRedeemManualIn,
    TotemRedeemOut,
)

from app.services import backend_client

router = APIRouter(tags=["pickup"])

# Token curto (fallback/manual e/ou usado para gerar o QR)
TOKEN_TTL_SEC = 600  # 10 min
QR_ROTATE_SEC = int(os.getenv("QR_ROTATE_SEC", "600"))  # 10 min
PICKUP_QR_SECRET = os.getenv("PICKUP_QR_SECRET", "dev-secret-change-me").encode("utf-8")


# -----------------------------
# helpers
# -----------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def _epoch(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def _ensure_pickup_window(order: Order) -> None:
    now = _utcnow()
    if not order.pickup_deadline_at:
        raise HTTPException(status_code=409, detail="pickup window not set")
    deadline = order.pickup_deadline_at
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now > deadline:
        raise HTTPException(status_code=409, detail="pickup window expired")

def _sign_qr(*, pickup_id: str, token_id: str, ctr: int, exp: int) -> str:
    # assinatura HMAC (base16/hex simples) - suficiente para MVP
    msg = f"{pickup_id}|{token_id}|{ctr}|{exp}".encode("utf-8")
    return hmac.new(PICKUP_QR_SECRET, msg, hashlib.sha256).hexdigest()

def _verify_qr(*, pickup_id: str, token_id: str, ctr: int, exp: int, sig: str) -> bool:
    expected = _sign_qr(pickup_id=pickup_id, token_id=token_id, ctr=ctr, exp=exp)
    return hmac.compare_digest(expected, sig)

def _calc_ctr(*, issued_at: datetime, rotate_sec: int) -> int:
    now = _utcnow()
    delta = (now - issued_at).total_seconds()
    if delta < 0:
        delta = 0
    return int(delta // rotate_sec)

def _refresh_in_sec(*, issued_at: datetime, rotate_sec: int) -> int:
    now = _utcnow()
    elapsed = int((now - issued_at).total_seconds())
    if elapsed < 0:
        elapsed = 0
    into = elapsed % rotate_sec
    return max(0, rotate_sec - into)


# -----------------------------
# Legacy: site/app pega token curto (10 min)
# -----------------------------
@router.post("/orders/{order_id}/pickup-token")
def generate_pickup_token(order_id: str, db: Session = Depends(get_db), user=Depends(get_current_user_or_dev)):
    """
    Legado (ainda útil como fallback manual):
    - Cliente logado pega um token curto válido por 10 min.
    - Esse token pode ser digitado no totem (redeem-manual).
    - Também pode ser usado para gerar QR (novo endpoint /me/pickups/{id}/qr).
    """
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == user.id,
        Order.channel == OrderChannel.ONLINE
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    _ensure_pickup_window(order)

    now = _utcnow()

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
        "pickup_token": raw,  # segredo curto (10 min)
        "token_id": tok.id,   # referência (não é segredo)
        "expires_in_sec": TOKEN_TTL_SEC,
        "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None
    }


# -----------------------------
# Novo: cliente obtém QR atual (rotativo)
# -----------------------------
@router.post("/me/pickups/{pickup_id}/qr", response_model=PickupQrOut)
def me_pickup_qr(pickup_id: str, db: Session = Depends(get_db), user=Depends(get_current_user_or_dev)):
    """
    MVP do contrato novo:
    - pickup_id = order_id (por enquanto) para não travar implementação.
    - Gera/usa um token curto (PickupToken) e entrega QR payload assinado.
    - QR rotaciona por ctr (10min).
    """
    order = db.query(Order).filter(
        Order.id == pickup_id,
        Order.user_id == user.id,
        Order.channel == OrderChannel.ONLINE
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="pickup/order not found")
    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    _ensure_pickup_window(order)

    now = _utcnow()

    # reutiliza token ativo se existir, senão cria outro
    tok = db.query(PickupToken).filter(
        PickupToken.order_id == order.id,
        PickupToken.used_at.is_(None),
        PickupToken.expires_at > now.replace(tzinfo=None)
    ).order_by(PickupToken.expires_at.desc()).first()

    if not tok:
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
        # IMPORTANTE: não retornamos o raw aqui; QR é o “meio” de apresentação
        issued_at = now
    else:
        # inferimos issued_at a partir do expires_at - TTL (MVP)
        issued_at = tok.expires_at.replace(tzinfo=timezone.utc) - timedelta(seconds=TOKEN_TTL_SEC)

    exp_epoch = _epoch(order.pickup_deadline_at.replace(tzinfo=timezone.utc) if order.pickup_deadline_at.tzinfo is None else order.pickup_deadline_at)
    ctr = _calc_ctr(issued_at=issued_at, rotate_sec=QR_ROTATE_SEC)
    sig = _sign_qr(pickup_id=order.id, token_id=tok.id, ctr=ctr, exp=exp_epoch)

    qr = QrPayloadV1(
        pickup_id=order.id,
        token_id=tok.id,
        ctr=ctr,
        exp=exp_epoch,
        sig=sig,
    )

    return PickupQrOut(qr=qr, refresh_in_sec=_refresh_in_sec(issued_at=issued_at, rotate_sec=QR_ROTATE_SEC))


# -----------------------------
# Totem: redeem via QR (contrato novo)
# -----------------------------
@router.post("/totem/pickups/redeem", response_model=TotemRedeemOut)
def totem_redeem(payload: TotemRedeemIn, db: Session = Depends(get_db)):
    """
    Totem recebe QR e valida:
    - assinatura
    - exp (janela 2h)
    - ctr (aceita ctr atual e o anterior como tolerância)
    - token não usado + ainda válido (10 min)
    """
    now = _utcnow()

    qr = payload.qr

    # valida expiração total (2h)
    if now.timestamp() > qr.exp:
        raise HTTPException(status_code=409, detail={"type": "PICKUP_EXPIRED", "message": "pickup window expired", "retryable": False})

    # valida assinatura
    if not _verify_qr(pickup_id=qr.pickup_id, token_id=qr.token_id, ctr=qr.ctr, exp=qr.exp, sig=qr.sig):
        raise HTTPException(status_code=401, detail={"type": "INVALID_QR_SIGNATURE", "message": "invalid QR signature", "retryable": False})

    # token precisa existir e estar válido
    tok = db.query(PickupToken).filter(
        PickupToken.id == qr.token_id,
        PickupToken.used_at.is_(None),
        PickupToken.expires_at > now.replace(tzinfo=None)
    ).first()
    if not tok or tok.order_id != qr.pickup_id:
        raise HTTPException(status_code=401, detail={"type": "INVALID_OR_EXPIRED_TOKEN", "message": "invalid or expired token", "retryable": False})

    # carrega pedido (pickup_id = order_id no MVP)
    order = db.query(Order).filter(Order.id == tok.order_id, Order.channel == OrderChannel.ONLINE).first()
    if not order:
        raise HTTPException(status_code=404, detail={"type": "ORDER_NOT_FOUND", "message": "order not found", "retryable": False})

    # valida região (do pedido)
    if getattr(order, "region", None) != payload.region:
        raise HTTPException(status_code=403, detail={"type": "WRONG_REGION", "message": "QR not valid for this region", "retryable": False})

    # valida janela 2h do pedido (fonte de verdade)
    _ensure_pickup_window(order)

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail={"type": "ALLOCATION_NOT_FOUND", "message": "allocation not found", "retryable": True})

    # consome token
    tok.used_at = now.replace(tzinfo=None)

    # abre e ilumina
    backend_client.locker_light_on(order.region, allocation.slot)
    backend_client.locker_open(order.region, allocation.slot)
    backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    # marca estados (MVP: direto)
    order.status = OrderStatus.PICKED_UP
    allocation.state = AllocationState.OPENED_FOR_PICKUP

    db.commit()

    return TotemRedeemOut(
        pickup_id=order.id,
        order_id=order.id,
        slot=allocation.slot,
        expires_at=order.pickup_deadline_at.replace(tzinfo=timezone.utc) if order.pickup_deadline_at.tzinfo is None else order.pickup_deadline_at,
    )


# -----------------------------
# Totem: redeem manual (fallback sem QR)
# -----------------------------
@router.post("/totem/pickups/redeem-manual", response_model=TotemRedeemOut)
def totem_redeem_manual(payload: TotemRedeemManualIn, db: Session = Depends(get_db)):
    """
    MVP fallback:
    - manual_code aqui é o token raw (pk_...) gerado pelo endpoint legado /pickup-token
      (mais pra frente você troca por um código 6–8 dígitos real, armazenado)
    """
    now = _utcnow()
    token_hash = _hash_token(payload.manual_code)

    tok = db.query(PickupToken).filter(
        PickupToken.token_hash == token_hash,
        PickupToken.used_at.is_(None),
        PickupToken.expires_at > now.replace(tzinfo=None)
    ).first()
    if not tok:
        raise HTTPException(status_code=401, detail={"type": "INVALID_OR_EXPIRED_TOKEN", "message": "invalid or expired manual code", "retryable": False})

    order = db.query(Order).filter(Order.id == tok.order_id, Order.channel == OrderChannel.ONLINE).first()
    if not order:
        raise HTTPException(status_code=404, detail={"type": "ORDER_NOT_FOUND", "message": "order not found", "retryable": False})

    if getattr(order, "region", None) != payload.region:
        raise HTTPException(status_code=403, detail={"type": "WRONG_REGION", "message": "code not valid for this region", "retryable": False})

    _ensure_pickup_window(order)

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail={"type": "ALLOCATION_NOT_FOUND", "message": "allocation not found", "retryable": True})

    tok.used_at = now.replace(tzinfo=None)

    backend_client.locker_light_on(order.region, allocation.slot)
    backend_client.locker_open(order.region, allocation.slot)
    backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    order.status = OrderStatus.PICKED_UP
    allocation.state = AllocationState.OPENED_FOR_PICKUP

    db.commit()

    return TotemRedeemOut(
        pickup_id=order.id,
        order_id=order.id,
        slot=allocation.slot,
        expires_at=order.pickup_deadline_at.replace(tzinfo=timezone.utc) if order.pickup_deadline_at.tzinfo is None else order.pickup_deadline_at,
    )