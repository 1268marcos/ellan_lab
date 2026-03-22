# 01_source/order_pickup_service/app/routers/internal.py
# Router: /internal/* (protegido por X-Internal-Token)

from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.core.lifecycle_client import LifecycleClientError
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
from app.schemas.internal import InternalPaymentApprovedIn as PaymentConfirmIn
from app.services import backend_client
from app.services.lifecycle_integration import cancel_prepayment_timeout_deadline

from app.services.pickup_event_publisher import (
    publish_pickup_created,
    publish_pickup_ready,
    publish_pickup_door_opened,
    publish_pickup_expired,
    publish_pickup_cancelled,
)

from app.services.domain_event_outbox_service import enqueue_order_paid_event

router = APIRouter(prefix="/internal", tags=["internal"])

PICKUP_WINDOW_HOURS = 2
QR_ROTATE_SEC = settings.qr_rotate_sec


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_naive() -> datetime:
    return _utc_now().replace(tzinfo=None)


def _enum_value_or_raw(value) -> str | None:
    if value is None:
        return None
    return getattr(value, "value", value)


def _ensure_allocation(db: Session, order_id: str) -> Allocation:
    allocation = db.query(Allocation).filter(Allocation.order_id == order_id).first()
    if not allocation:
        raise HTTPException(status_code=500, detail="allocation not found")
    return allocation


def _ensure_order(db: Session, order_id: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="order not found")
    return order


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _generate_manual_code() -> str:
    return f"{uuid.uuid4().int % 1_000_000:06d}"


def _create_pickup_token(db: Session, *, pickup_id: str, expires_at_utc: datetime) -> dict:
    manual_code = _generate_manual_code()
    tok = PickupToken(
        id=str(uuid.uuid4()),
        pickup_id=pickup_id,
        token_hash=_sha256(manual_code),
        expires_at=expires_at_utc.replace(tzinfo=None),
        used_at=None,
    )
    db.add(tok)
    db.flush()
    return {"token_id": tok.id, "manual_code": manual_code}


def _pickup_channel_from_order(order: Order) -> PickupChannel:
    return PickupChannel.KIOSK if order.channel == OrderChannel.KIOSK else PickupChannel.ONLINE


def _build_pickup_context(order: Order, allocation: Allocation) -> dict:
    return {
        "channel": _pickup_channel_from_order(order),
        "region": order.region,
        "locker_id": allocation.locker_id or order.totem_id,
        "machine_id": order.totem_id,
        "slot": str(allocation.slot) if allocation.slot is not None else None,
        "operator_id": None,
        "tenant_id": None,
        "site_id": None,
    }


def _apply_pickup_context(pickup: Pickup, *, order: Order, allocation: Allocation) -> None:
    ctx = _build_pickup_context(order, allocation)
    pickup.channel = ctx["channel"]
    pickup.region = ctx["region"]
    pickup.locker_id = ctx["locker_id"]
    pickup.machine_id = ctx["machine_id"]
    pickup.slot = ctx["slot"]
    pickup.operator_id = ctx["operator_id"]
    pickup.tenant_id = ctx["tenant_id"]
    pickup.site_id = ctx["site_id"]


def _ensure_online_pickup(
    db: Session,
    *,
    order: Order,
    allocation: Allocation,
    deadline_utc: datetime,
) -> Pickup:
    now_naive = _utc_now_naive()
    existing_pickup = _get_active_pickup_by_order(db, order.id)

    if existing_pickup:
        pickup = existing_pickup
        _apply_pickup_context(pickup, order=order, allocation=allocation)
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.READY_FOR_PICKUP
        pickup.activated_at = pickup.activated_at or now_naive
        pickup.ready_at = now_naive
        pickup.expires_at = deadline_utc.replace(tzinfo=None)
        pickup.door_opened_at = None
        pickup.item_removed_at = None
        pickup.door_closed_at = None
        pickup.redeemed_at = None
        pickup.redeemed_via = None
        pickup.expired_at = None
        pickup.cancelled_at = None
        pickup.cancel_reason = None
        pickup.notes = None
        pickup.touch()
        return pickup

    pickup = Pickup(
        id=str(uuid.uuid4()),
        order_id=order.id,
        channel=PickupChannel.ONLINE,
        region=order.region,
        locker_id=allocation.locker_id or order.totem_id,
        machine_id=order.totem_id,
        slot=str(allocation.slot) if allocation.slot is not None else None,
        operator_id=None,
        tenant_id=None,
        site_id=None,
        status=PickupStatus.ACTIVE,
        lifecycle_stage=PickupLifecycleStage.READY_FOR_PICKUP,
        current_token_id=None,
        activated_at=now_naive,
        ready_at=now_naive,
        expires_at=deadline_utc.replace(tzinfo=None),
        door_opened_at=None,
        item_removed_at=None,
        door_closed_at=None,
        redeemed_at=None,
        redeemed_via=None,
        expired_at=None,
        cancelled_at=None,
        cancel_reason=None,
        correlation_id=None,
        source_event_id=None,
        sensor_event_id=None,
        notes=None,
    )
    db.add(pickup)
    db.flush()
    return pickup


def _ensure_kiosk_pickup(
    db: Session,
    *,
    order: Order,
    allocation: Allocation,
) -> Pickup:
    now_naive = _utc_now_naive()
    existing_pickup = _get_active_pickup_by_order(db, order.id)

    if existing_pickup:
        pickup = existing_pickup
        _apply_pickup_context(pickup, order=order, allocation=allocation)
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.DOOR_OPENED
        pickup.activated_at = pickup.activated_at or now_naive
        pickup.ready_at = pickup.ready_at or now_naive
        pickup.expires_at = None
        pickup.door_opened_at = pickup.door_opened_at or now_naive
        pickup.item_removed_at = None
        pickup.door_closed_at = None
        pickup.redeemed_at = None
        pickup.redeemed_via = None
        pickup.expired_at = None
        pickup.cancelled_at = None
        pickup.cancel_reason = None
        pickup.current_token_id = None
        pickup.notes = "Pickup liberado via fluxo KIOSK."
        pickup.touch()
        return pickup

    pickup = Pickup(
        id=str(uuid.uuid4()),
        order_id=order.id,
        channel=PickupChannel.KIOSK,
        region=order.region,
        locker_id=allocation.locker_id or order.totem_id,
        machine_id=order.totem_id,
        slot=str(allocation.slot) if allocation.slot is not None else None,
        operator_id=None,
        tenant_id=None,
        site_id=None,
        status=PickupStatus.ACTIVE,
        lifecycle_stage=PickupLifecycleStage.DOOR_OPENED,
        current_token_id=None,
        activated_at=now_naive,
        ready_at=now_naive,
        expires_at=None,
        door_opened_at=now_naive,
        item_removed_at=None,
        door_closed_at=None,
        redeemed_at=None,
        redeemed_via=None,
        expired_at=None,
        cancelled_at=None,
        cancel_reason=None,
        correlation_id=None,
        source_event_id=None,
        sensor_event_id=None,
        notes="Pickup liberado via fluxo KIOSK.",
    )
    db.add(pickup)
    db.flush()
    return pickup


def _reallocate_if_needed(db: Session, *, order: Order, allocation: Allocation) -> Allocation:
    request_id = str(uuid.uuid4())

    try:
        alloc = backend_client.locker_allocate(
            order.region,
            order.sku_id,
            ttl_sec=120,
            request_id=request_id,
            locker_id=order.totem_id,
        )
    except requests.HTTPError as e:
        status = getattr(e.response, "status_code", None)

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
                    "type": "REALLOCATE_CONFLICT",
                    "message": "A reserva original expirou e não foi possível realocar uma nova gaveta.",
                    "order_id": order.id,
                    "region": order.region,
                    "locker_id": order.totem_id,
                    "sku_id": order.sku_id,
                    "retryable": True,
                    "action": "create_new_order",
                    "backend_detail": backend_detail,
                },
            )

        raise HTTPException(
            status_code=502,
            detail={
                "type": "REALLOCATE_FAILED",
                "message": "Falha ao tentar realocar gaveta no backend.",
                "order_id": order.id,
                "region": order.region,
                "locker_id": order.totem_id,
                "sku_id": order.sku_id,
                "backend_status": status,
                "backend_detail": backend_detail,
            },
        )

    new_allocation_id = alloc.get("allocation_id")
    new_slot = alloc.get("slot")

    if not new_allocation_id or new_slot is None:
        raise HTTPException(
            status_code=502,
            detail={
                "type": "REALLOCATE_INVALID_RESPONSE",
                "message": "Resposta inválida do backend ao realocar gaveta.",
                "order_id": order.id,
            },
        )

    allocation.mark_released()

    new_alloc = Allocation(
        id=new_allocation_id,
        order_id=order.id,
        locker_id=order.totem_id,
        slot=int(new_slot),
        state=AllocationState.RESERVED_PENDING_PAYMENT,
        locked_until=None,
    )
    db.add(new_alloc)
    db.flush()
    return new_alloc


def _get_active_pickup_by_order(db: Session, order_id: str) -> Optional[Pickup]:
    return (
        db.query(Pickup)
        .filter(
            Pickup.order_id == order_id,
            Pickup.status == PickupStatus.ACTIVE,
        )
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )


def _get_latest_pickup_by_order(db: Session, order_id: str) -> Optional[Pickup]:
    return (
        db.query(Pickup)
        .filter(Pickup.order_id == order_id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )


@router.get("/health")
def internal_health(_=Depends(require_internal_token)):
    return {
        "ok": True,
        "service": "order_pickup_service",
        "time": _utc_now().isoformat(),
    }


@router.post("/orders/{order_id}/payment-confirm")
def payment_confirm(
    order_id: str,
    payload: PaymentConfirmIn,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    order = _ensure_order(db, order_id)

    if getattr(payload, "region", None) and order.region != payload.region:
        raise HTTPException(
            status_code=409,
            detail=f"region mismatch: order={order.region} payload={payload.region}",
        )

    if order.status in (
        OrderStatus.PAID_PENDING_PICKUP,
        OrderStatus.DISPENSED,
        OrderStatus.PICKED_UP,
    ):
        allocation = _ensure_allocation(db, order.id)
        pickup = _get_latest_pickup_by_order(db, order.id)

        return {
            "ok": True,
            "idempotent": True,
            "order_id": order.id,
            "channel": order.channel.value,
            "status": order.status.value,
            "slot": allocation.slot,
            "allocation_id": allocation.id,
            "payment_method": _enum_value_or_raw(order.payment_method),
            "picked_up_at": order.picked_up_at.isoformat() if order.picked_up_at else None,
            "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
            "pickup_id": pickup.id if pickup else None,
            "pickup_status": pickup.status.value if pickup else None,
            "pickup_expires_at": pickup.expires_at.isoformat() if pickup and pickup.expires_at else None,
            "pickup_channel": pickup.channel.value if pickup and pickup.channel else None,
            "pickup_lifecycle_stage": pickup.lifecycle_stage.value if pickup and pickup.lifecycle_stage else None,
            "pickup_locker_id": pickup.locker_id if pickup else None,
            "pickup_machine_id": pickup.machine_id if pickup else None,
            "pickup_slot": pickup.slot if pickup else None,
            "token_id": pickup.current_token_id if pickup else None,
            "manual_code": None,
            "qr_rotate_sec": QR_ROTATE_SEC if order.channel == OrderChannel.ONLINE else None,
            "totem_id": order.totem_id,
        }

    if order.status != OrderStatus.PAYMENT_PENDING:
        raise HTTPException(status_code=409, detail=f"invalid state: {order.status.value}")

    allocation = _ensure_allocation(db, order.id)
    now = _utc_now()

    order.gateway_transaction_id = payload.transaction_id
    provider_value = getattr(payload, "provider", None)
    if provider_value:
        order.payment_method = _enum_value_or_raw(provider_value)
    order.paid_at = now
    order.mark_payment_approved()

    token_id: Optional[str] = None
    manual_code: Optional[str] = None
    pickup: Optional[Pickup] = None

    if order.channel == OrderChannel.ONLINE:
        deadline = now + timedelta(hours=PICKUP_WINDOW_HOURS)

        order.pickup_deadline_at = deadline
        order.status = OrderStatus.PAID_PENDING_PICKUP

        allocation.mark_reserved_paid_pending_pickup()
        allocation.locked_until = deadline.replace(tzinfo=None)

        try:
            backend_client.locker_commit(
                order.region,
                allocation.id,
                deadline.isoformat(),
                locker_id=order.totem_id,
            )
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)

            if status == 409:
                allocation = _reallocate_if_needed(db, order=order, allocation=allocation)
                allocation.mark_reserved_paid_pending_pickup()
                allocation.locked_until = deadline.replace(tzinfo=None)

                try:
                    backend_client.locker_commit(
                        order.region,
                        allocation.id,
                        deadline.isoformat(),
                        locker_id=order.totem_id,
                    )
                except requests.HTTPError as e2:
                    status2 = getattr(e2.response, "status_code", None)

                    backend_detail = None
                    if e2.response is not None:
                        try:
                            backend_detail = e2.response.json()
                        except Exception:
                            backend_detail = e2.response.text

                    raise HTTPException(
                        status_code=409 if status2 == 409 else 502,
                        detail={
                            "type": "COMMIT_AFTER_REALLOCATE_FAILED",
                            "message": "A gaveta foi realocada, mas o commit final falhou.",
                            "order_id": order.id,
                            "allocation_id": allocation.id,
                            "region": order.region,
                            "locker_id": order.totem_id,
                            "backend_status": status2,
                            "backend_detail": backend_detail,
                        },
                    )
            else:
                backend_detail = None
                if e.response is not None:
                    try:
                        backend_detail = e.response.json()
                    except Exception:
                        backend_detail = e.response.text

                raise HTTPException(
                    status_code=409 if status == 409 else 502,
                    detail={
                        "type": "LOCKER_COMMIT_FAILED",
                        "message": "Falha ao confirmar a reserva da gaveta no backend.",
                        "order_id": order.id,
                        "allocation_id": allocation.id,
                        "region": order.region,
                        "locker_id": order.totem_id,
                        "backend_status": status,
                        "backend_detail": backend_detail,
                    },
                )

        backend_client.locker_set_state(
            order.region,
            allocation.slot,
            "PAID_PENDING_PICKUP",
            locker_id=order.totem_id,
        )

        pickup = _ensure_online_pickup(
            db,
            order=order,
            allocation=allocation,
            deadline_utc=deadline,
        )

        publish_pickup_created(
            order_id=order.id,
            pickup_id=pickup.id,
            channel=pickup.channel.value,
            region=pickup.region,
            locker_id=pickup.locker_id,
            machine_id=pickup.machine_id,
            slot=pickup.slot,
        )

        publish_pickup_ready(
            order_id=order.id,
            pickup_id=pickup.id,
            channel=pickup.channel.value,
            region=pickup.region,
            locker_id=pickup.locker_id,
            machine_id=pickup.machine_id,
            slot=pickup.slot,
        )

        tok = _create_pickup_token(db, pickup_id=pickup.id, expires_at_utc=deadline)
        token_id = tok["token_id"]
        manual_code = tok["manual_code"]
        pickup.current_token_id = token_id
        pickup.touch()

    else:
        order.pickup_deadline_at = None
        order.status = OrderStatus.DISPENSED

        allocation.mark_opened_for_pickup()

        try:
            backend_client.locker_commit(
                order.region,
                allocation.id,
                None,
                locker_id=order.totem_id,
            )
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)

            if status == 409:
                allocation = _reallocate_if_needed(db, order=order, allocation=allocation)
                allocation.mark_opened_for_pickup()

                try:
                    backend_client.locker_commit(
                        order.region,
                        allocation.id,
                        None,
                        locker_id=order.totem_id,
                    )
                except requests.HTTPError as e2:
                    status2 = getattr(e2.response, "status_code", None)

                    backend_detail = None
                    if e2.response is not None:
                        try:
                            backend_detail = e2.response.json()
                        except Exception:
                            backend_detail = e2.response.text

                    raise HTTPException(
                        status_code=409 if status2 == 409 else 502,
                        detail={
                            "type": "COMMIT_AFTER_REALLOCATE_FAILED",
                            "message": "A gaveta foi realocada no fluxo KIOSK, mas o commit final falhou.",
                            "order_id": order.id,
                            "allocation_id": allocation.id,
                            "region": order.region,
                            "locker_id": order.totem_id,
                            "backend_status": status2,
                            "backend_detail": backend_detail,
                        },
                    )
            else:
                backend_detail = None
                if e.response is not None:
                    try:
                        backend_detail = e.response.json()
                    except Exception:
                        backend_detail = e.response.text

                raise HTTPException(
                    status_code=409 if status == 409 else 502,
                    detail={
                        "type": "LOCKER_COMMIT_FAILED",
                        "message": "Falha ao confirmar a reserva da gaveta no fluxo KIOSK.",
                        "order_id": order.id,
                        "allocation_id": allocation.id,
                        "region": order.region,
                        "locker_id": order.totem_id,
                        "backend_status": status,
                        "backend_detail": backend_detail,
                    },
                )

        pickup = _ensure_kiosk_pickup(
            db,
            order=order,
            allocation=allocation,
        )

        publish_pickup_created(
            order_id=order.id,
            pickup_id=pickup.id,
            channel=pickup.channel.value,
            region=pickup.region,
            locker_id=pickup.locker_id,
            machine_id=pickup.machine_id,
            slot=pickup.slot,
        )

        publish_pickup_door_opened(
            order_id=order.id,
            pickup_id=pickup.id,
            channel=pickup.channel.value,
            region=pickup.region,
            locker_id=pickup.locker_id,
            machine_id=pickup.machine_id,
            slot=pickup.slot,
        )

        backend_client.locker_light_on(
            order.region,
            allocation.slot,
            locker_id=order.totem_id,
        )
        backend_client.locker_open(
            order.region,
            allocation.slot,
            locker_id=order.totem_id,
        )

    # order.paid nasce na mesma transação que confirmou o pagamento
    enqueue_order_paid_event(
        db,
        order_id=order.id,
        region=order.region,
        channel=_enum_value_or_raw(order.channel),
        payment_method=_enum_value_or_raw(order.payment_method),
        transaction_id=order.gateway_transaction_id,
        amount_cents=order.amount_cents,
        currency=payload.currency,
        locker_id=(pickup.locker_id if pickup else order.totem_id),
        machine_id=(pickup.machine_id if pickup else order.totem_id),
        slot=(pickup.slot if pickup else allocation.slot),
        allocation_id=allocation.id,
        pickup_id=(pickup.id if pickup else None),
        tenant_id=None,
        operator_id=None,
        site_id=None,
        source_service="order_pickup_service",
    )

    db.commit()
    db.refresh(order)
    db.refresh(allocation)
    if pickup is not None:
        db.refresh(pickup)

    try:
        cancel_prepayment_timeout_deadline(order_id=order.id)
    except LifecycleClientError:
        raise HTTPException(
            status_code=503,
            detail={
                "type": "LIFECYCLE_DEADLINE_CANCEL_FAILED",
                "message": "Pagamento confirmado localmente, mas falhou ao cancelar o deadline de pré-pagamento.",
                "order_id": order.id,
                "channel": order.channel.value,
                "region": order.region,
            },
        )

    return {
        "ok": True,
        "order_id": order.id,
        "channel": order.channel.value,
        "status": order.status.value,
        "slot": allocation.slot,
        "allocation_id": allocation.id,
        "payment_method": _enum_value_or_raw(order.payment_method),
        "picked_up_at": order.picked_up_at.isoformat() if order.picked_up_at else None,
        "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
        "pickup_id": pickup.id if pickup else None,
        "pickup_status": pickup.status.value if pickup else None,
        "pickup_expires_at": pickup.expires_at.isoformat() if pickup and pickup.expires_at else None,
        "pickup_channel": pickup.channel.value if pickup and pickup.channel else None,
        "pickup_lifecycle_stage": pickup.lifecycle_stage.value if pickup and pickup.lifecycle_stage else None,
        "pickup_locker_id": pickup.locker_id if pickup else None,
        "pickup_machine_id": pickup.machine_id if pickup else None,
        "pickup_slot": pickup.slot if pickup else None,
        "token_id": token_id,
        "manual_code": manual_code,
        "qr_rotate_sec": QR_ROTATE_SEC if order.channel == OrderChannel.ONLINE else None,
        "totem_id": order.totem_id,
    }


@router.post("/orders/{order_id}/release")
def release_order(
    order_id: str,
    reason: Optional[str] = None,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    order = _ensure_order(db, order_id)
    allocation = _ensure_allocation(db, order.id)

    if order.status in (OrderStatus.PICKED_UP,):
        raise HTTPException(status_code=409, detail=f"cannot release in state: {order.status.value}")

    try:
        backend_client.locker_release(
            order.region,
            allocation.id,
            locker_id=order.totem_id,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"backend release failed: {str(e)}")

    order.status = OrderStatus.EXPIRED
    order.mark_payment_expired()
    allocation.mark_released()

    pickup = _get_active_pickup_by_order(db, order.id)
    if pickup:
        if order.channel == OrderChannel.ONLINE:
            pickup.mark_expired()

            publish_pickup_expired(
                order_id=order.id,
                pickup_id=pickup.id,
                channel=pickup.channel.value,
                region=pickup.region,
                locker_id=pickup.locker_id,
                machine_id=pickup.machine_id,
                slot=pickup.slot,
            )

        else:
            pickup.mark_cancelled(reason or "kiosk_release_before_completion")

            publish_pickup_cancelled(
                order_id=order.id,
                pickup_id=pickup.id,
                channel=pickup.channel.value,
                region=pickup.region,
                locker_id=pickup.locker_id,
                machine_id=pickup.machine_id,
                slot=pickup.slot,
                payload={"reason": reason},
            )

    db.commit()

    return {
        "ok": True,
        "order_id": order.id,
        "status": order.status.value,
        "reason": reason,
        "pickup_id": pickup.id if pickup else None,
        "pickup_status": pickup.status.value if pickup else None,
        "pickup_lifecycle_stage": pickup.lifecycle_stage.value if pickup else None,
        "totem_id": order.totem_id,
    }


@router.post("/slots/{slot}/set-state")
def internal_set_slot_state(
    slot: int,
    state: str,
    region: str,
    totem_id: str,
    _=Depends(require_internal_token),
):
    if slot < 1 or slot > 24:
        raise HTTPException(status_code=400, detail="slot must be between 1 and 24")
    if region not in ("SP", "PT"):
        raise HTTPException(status_code=400, detail="region must be SP or PT")
    if not totem_id or not str(totem_id).strip():
        raise HTTPException(status_code=400, detail="totem_id is required")

    try:
        resp = backend_client.locker_set_state(
            region,
            slot,
            state,
            locker_id=totem_id,
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"backend set-state failed: {str(e)}")

    return {
        "ok": True,
        "region": region,
        "totem_id": totem_id,
        "slot": slot,
        "state": state,
        "backend_response": resp,
    }


@router.get("/orders/{order_id}/status")
def internal_order_status(
    order_id: str,
    _=Depends(require_internal_token),
    db: Session = Depends(get_db),
):
    order = _ensure_order(db, order_id)
    allocation = db.query(Allocation).filter(Allocation.order_id == order.id).first()
    pickup = _get_latest_pickup_by_order(db, order.id)

    return {
        "ok": True,
        "order": {
            "id": order.id,
            "channel": order.channel.value,
            "region": order.region,
            "totem_id": order.totem_id,
            "sku_id": getattr(order, "sku_id", None),
            "status": order.status.value,
            "amount_cents": getattr(order, "amount_cents", None),
            "payment_method": _enum_value_or_raw(order.payment_method),
            "paid_at": order.paid_at.isoformat() if getattr(order, "paid_at", None) else None,
            "pickup_deadline_at": order.pickup_deadline_at.isoformat() if order.pickup_deadline_at else None,
            "picked_up_at": order.picked_up_at.isoformat() if order.picked_up_at else None,
            "gateway_transaction_id": getattr(order, "gateway_transaction_id", None),
        },
        "allocation": None if not allocation else {
            "id": allocation.id,
            "locker_id": allocation.locker_id,
            "slot": allocation.slot,
            "state": allocation.state.value,
            "locked_until": allocation.locked_until.isoformat() if allocation.locked_until else None,
        },
        "pickup": None if not pickup else {
            "id": pickup.id,
            "order_id": pickup.order_id,
            "channel": pickup.channel.value if pickup.channel else None,
            "region": pickup.region,
            "locker_id": pickup.locker_id,
            "machine_id": pickup.machine_id,
            "slot": pickup.slot,
            "status": pickup.status.value,
            "lifecycle_stage": pickup.lifecycle_stage.value if pickup.lifecycle_stage else None,
            "expires_at": pickup.expires_at.isoformat() if pickup.expires_at else None,
            "current_token_id": pickup.current_token_id,
            "activated_at": pickup.activated_at.isoformat() if pickup.activated_at else None,
            "ready_at": pickup.ready_at.isoformat() if pickup.ready_at else None,
            "door_opened_at": pickup.door_opened_at.isoformat() if pickup.door_opened_at else None,
            "item_removed_at": pickup.item_removed_at.isoformat() if pickup.item_removed_at else None,
            "door_closed_at": pickup.door_closed_at.isoformat() if pickup.door_closed_at else None,
            "redeemed_at": pickup.redeemed_at.isoformat() if pickup.redeemed_at else None,
            "redeemed_via": pickup.redeemed_via.value if pickup.redeemed_via else None,
            "expired_at": pickup.expired_at.isoformat() if pickup.expired_at else None,
            "cancelled_at": pickup.cancelled_at.isoformat() if pickup.cancelled_at else None,
            "cancel_reason": pickup.cancel_reason,
            "correlation_id": pickup.correlation_id,
            "source_event_id": pickup.source_event_id,
            "sensor_event_id": pickup.sensor_event_id,
            "notes": pickup.notes,
        },
    }