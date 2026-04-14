# 01_source/order_pickup_service/app/routers/pickup.py

from __future__ import annotations

import hashlib
import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dev import get_current_user_or_dev
from app.core.config import settings
from app.core.db import get_db
from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.pickup import (
    Pickup,
    PickupChannel,
    PickupLifecycleStage,
    PickupRedeemVia,
    PickupStatus,
)
from app.models.pickup_token import PickupToken
from app.schemas.pickup import (
    PickupQrOut,
    PickupViewOut,
    QrPayloadV1,
    QrPayloadV2,
    TotemRedeemIn,
    TotemRedeemManualIn,
    TotemRedeemOut,
)
from app.services import backend_client

from app.services.pickup_event_publisher import (
    publish_pickup_door_opened,
    publish_pickup_item_removed,
    publish_pickup_door_closed,
    publish_pickup_redeemed,
)

router = APIRouter(tags=["pickup"])
logger = logging.getLogger(__name__)

QR_ROTATE_SEC = settings.qr_rotate_sec
QR_PAYLOAD_VERSION = settings.pickup_qr_payload_version

APP_ENV = str(settings.app_env or settings.node_env or "dev").strip().lower()

_QR_SECRET_RAW = str(settings.pickup_qr_secret or "").strip()
_DEV_FALLBACK_QR_SECRET = "dev-secreto-mudar"

MANUAL_REDEEM_MAX_ATTEMPTS = settings.manual_redeem_max_attempts
MANUAL_REDEEM_WINDOW_SEC = settings.manual_redeem_window_sec
MANUAL_REDEEM_BLOCK_SEC = settings.manual_redeem_block_sec

_manual_redeem_attempts = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_naive() -> datetime:
    return _utcnow().replace(tzinfo=None)


def _epoch(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _normalize_region(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if normalized not in {"SP", "PT"}:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_REGION",
                "message": "region must be SP or PT",
                "retryable": False,
            },
        )
    return normalized


def _normalize_locker_id(value: str) -> str:
    normalized = str(value or "").strip().upper()
    if not normalized:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_LOCKER_ID",
                "message": "locker_id is required",
                "retryable": False,
            },
        )
    return normalized


def _get_qr_secret_bytes() -> bytes:
    secret = _QR_SECRET_RAW or _DEV_FALLBACK_QR_SECRET
    is_weak = (not _QR_SECRET_RAW) or (_QR_SECRET_RAW == _DEV_FALLBACK_QR_SECRET) or (len(secret) < 32)

    if APP_ENV in {"prod", "production"} and is_weak:
        raise RuntimeError(
            "PICKUP_QR_SECRET inseguro para produção. "
            "Configure segredo forte com pelo menos 32 caracteres."
        )

    if is_weak:
        logger.warning("pickup_qr_using_weak_or_default_secret_in_non_production")

    return secret.encode("utf-8")


def _client_ip(request: Request) -> str:
    xfwd = request.headers.get("x-forwarded-for")
    if xfwd:
        return xfwd.split(",")[0].strip()
    if getattr(request, "client", None) and request.client:
        return request.client.host or "unknown"
    return "unknown"


def _manual_redeem_key(region: str, manual_code: str, request: Request) -> str:
    return f"{region}:{manual_code}:{_client_ip(request)}"


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


def _register_manual_redeem_failure(region: str, manual_code: str, request: Request) -> None:
    key = _manual_redeem_key(region, manual_code, request)
    now = int(_utcnow().timestamp())
    entry = _manual_redeem_attempts.get(key, {"fails": [], "blocked_until": None})

    fails = [ts for ts in entry.get("fails", []) if now - ts <= MANUAL_REDEEM_WINDOW_SEC]
    fails.append(now)

    blocked_until = None
    if len(fails) >= MANUAL_REDEEM_MAX_ATTEMPTS:
        blocked_until = now + MANUAL_REDEEM_BLOCK_SEC

    _manual_redeem_attempts[key] = {
        "fails": fails,
        "blocked_until": blocked_until,
    }


def _clear_manual_redeem_failures(region: str, manual_code: str, request: Request) -> None:
    key = _manual_redeem_key(region, manual_code, request)
    if key in _manual_redeem_attempts:
        del _manual_redeem_attempts[key]


def _generate_manual_code() -> str:
    return f"{uuid.uuid4().int % 1_000_000:06d}"


def _ensure_pickup_window(pickup: Pickup) -> None:
    if pickup.channel == PickupChannel.KIOSK:
        return

    now = _utcnow()
    if not pickup.expires_at:
        raise HTTPException(status_code=409, detail="pickup window not set")

    deadline = pickup.expires_at
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    if now > deadline:
        raise HTTPException(status_code=409, detail="pickup window expired")


def _issued_at_for_ctr(order: Order) -> datetime:
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


def _sign_qr_v1(*, pickup_id: str, token_id: str, ctr: int, exp: int) -> str:
    msg = f"{pickup_id}|{token_id}|{ctr}|{exp}".encode("utf-8")
    return hmac.new(_get_qr_secret_bytes(), msg, hashlib.sha256).hexdigest()


def _sign_qr_v2(
    *,
    pickup_id: str,
    token_id: str,
    locker_id: str,
    region: str,
    ctr: int,
    exp: int,
) -> str:
    normalized_locker_id = _normalize_locker_id(locker_id)
    normalized_region = _normalize_region(region)
    msg = (
        f"{pickup_id}|{token_id}|{normalized_locker_id}|{normalized_region}|{ctr}|{exp}"
    ).encode("utf-8")
    return hmac.new(_get_qr_secret_bytes(), msg, hashlib.sha256).hexdigest()


def _verify_qr_v1(*, pickup_id: str, token_id: str, ctr: int, exp: int, sig: str) -> bool:
    expected = _sign_qr_v1(
        pickup_id=pickup_id,
        token_id=token_id,
        ctr=ctr,
        exp=exp,
    )
    return hmac.compare_digest(expected, sig)


def _verify_qr_v2(
    *,
    pickup_id: str,
    token_id: str,
    locker_id: str,
    region: str,
    ctr: int,
    exp: int,
    sig: str,
) -> bool:
    expected = _sign_qr_v2(
        pickup_id=pickup_id,
        token_id=token_id,
        locker_id=locker_id,
        region=region,
        ctr=ctr,
        exp=exp,
    )
    return hmac.compare_digest(expected, sig)


def _get_pickup_by_order(db: Session, *, order_id: str) -> Pickup:
    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order_id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )
    if not pickup:
        raise HTTPException(status_code=404, detail="pickup not found")
    return pickup


def _get_pickup(db: Session, *, pickup_id: str) -> Pickup:
    pickup = db.query(Pickup).filter(Pickup.id == pickup_id).first()
    if not pickup:
        raise HTTPException(status_code=404, detail="pickup not found")
    return pickup


def _get_active_token(db: Session, *, pickup_id: str) -> PickupToken:
    now = _utcnow()
    pickup = _get_pickup(db, pickup_id=pickup_id)

    if pickup.current_token_id:
        tok = (
            db.query(PickupToken)
            .filter(
                PickupToken.id == pickup.current_token_id,
                PickupToken.pickup_id == pickup_id,
                PickupToken.used_at.is_(None),
                PickupToken.expires_at > now.replace(tzinfo=None),
            )
            .first()
        )
        if tok:
            return tok

    tok = (
        db.query(PickupToken)
        .filter(
            PickupToken.pickup_id == pickup_id,
            PickupToken.used_at.is_(None),
            PickupToken.expires_at > now.replace(tzinfo=None),
        )
        .order_by(PickupToken.expires_at.desc(), PickupToken.id.desc())
        .first()
    )
    if not tok:
        raise HTTPException(status_code=404, detail="pickup token not found")
    return tok


def _resolve_locker_id(order: Order, allocation: Allocation | None, pickup: Pickup | None = None) -> str | None:
    if pickup and getattr(pickup, "locker_id", None):
        return pickup.locker_id
    if allocation and getattr(allocation, "locker_id", None):
        return allocation.locker_id
    if getattr(order, "totem_id", None):
        return order.totem_id
    return None


def _ensure_expected_locker_id(*, payload_locker_id: str, resolved_locker_id: str | None) -> str:
    normalized_payload = _normalize_locker_id(payload_locker_id)
    normalized_resolved = str(resolved_locker_id or "").strip().upper()

    if not normalized_resolved:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "LOCKER_CONTEXT_MISSING",
                "message": "locker context missing for pickup redeem",
                "retryable": True,
            },
        )

    if normalized_payload != normalized_resolved:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_MISMATCH",
                "message": "pickup is not valid for this locker",
                "locker_id": normalized_payload,
                "expected_locker_id": normalized_resolved,
                "retryable": False,
            },
        )

    return normalized_resolved


def _verify_qr_payload_signature(qr: QrPayloadV1 | QrPayloadV2) -> bool:
    if qr.v == 2:
        return _verify_qr_v2(
            pickup_id=qr.pickup_id,
            token_id=qr.token_id,
            locker_id=qr.locker_id,
            region=qr.region,
            ctr=qr.ctr,
            exp=qr.exp,
            sig=qr.sig,
        )

    return _verify_qr_v1(
        pickup_id=qr.pickup_id,
        token_id=qr.token_id,
        ctr=qr.ctr,
        exp=qr.exp,
        sig=qr.sig,
    )


def _ensure_qr_v2_context(
    *,
    qr: QrPayloadV1 | QrPayloadV2,
    payload_region: str,
    payload_locker_id: str,
    resolved_locker_id: str,
) -> None:
    if qr.v != 2:
        return

    qr_region = _normalize_region(qr.region)
    request_region = _normalize_region(payload_region)
    if qr_region != request_region:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "QR_REGION_MISMATCH",
                "message": "QR region does not match redeem request region",
                "qr_region": qr_region,
                "request_region": request_region,
                "retryable": False,
            },
        )

    qr_locker_id = _normalize_locker_id(qr.locker_id)
    request_locker_id = _normalize_locker_id(payload_locker_id)
    expected_locker_id = _normalize_locker_id(resolved_locker_id)

    if qr_locker_id != request_locker_id or qr_locker_id != expected_locker_id:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "QR_LOCKER_MISMATCH",
                "message": "QR locker does not match redeem request locker",
                "qr_locker_id": qr_locker_id,
                "request_locker_id": request_locker_id,
                "expected_locker_id": expected_locker_id,
                "retryable": False,
            },
        )


def _mark_pickup_redeemed_operationally(
    *,
    pickup: Pickup,
    order: Order,
    allocation: Allocation,
    via: PickupRedeemVia,
) -> None:
    now_naive = _utcnow_naive()

    if pickup.lifecycle_stage != PickupLifecycleStage.DOOR_OPENED:
        pickup.mark_door_opened()

        publish_pickup_door_opened(
            order_id=order.id,
            pickup_id=pickup.id,
            channel=pickup.channel.value,
            region=pickup.region,
            locker_id=pickup.locker_id,
            machine_id=pickup.machine_id,
            slot=pickup.slot,
        )

    pickup.mark_item_removed()

    publish_pickup_item_removed(
        order_id=order.id,
        pickup_id=pickup.id,
        channel=pickup.channel.value,
        region=pickup.region,
        locker_id=pickup.locker_id,
        machine_id=pickup.machine_id,
        slot=pickup.slot,
    )

    pickup.mark_door_closed()

    publish_pickup_door_closed(
        order_id=order.id,
        pickup_id=pickup.id,
        channel=pickup.channel.value,
        region=pickup.region,
        locker_id=pickup.locker_id,
        machine_id=pickup.machine_id,
        slot=pickup.slot,
    )

    pickup.mark_redeemed(via)

    publish_pickup_redeemed(
        order_id=order.id,
        pickup_id=pickup.id,
        channel=pickup.channel.value,
        region=pickup.region,
        locker_id=pickup.locker_id,
        machine_id=pickup.machine_id,
        slot=pickup.slot,
        payload={"via": via.value},
    )

    order.mark_as_picked_up()
    allocation.state = AllocationState.PICKED_UP # provalvemente bug - isso depende de sensor OU confirmação humana
    # allocation.state = AllocationState.DISPENSED # máquina liberou - pickup.door_opened
    allocation.locked_until = None

    if pickup.channel == PickupChannel.KIOSK and not pickup.notes:
        pickup.notes = "Retirada concluída no fluxo KIOSK."


def _build_redeem_out(
    *,
    pickup: Pickup,
    order: Order,
    allocation: Allocation,
    locker_id: str,
) -> TotemRedeemOut:
    exp_dt = pickup.expires_at
    if exp_dt and exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)

    return TotemRedeemOut(
        pickup_id=pickup.id,
        order_id=order.id,
        locker_id=locker_id,
        slot=allocation.slot,
        expires_at=exp_dt,
    )


@router.post("/orders/{order_id}/pickup-token")
def legacy_generate_manual_code(
    order_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    order = (
        db.query(Order)
        .filter(
            Order.id == order_id,
            Order.user_id == str(user.id),
            Order.channel == OrderChannel.ONLINE,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="order not found")

    if order.status != OrderStatus.PAID_PENDING_PICKUP:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    pickup = _get_pickup_by_order(db, order_id=order.id)

    if pickup.channel != PickupChannel.ONLINE:
        raise HTTPException(status_code=409, detail="pickup token generation is only valid for ONLINE")

    _ensure_pickup_window(pickup)

    now = _utcnow()

    db.query(PickupToken).filter(
        PickupToken.pickup_id == pickup.id,
        PickupToken.used_at.is_(None),
        PickupToken.expires_at > now.replace(tzinfo=None),
    ).update({"used_at": now.replace(tzinfo=None)}, synchronize_session=False)

    manual_code = _generate_manual_code()

    deadline = pickup.expires_at
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)

    tok = PickupToken(
        id=str(uuid.uuid4()),
        pickup_id=pickup.id,
        token_hash=_sha256(manual_code),
        expires_at=deadline.replace(tzinfo=None),
        used_at=None,
    )
    db.add(tok)
    db.flush()

    pickup.current_token_id = tok.id
    pickup.touch()
    db.commit()

    return {
        "ok": True,
        "order_id": order.id,
        "pickup_id": pickup.id,
        "token_id": tok.id,
        "manual_code": manual_code,
        "expires_at": deadline.isoformat(),
        "note": "Gerar novo código invalida códigos anteriores.",
    }


@router.get("/me/pickups/{pickup_id}", response_model=PickupViewOut)
def me_pickup_view(
    pickup_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    pickup = _get_pickup(db, pickup_id=pickup_id)

    order = (
        db.query(Order)
        .filter(
            Order.id == pickup.order_id,
            Order.user_id == str(user.id),
            Order.channel == OrderChannel.ONLINE,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="pickup/order not found")

    expires_at = pickup.expires_at
    if expires_at and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    return PickupViewOut(
        pickup_id=pickup.id,
        order_id=order.id,
        region=pickup.region,
        status=pickup.status.value,
        expires_at=expires_at,
        qr_rotate_sec=QR_ROTATE_SEC,
        token_id=pickup.current_token_id,
        manual_code_hint=None,
    )


@router.post("/me/pickups/{pickup_id}/qr", response_model=PickupQrOut)
def me_pickup_qr(
    pickup_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user_or_dev),
):
    pickup = _get_pickup(db, pickup_id=pickup_id)

    order = (
        db.query(Order)
        .filter(
            Order.id == pickup.order_id,
            Order.user_id == str(user.id),
            Order.channel == OrderChannel.ONLINE,
        )
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="pickup/order not found")

    if pickup.channel != PickupChannel.ONLINE:
        raise HTTPException(status_code=409, detail="qr is only valid for ONLINE pickups")

    if pickup.status != PickupStatus.ACTIVE:
        raise HTTPException(status_code=409, detail=f"invalid pickup state: {pickup.status.value}")

    _ensure_pickup_window(pickup)

    tok = _get_active_token(db, pickup_id=pickup.id)

    exp_dt = pickup.expires_at
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=timezone.utc)
    exp_epoch = _epoch(exp_dt)

    issued_at = _issued_at_for_ctr(order)
    ctr = _calc_ctr(issued_at, QR_ROTATE_SEC)

    resolved_locker_id = _resolve_locker_id(order, None, pickup)
    if not resolved_locker_id:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "LOCKER_CONTEXT_MISSING",
                "message": "locker context missing for QR generation",
                "retryable": True,
            },
        )

    if QR_PAYLOAD_VERSION >= 2:
        qr = QrPayloadV2(
            pickup_id=pickup.id,
            token_id=tok.id,
            locker_id=_normalize_locker_id(resolved_locker_id),
            region=_normalize_region(order.region),
            ctr=ctr,
            exp=exp_epoch,
            sig=_sign_qr_v2(
                pickup_id=pickup.id,
                token_id=tok.id,
                locker_id=resolved_locker_id,
                region=order.region,
                ctr=ctr,
                exp=exp_epoch,
            ),
        )
    else:
        qr = QrPayloadV1(
            pickup_id=pickup.id,
            token_id=tok.id,
            ctr=ctr,
            exp=exp_epoch,
            sig=_sign_qr_v1(
                pickup_id=pickup.id,
                token_id=tok.id,
                ctr=ctr,
                exp=exp_epoch,
            ),
        )

    return PickupQrOut(qr=qr, refresh_in_sec=_refresh_in_sec(issued_at, QR_ROTATE_SEC))


@router.post("/totem/pickups/redeem", response_model=TotemRedeemOut)
def totem_redeem(payload: TotemRedeemIn, db: Session = Depends(get_db)):
    now = _utcnow()
    qr = payload.qr

    if now.timestamp() > qr.exp:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "PICKUP_EXPIRED",
                "message": "pickup window expired",
                "retryable": False,
            },
        )

    if not _verify_qr_payload_signature(qr):
        raise HTTPException(
            status_code=401,
            detail={
                "type": "INVALID_QR_SIGNATURE",
                "message": "invalid QR signature",
                "retryable": False,
            },
        )

    tok = (
        db.query(PickupToken)
        .filter(
            PickupToken.id == qr.token_id,
            PickupToken.used_at.is_(None),
            PickupToken.expires_at > now.replace(tzinfo=None),
        )
        .first()
    )
    if not tok or tok.pickup_id != qr.pickup_id:
        raise HTTPException(
            status_code=401,
            detail={
                "type": "INVALID_OR_EXPIRED_TOKEN",
                "message": "invalid or expired token",
                "retryable": False,
            },
        )

    pickup = _get_pickup(db, pickup_id=tok.pickup_id)
    order = (
        db.query(Order)
        .filter(Order.id == pickup.order_id, Order.channel == OrderChannel.ONLINE)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "order not found",
                "retryable": False,
            },
        )

    if pickup.channel != PickupChannel.ONLINE:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "INVALID_PICKUP_CHANNEL",
                "message": "QR redeem is only valid for ONLINE pickups",
                "retryable": False,
            },
        )

    if pickup.region != payload.region:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "WRONG_REGION",
                "message": "QR not valid for this region",
                "retryable": False,
            },
        )

    _ensure_pickup_window(pickup)

    issued_at = _issued_at_for_ctr(order)
    current_ctr = _calc_ctr(issued_at, QR_ROTATE_SEC)
    if qr.ctr not in (current_ctr, max(0, current_ctr - 1)):
        raise HTTPException(
            status_code=401,
            detail={
                "type": "STALE_QR",
                "message": "QR is stale; refresh and try again",
                "retryable": True,
            },
        )

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "ALLOCATION_NOT_FOUND",
                "message": "allocation not found",
                "retryable": True,
            },
        )

    locker_id = _resolve_locker_id(order, allocation, pickup)
    resolved_locker_id = _ensure_expected_locker_id(
        payload_locker_id=payload.locker_id,
        resolved_locker_id=locker_id,
    )

    _ensure_qr_v2_context(
        qr=qr,
        payload_region=payload.region,
        payload_locker_id=payload.locker_id,
        resolved_locker_id=resolved_locker_id,
    )

    tok.used_at = now.replace(tzinfo=None)

    backend_client.locker_light_on(
        order.region,
        allocation.slot,
        locker_id=resolved_locker_id,
    )
    backend_client.locker_open(
        order.region,
        allocation.slot,
        locker_id=resolved_locker_id,
    )
    backend_client.locker_set_state(
        order.region,
        allocation.slot,
        "OUT_OF_STOCK",
        locker_id=resolved_locker_id,
    )

    _mark_pickup_redeemed_operationally(
        pickup=pickup,
        order=order,
        allocation=allocation,
        via=PickupRedeemVia.QR,
    )

    db.commit()

    return _build_redeem_out(
        pickup=pickup,
        order=order,
        allocation=allocation,
        locker_id=resolved_locker_id,
    )


@router.post("/totem/pickups/redeem-manual", response_model=TotemRedeemOut)
def totem_redeem_manual(
    payload: TotemRedeemManualIn,
    request: Request,
    db: Session = Depends(get_db),
):
    now = _utcnow()
    token_hash = _sha256(payload.manual_code)

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
        _register_manual_redeem_failure(payload.region, payload.manual_code, request)
        raise HTTPException(
            status_code=401,
            detail={
                "type": "INVALID_OR_EXPIRED_CODE",
                "message": "invalid or expired manual code",
                "retryable": False,
            },
        )

    pickup = _get_pickup(db, pickup_id=tok.pickup_id)
    order = (
        db.query(Order)
        .filter(Order.id == pickup.order_id, Order.channel == OrderChannel.ONLINE)
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "order not found",
                "retryable": False,
            },
        )

    if pickup.channel != PickupChannel.ONLINE:
        _register_manual_redeem_failure(payload.region, payload.manual_code, request)
        raise HTTPException(
            status_code=409,
            detail={
                "type": "INVALID_PICKUP_CHANNEL",
                "message": "manual redeem is only valid for ONLINE pickups",
                "retryable": False,
            },
        )

    if pickup.region != payload.region:
        _register_manual_redeem_failure(payload.region, payload.manual_code, request)
        raise HTTPException(
            status_code=403,
            detail={
                "type": "WRONG_REGION",
                "message": "code not valid for this region",
                "retryable": False,
            },
        )

    _ensure_pickup_window(pickup)

    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    if not allocation:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "ALLOCATION_NOT_FOUND",
                "message": "allocation not found",
                "retryable": True,
            },
        )

    locker_id = _resolve_locker_id(order, allocation, pickup)
    resolved_locker_id = _ensure_expected_locker_id(
        payload_locker_id=payload.locker_id,
        resolved_locker_id=locker_id,
    )

    tok.used_at = now.replace(tzinfo=None)

    backend_client.locker_light_on(
        order.region,
        allocation.slot,
        locker_id=resolved_locker_id,
    )
    backend_client.locker_open(
        order.region,
        allocation.slot,
        locker_id=resolved_locker_id,
    )
    backend_client.locker_set_state(
        order.region,
        allocation.slot,
        "OUT_OF_STOCK",
        locker_id=resolved_locker_id,
    )

    _mark_pickup_redeemed_operationally(
        pickup=pickup,
        order=order,
        allocation=allocation,
        via=PickupRedeemVia.MANUAL,
    )

    db.commit()
    _clear_manual_redeem_failures(payload.region, payload.manual_code, request)

    return _build_redeem_out(
        pickup=pickup,
        order=order,
        allocation=allocation,
        locker_id=resolved_locker_id,
    )