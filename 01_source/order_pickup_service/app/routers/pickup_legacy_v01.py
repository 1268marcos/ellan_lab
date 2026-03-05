# O que mudou (em relação ao seu)
# ✅ Removeu a criação de PickupToken de 10 minutos no QR.
# Agora o QR usa somente token criado no payment-confirm.
# ✅ redeem-manual agora espera código 6 dígitos, não pk_....
# ✅ redeem valida ctr atual ou anterior (tolerância).
# Você pode apagar (ou deixar de usar) o endpoint 
# legado /orders/{order_id}/pickup-token. Eu removi aqui 
# de propósito para impedir que o sistema crie tokens 
# paralelos e confunda o fluxo. Se você quiser manter 
# por compatibilidade, eu te devolvo uma versão com ele 
# mas gerando manual_code no mesmo formato 6 dígitos, sem TTL 10 min.

import os
import hmac
import hashlib
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.auth_dev import get_current_user_or_dev

from app.models.order import Order, OrderChannel, OrderStatus
from app.models.allocation import Allocation, AllocationState
from app.models.pickup_token import PickupToken

from app.schemas.pickup import (
    QrPayloadV1,
    PickupQrOut,
    PickupViewOut,
    TotemRedeemIn,
    TotemRedeemManualIn,
    TotemRedeemOut,
)

from app.services import backend_client

router = APIRouter(tags=["pickup"])

QR_ROTATE_SEC = int(os.getenv("QR_ROTATE_SEC", "600"))  # 10 min
PICKUP_QR_SECRET = os.getenv("PICKUP_QR_SECRET", "dev-secret-change-me").encode("utf-8")


# -----------------------------
# helpers
# -----------------------------

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

def _epoch(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())

def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _ensure_pickup_window(order: Order) -> None:
    now = _utcnow()
    if not order.pickup_deadline_at:
        raise HTTPException(status_code=409, detail="pickup window not set")
    deadline = order.pickup_deadline_at
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    if now > deadline:
        raise HTTPException(status_code=409, detail="pickup window expired")

def _issued_at_for_ctr(order: Order) -> datetime:
    """
    Base para ctr (rotação 10 min):
    - ideal: order.paid_at
    - fallback: pickup_deadline_at - 2h (se paid_at não existir)
    """
    if getattr(order, "paid_at", None):
        dt = order.paid_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    # fallback seguro
    if order.pickup_deadline_at:
        dl = order.pickup_deadline_at
        if dl.tzinfo is None:
            dl = dl.replace(tzinfo=timezone.utc)
        return dl - timedelta(hours=2)

    return _utcnow()

def _calc_ctr(issued_at: datetime, rotate_sec: int) -> int:
    now = _utcnow()
    delta = (now - issued_at).total_seconds()
    if delta < 0:
        delta = 0
    return int(delta // rotate_sec)

def _refresh_in_sec(issued_at: datetime, rotate_sec: int) -> int:
    now = _utcnow()
    elapsed = int((now - issued_at).total_seconds())
    if elapsed < 0:
        elapsed = 0
    into = elapsed % rotate_sec
    return max(0, rotate_sec - into)

def _sign_qr(*, pickup_id: str, token_id: str, ctr: int, exp: int) -> str:
    msg = f"{pickup_id}|{token_id}|{ctr}|{exp}".encode("utf-8")
    return hmac.new(PICKUP_QR_SECRET, msg, hashlib.sha256).hexdigest()

def _verify_qr(*, pickup_id: str, token_id: str, ctr: int, exp: int, sig: str) -> bool:
    expected = _sign_qr(pickup_id=pickup_id, token_id=token_id, ctr=ctr, exp=exp)
    return hmac.compare_digest(expected, sig)

def _get_active_token(db: Session, *, order_id: str) -> PickupToken:
    """
    Opção A (ponteiro):
    token já foi criado no /internal/.../payment-confirm e expira no deadline (2h).
    Aqui só buscamos o token ativo.
    """
    now = _utcnow()
    tok = (
        db.query(PickupToken)
        .filter(
            PickupToken.order_id == order_id,
            PickupToken.used_at.is_(None),
            PickupToken.expires_at > now.replace(tzinfo=None),
        )
        .order_by(PickupToken.expires_at.desc())
        .first()
    )
    if not tok:
        raise HTTPException(status_code=404, detail="pickup token not found (payment-confirm not done?)")
    return tok


# -----------------------------
# Client: ver pickup (para UI "Meus pedidos -> Retirada")
# -----------------------------
@router.get("/me/pickups/{pickup_id}", response_model=PickupViewOut)
def me_pickup_view(pickup_id: str, db: Session = Depends(get_db), user=Depends(get_current_user_or_dev)):
    """
    MVP: pickup_id == order_id
    """
    order = (
        db.query(Order)
        .filter(
            Order.id == pickup_id,
            Order.user_id == user.id,
            Order.channel == OrderChannel.ONLINE,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="pickup/order not found")

    # status do pickup baseado no order
    if order.status == OrderStatus.PAID_PENDING_PICKUP:
        status = "ACTIVE"
    elif order.status == OrderStatus.PICKED_UP:
        status = "REDEEMED"
    elif order.status == OrderStatus.EXPIRED:
        status = "EXPIRED"
    else:
        # ainda não pago
        status = "CANCELLED"

    expires_at = order.pickup_deadline_at
    if not expires_at:
        # ainda não confirmaram pagamento
        # devolve expires_at como agora para não quebrar schema; UI trata status
        expires_at = _utcnow()

    # opcional: expor token_id ativo (referência)
    token_id = None
    if order.status == OrderStatus.PAID_PENDING_PICKUP and order.pickup_deadline_at:
        try:
            tok = _get_active_token(db, order_id=order.id)
            token_id = tok.id
        except Exception:
            token_id = None

    return PickupViewOut(
        pickup_id=order.id,
        order_id=order.id,
        region=order.region,
        status=status,  # type: ignore
        expires_at=expires_at.replace(tzinfo=timezone.utc) if expires_at.tzinfo is None else expires_at,
        qr_rotate_sec=QR_ROTATE_SEC,
        token_id=token_id,
        manual_code_hint=None,  # se quiser, podemos retornar "***123" no futuro
    )


# -----------------------------
# Client: obter QR atual (rotativo)
# -----------------------------
@router.post("/me/pickups/{pickup_id}/qr", response_model=PickupQrOut)
def me_pickup_qr(pickup_id: str, db: Session = Depends(get_db), user=Depends(get_current_user_or_dev)):
    """
    Opção A (ponteiro):
    - NÃO cria token aqui.
    - Busca token_id ativo já criado no payment-confirm.
    - Gera QR rotativo com ctr.
    """
    order = (
        db.query(Order)
        .filter(
            Order.id == pickup_id,
            Order.user_id == user.id,
            Order.channel == OrderChannel.ONLINE,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="pickup/order not found")

    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    _ensure_pickup_window(order)

    tok = _get_active_token(db, order_id=order.id)

    # exp total (deadline 2h)
    exp_dt = order.pickup_deadline_at
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
    exp_epoch = _epoch(exp_dt)

    issued_at = _issued_at_for_ctr(order)
    ctr = _calc_ctr(issued_at, QR_ROTATE_SEC)
    sig = _sign_qr(pickup_id=order.id, token_id=tok.id, ctr=ctr, exp=exp_epoch)

    qr = QrPayloadV1(
        pickup_id=order.id,
        token_id=tok.id,
        ctr=ctr,
        exp=exp_epoch,
        sig=sig,
    )

    return PickupQrOut(qr=qr, refresh_in_sec=_refresh_in_sec(issued_at, QR_ROTATE_SEC))


# -----------------------------
# Totem: redeem via QR (contrato novo)
# -----------------------------
@router.post("/totem/pickups/redeem", response_model=TotemRedeemOut)
def totem_redeem(payload: TotemRedeemIn, db: Session = Depends(get_db)):
    """
    Valida:
    - exp (deadline 2h)
    - assinatura (sig)
    - token ativo (token_id existe e não usado)
    - ctr atual ou anterior (tolerância de virada)
    """
    now = _utcnow()
    qr = payload.qr

    # 1) expiração total (2h)
    if now.timestamp() > qr.exp:
        raise HTTPException(status_code=409, detail={"type": "PICKUP_EXPIRED", "message": "pickup window expired", "retryable": False})

    # 2) assinatura
    if not _verify_qr(pickup_id=qr.pickup_id, token_id=qr.token_id, ctr=qr.ctr, exp=qr.exp, sig=qr.sig):
        raise HTTPException(status_code=401, detail={"type": "INVALID_QR_SIGNATURE", "message": "invalid QR signature", "retryable": False})

    # 3) token ativo
    tok = (
        db.query(PickupToken)
        .filter(
            PickupToken.id == qr.token_id,
            PickupToken.used_at.is_(None),
            PickupToken.expires_at > now.replace(tzinfo=None),
        )
        .first()
    )
    if not tok or tok.order_id != qr.pickup_id:
        raise HTTPException(status_code=401, detail={"type": "INVALID_OR_EXPIRED_TOKEN", "message": "invalid or expired token", "retryable": False})

    # 4) order e região
    order = db.query(Order).filter(Order.id == tok.order_id, Order.channel == OrderChannel.ONLINE).first()
    if not order:
        raise HTTPException(status_code=404, detail={"type": "ORDER_NOT_FOUND", "message": "order not found", "retryable": False})

    if getattr(order, "region", None) != payload.region:
        raise HTTPException(status_code=403, detail={"type": "WRONG_REGION", "message": "QR not valid for this region", "retryable": False})

    _ensure_pickup_window(order)

    # 5) tolerância de ctr (atual ou anterior)
    issued_at = _issued_at_for_ctr(order)
    current_ctr = _calc_ctr(issued_at, QR_ROTATE_SEC)
    if qr.ctr not in (current_ctr, max(0, current_ctr - 1)):
        raise HTTPException(status_code=401, detail={"type": "STALE_QR", "message": "QR is stale; refresh and try again", "retryable": True})

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail={"type": "ALLOCATION_NOT_FOUND", "message": "allocation not found", "retryable": True})

    # 6) consome token (1 uso)
    tok.used_at = now.replace(tzinfo=None)

    # 7) abre e ilumina
    backend_client.locker_light_on(order.region, allocation.slot)
    backend_client.locker_open(order.region, allocation.slot)
    backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    # 8) marca estados (MVP: direto)
    order.status = OrderStatus.PICKED_UP
    allocation.state = AllocationState.OPENED_FOR_PICKUP

    db.commit()

    exp_dt = order.pickup_deadline_at
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)

    return TotemRedeemOut(
        pickup_id=order.id,
        order_id=order.id,
        slot=allocation.slot,
        expires_at=exp_dt,
    )


# -----------------------------
# Totem: redeem manual (fallback sem QR)
# -----------------------------
@router.post("/totem/pickups/redeem-manual", response_model=TotemRedeemOut)
def totem_redeem_manual(payload: TotemRedeemManualIn, db: Session = Depends(get_db)):
    """
    Fallback sem QR:
    - manual_code = 6 dígitos que o cliente vê no site/app (gerado no payment-confirm)
    - no DB guardamos apenas hash (token_hash)
    """
    now = _utcnow()
    token_hash = _sha256(payload.manual_code)

    tok = (
        db.query(PickupToken)
        .filter(
            PickupToken.token_hash == token_hash,
            PickupToken.used_at.is_(None),
            PickupToken.expires_at > now.replace(tzinfo=None),
        )
        .first()
    )
    if not tok:
        raise HTTPException(status_code=401, detail={"type": "INVALID_OR_EXPIRED_CODE", "message": "invalid or expired manual code", "retryable": False})

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

    exp_dt = order.pickup_deadline_at
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)

    return TotemRedeemOut(
        pickup_id=order.id,
        order_id=order.id,
        slot=allocation.slot,
        expires_at=exp_dt,
    )