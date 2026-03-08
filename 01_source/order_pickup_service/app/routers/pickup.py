import os
import hmac
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
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

# localizado em /02_docker/.env
QR_ROTATE_SEC = int(os.getenv("QR_ROTATE_SEC", "600"))  # 10 min
PICKUP_QR_SECRET = os.getenv("PICKUP_QR_SECRET", "dev-secreto-mudar").encode("utf-8")

# localizado em /01_source/order_pickup_service/.env
MANUAL_REDEEM_MAX_ATTEMPTS = int(os.getenv("MANUAL_REDEEM_MAX_ATTEMPTS", "5"))
MANUAL_REDEEM_WINDOW_SEC = int(os.getenv("MANUAL_REDEEM_WINDOW_SEC", "120"))
MANUAL_REDEEM_BLOCK_SEC = int(os.getenv("MANUAL_REDEEM_BLOCK_SEC", "300"))

# Estrutura simples em memória:
# {
#   "key": {
#       "fails": [epoch1, epoch2, ...],
#       "blocked_until": epoch_or_none,
#   }
# }
_manual_redeem_attempts = {}


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

def _client_ip(request: Request) -> str:
    xfwd = request.headers.get("x-forwarded-for")
    if xfwd:
        return xfwd.split(",")[0].strip()
    if getattr(request, "client", None) and request.client:
        return request.client.host or "unknown"
    return "unknown"

# def _manual_redeem_key(region: str, request: Request) -> str:
#     return f"{region}:{_client_ip(request)}"
def _manual_redeem_key(region: str, manual_code: str, request: Request) -> str:
    return f"{region}:{manual_code}:{_client_ip(request)}"

# def _check_manual_redeem_block(region: str, request: Request) -> None:
#     key = _manual_redeem_key(region, request)
def _check_manual_redeem_block(region: str, manual_code: str, request: Request) -> None:
    key = _manual_redeem_key(region, manual_code, request)
    now = int(_utcnow().timestamp())
    entry = _manual_redeem_attempts.get(key)

    if not entry:
        return

    blocked_until = entry.get("blocked_until")
    if blocked_until and now < blocked_until:
        retry_after = blocked_until - now
        raise HTTPException(
            status_code=429,
            detail={
                "type": "TOO_MANY_MANUAL_CODE_ATTEMPTS",
                "message": "too many invalid manual code attempts; try again later",
                "retryable": True,
                "retry_after_sec": retry_after,
            },
        )

# def _register_manual_redeem_failure(region: str, request: Request) -> None:
#     key = _manual_redeem_key(region, request)
def _register_manual_redeem_failure(region: str, manual_code: str, request: Request) -> None:
    key = _manual_redeem_key(region, manual_code, request)
    now = int(_utcnow().timestamp())
    entry = _manual_redeem_attempts.get(key, {"fails": [], "blocked_until": None})

    # mantém só falhas dentro da janela
    fails = [ts for ts in entry.get("fails", []) if now - ts <= MANUAL_REDEEM_WINDOW_SEC]
    fails.append(now)

    blocked_until = None
    if len(fails) >= MANUAL_REDEEM_MAX_ATTEMPTS:
        blocked_until = now + MANUAL_REDEEM_BLOCK_SEC

    _manual_redeem_attempts[key] = {
        "fails": fails,
        "blocked_until": blocked_until,
    }

# def _clear_manual_redeem_failures(region: str, request: Request) -> None:
#     key = _manual_redeem_key(region, request)
def _clear_manual_redeem_failures(region: str, manual_code: str, request: Request) -> None:
    key = _manual_redeem_key(region, manual_code, request)
    if key in _manual_redeem_attempts:
        del _manual_redeem_attempts[key]

def _generate_manual_code() -> str:
    # 6 dígitos
    return f"{uuid.uuid4().int % 1_000_000:06d}"

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
    Base para ctr:
    - ideal: order.paid_at
    - fallback: pickup_deadline_at - 2h
    """
    if getattr(order, "paid_at", None):
        dt = order.paid_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

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
    Token ativo (ponteiro) para este pedido.
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
# LEGADO: /orders/{order_id}/pickup-token
# -----------------------------
@router.post("/orders/{order_id}/pickup-token")
def legacy_generate_manual_code(order_id: str, db: Session = Depends(get_db), user=Depends(get_current_user_or_dev)):
    """
    Mantido por compatibilidade.
    Agora ele gera um MANUAL_CODE de 6 dígitos (fallback sem QR), válido até pickup_deadline_at (2h).

    Para evitar "tokens paralelos":
    - ao gerar um novo código, invalidamos todos os tokens antigos não usados do pedido (used_at=now).
    Assim sempre existe no máximo 1 token ativo por order.

    Retorna:
      - manual_code (para o cliente digitar no totem se precisar)
      - token_id (ponteiro, útil para debug)
      - expires_at (deadline 2h do pedido)
    """
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == user.id,
            Order.channel == OrderChannel.ONLINE,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    _ensure_pickup_window(order)

    now = _utcnow()

    # invalida tokens anteriores (evita paralelos)
    db.query(PickupToken).filter(
        PickupToken.order_id == order.id,
        PickupToken.used_at.is_(None),
        PickupToken.expires_at > now.replace(tzinfo=None),
    ).update({"used_at": now.replace(tzinfo=None)}, synchronize_session=False)

    # gera novo código válido até o deadline do pedido
    manual_code = _generate_manual_code()

    deadline = order.pickup_deadline_at
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    tok = PickupToken(
        id=str(uuid.uuid4()),
        order_id=order.id,
        token_hash=_sha256(manual_code),
        expires_at=deadline.replace(tzinfo=None),  # DB naive
        used_at=None,
    )
    db.add(tok)
    db.commit()

    return {
        "ok": True,
        "order_id": order.id,
        "pickup_id": order.id,  # MVP
        "token_id": tok.id,
        "manual_code": manual_code,
        "expires_at": deadline.isoformat(),
        "note": "Gerar novo código invalida códigos anteriores.",
    }


# -----------------------------
# Client: ver pickup (Meus pedidos -> Retirada)
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

    if order.status == OrderStatus.PAID_PENDING_PICKUP:
        status = "ACTIVE"
    elif order.status == OrderStatus.PICKED_UP:
        status = "REDEEMED"
    elif order.status == OrderStatus.EXPIRED:
        status = "EXPIRED"
    else:
        status = "CANCELLED"

    expires_at = order.pickup_deadline_at or _utcnow()

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
        manual_code_hint=None,
    )


# -----------------------------
# Client: obter QR atual (rotativo) - Opção A
# -----------------------------
@router.post("/me/pickups/{pickup_id}/qr", response_model=PickupQrOut)
def me_pickup_qr(pickup_id: str, db: Session = Depends(get_db), user=Depends(get_current_user_or_dev)):
    """
    Opção A:
    - NÃO cria token aqui.
    - Busca token_id ativo já criado no payment-confirm (ou regenerado via endpoint legado).
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
# Totem: redeem via QR
# -----------------------------
@router.post("/totem/pickups/redeem", response_model=TotemRedeemOut)
def totem_redeem(payload: TotemRedeemIn, db: Session = Depends(get_db)):
    now = _utcnow()
    qr = payload.qr

    if now.timestamp() > qr.exp:
        raise HTTPException(status_code=409, detail={"type": "PICKUP_EXPIRED", "message": "pickup window expired", "retryable": False})

    if not _verify_qr(pickup_id=qr.pickup_id, token_id=qr.token_id, ctr=qr.ctr, exp=qr.exp, sig=qr.sig):
        raise HTTPException(status_code=401, detail={"type": "INVALID_QR_SIGNATURE", "message": "invalid QR signature", "retryable": False})

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

    order = db.query(Order).filter(Order.id == tok.order_id, Order.channel == OrderChannel.ONLINE).first()
    if not order:
        raise HTTPException(status_code=404, detail={"type": "ORDER_NOT_FOUND", "message": "order not found", "retryable": False})

    if getattr(order, "region", None) != payload.region:
        raise HTTPException(status_code=403, detail={"type": "WRONG_REGION", "message": "QR not valid for this region", "retryable": False})

    _ensure_pickup_window(order)

    # tolerância ctr: atual ou anterior
    issued_at = _issued_at_for_ctr(order)
    current_ctr = _calc_ctr(issued_at, QR_ROTATE_SEC)
    if qr.ctr not in (current_ctr, max(0, current_ctr - 1)):
        raise HTTPException(status_code=401, detail={"type": "STALE_QR", "message": "QR is stale; refresh and try again", "retryable": True})

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail={"type": "ALLOCATION_NOT_FOUND", "message": "allocation not found", "retryable": True})

    tok.used_at = now.replace(tzinfo=None)

    backend_client.locker_light_on(order.region, allocation.slot)
    backend_client.locker_open(order.region, allocation.slot)
    backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    # order.status = OrderStatus.PICKED_UP
    order.mark_as_picked_up()
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
def totem_redeem_manual(payload: TotemRedeemManualIn, request: Request, db: Session = Depends(get_db)):
    now = _utcnow()
    token_hash = _sha256(payload.manual_code)

    # _check_manual_redeem_block(payload.region, request)
    _check_manual_redeem_block(payload.region, payload.manual_code, request)

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
        # _register_manual_redeem_failure(payload.region, request)
        _register_manual_redeem_failure(payload.region, payload.manual_code, request)
        raise HTTPException(
            status_code=401,
            detail={
                "type": "INVALID_OR_EXPIRED_CODE",
                "message": "invalid or expired manual code",
                "retryable": False,
            },
        )

    order = db.query(Order).filter(Order.id == tok.order_id, Order.channel == OrderChannel.ONLINE).first()
    if not order:
        raise HTTPException(status_code=404, detail={"type": "ORDER_NOT_FOUND", "message": "order not found", "retryable": False})

    if getattr(order, "region", None) != payload.region:
        # _register_manual_redeem_failure(payload.region, request)
        _register_manual_redeem_failure(payload.region, payload.manual_code, request)
        raise HTTPException(
            status_code=403,
            detail={
                "type": "WRONG_REGION",
                "message": "code not valid for this region",
                "retryable": False,
            },
        )

    _ensure_pickup_window(order)

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail={"type": "ALLOCATION_NOT_FOUND", "message": "allocation not found", "retryable": True})

    tok.used_at = now.replace(tzinfo=None)

    backend_client.locker_light_on(order.region, allocation.slot)
    backend_client.locker_open(order.region, allocation.slot)
    backend_client.locker_set_state(order.region, allocation.slot, "OUT_OF_STOCK")

    # order.status = OrderStatus.PICKED_UP
    order.mark_as_picked_up()
    allocation.state = AllocationState.OPENED_FOR_PICKUP

    db.commit()

    exp_dt = order.pickup_deadline_at
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)

    # _clear_manual_redeem_failures(payload.region, request)
    _clear_manual_redeem_failures(payload.region, payload.manual_code, request)

    return TotemRedeemOut(
        pickup_id=order.id,
        order_id=order.id,
        slot=allocation.slot,
        expires_at=exp_dt,
    )