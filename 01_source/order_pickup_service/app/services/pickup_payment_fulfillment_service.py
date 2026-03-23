# 01_source/order_pickup_service/app/services/pickup_payment_fulfillment_service.py
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import requests
from sqlalchemy.orm import Session

from app.models.allocation import Allocation, AllocationState
from app.models.order import Order, OrderChannel, OrderStatus
from app.models.pickup import (
    Pickup,
    PickupChannel,
    PickupLifecycleStage,
    PickupStatus,
)
from app.models.pickup_token import PickupToken
from app.services import backend_client
from app.services.pickup_event_publisher import (
    publish_pickup_created,
    publish_pickup_door_opened,
    publish_pickup_ready,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_naive() -> datetime:
    return _utc_now().replace(tzinfo=None)


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
            raise RuntimeError(
                {
                    "type": "REALLOCATE_CONFLICT",
                    "message": "A reserva original expirou e não foi possível realocar uma nova gaveta.",
                    "order_id": order.id,
                    "region": order.region,
                    "locker_id": order.totem_id,
                    "sku_id": order.sku_id,
                    "retryable": True,
                    "action": "create_new_order",
                    "backend_detail": backend_detail,
                }
            )

        raise RuntimeError(
            {
                "type": "REALLOCATE_FAILED",
                "message": "Falha ao tentar realocar gaveta no backend.",
                "order_id": order.id,
                "region": order.region,
                "locker_id": order.totem_id,
                "sku_id": order.sku_id,
                "backend_status": status,
                "backend_detail": backend_detail,
            }
        )

    new_allocation_id = alloc.get("allocation_id")
    new_slot = alloc.get("slot")

    if not new_allocation_id or new_slot is None:
        raise RuntimeError(
            {
                "type": "REALLOCATE_INVALID_RESPONSE",
                "message": "Resposta inválida do backend ao realocar gaveta.",
                "order_id": order.id,
            }
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


def fulfill_payment_post_approval(
    *,
    db: Session,
    order: Order,
    allocation: Allocation,
    pickup_window_hours: int = 2,
    set_kiosk_out_of_stock: bool = True,
) -> dict:
    """
    Serviço operacional pós-pagamento:
    - ONLINE => reserva paga, pickup pronto, token manual
    - KIOSK => locker aberto, pickup ativo, sem token
    """

    if order.channel == OrderChannel.ONLINE:
        now = _utc_now()
        deadline = now + timedelta(hours=pickup_window_hours)

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

                    raise RuntimeError(
                        {
                            "type": "COMMIT_AFTER_REALLOCATE_FAILED",
                            "message": "A gaveta foi realocada, mas o commit final falhou.",
                            "order_id": order.id,
                            "allocation_id": allocation.id,
                            "region": order.region,
                            "locker_id": order.totem_id,
                            "backend_status": status2,
                            "backend_detail": backend_detail,
                        }
                    )
            else:
                backend_detail = None
                if e.response is not None:
                    try:
                        backend_detail = e.response.json()
                    except Exception:
                        backend_detail = e.response.text

                raise RuntimeError(
                    {
                        "type": "LOCKER_COMMIT_FAILED",
                        "message": "Falha ao confirmar a reserva da gaveta no backend.",
                        "order_id": order.id,
                        "allocation_id": allocation.id,
                        "region": order.region,
                        "locker_id": order.totem_id,
                        "backend_status": status,
                        "backend_detail": backend_detail,
                    }
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

        return {
            "allocation": allocation,
            "pickup": pickup,
            "token_id": token_id,
            "manual_code": manual_code,
            "pickup_deadline_at": deadline,
        }

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

                raise RuntimeError(
                    {
                        "type": "COMMIT_AFTER_REALLOCATE_FAILED",
                        "message": "A gaveta foi realocada no fluxo KIOSK, mas o commit final falhou.",
                        "order_id": order.id,
                        "allocation_id": allocation.id,
                        "region": order.region,
                        "locker_id": order.totem_id,
                        "backend_status": status2,
                        "backend_detail": backend_detail,
                    }
                )
        else:
            backend_detail = None
            if e.response is not None:
                try:
                    backend_detail = e.response.json()
                except Exception:
                    backend_detail = e.response.text

            raise RuntimeError(
                {
                    "type": "LOCKER_COMMIT_FAILED",
                    "message": "Falha ao confirmar a reserva da gaveta no fluxo KIOSK.",
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "region": order.region,
                    "locker_id": order.totem_id,
                    "backend_status": status,
                    "backend_detail": backend_detail,
                }
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

    if set_kiosk_out_of_stock:
        backend_client.locker_set_state(
            order.region,
            allocation.slot,
            "OUT_OF_STOCK",
            locker_id=order.totem_id,
        )

    return {
        "allocation": allocation,
        "pickup": pickup,
        "token_id": None,
        "manual_code": None,
        "pickup_deadline_at": None,
    }