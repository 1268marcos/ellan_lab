# 01_source/order_pickup_service/app/routers/dev_admin.py
# 15/04/2026 - nova @router.post("/simulate-online-payment") - foi substituída em 17/04/2026
# 17/04/2026 - nova @router.post("/simulate-online-payment")
# 18/04/2026 - remoção : from app.routers.internal import _ensure_online_pickup, _create_pickup_token
# 18/04/2026 - remoção : from app.routers.internal import _ensure_online_pickup
# 18/04/2026 - inclusão : from app.services.pickup_payment_fulfillment_service import _create_pickup_token, _ensure_online_pickup
# 20/04/2026 - compensação para não deixar slot preso

from __future__ import annotations

import logging

from typing import Any

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.config import settings
from app.core.db import get_db

from app.models.order import Order, OrderStatus
from app.models.pickup import Pickup
from app.schemas.dev_admin import (
    DevReconcileOrderIn,
    DevReconcileOrderOut,
    DevReleaseRegionalAllocationsIn,
    DevReleaseRegionalAllocationsOut,
    DevResetLockerIn,
    DevResetLockerOut,
)
from app.services import backend_client

from uuid import uuid4


from app.models.allocation import Allocation, AllocationState
from app.models.pickup import Pickup, PickupStatus, PickupLifecycleStage, PickupChannel
from app.models.pickup_token import PickupToken

from app.services.payment_confirm_service import apply_payment_confirmation

from app.services.pickup_payment_fulfillment_service import (
    _create_pickup_token,
    _ensure_online_pickup,
    fulfill_payment_post_approval,
)
from app.services.order_reconciliation_service import (
    reconcile_order_compensation,
    resolve_latest_allocation,
    resolve_latest_pickup,
)

from app.routers.internal import _ensure_allocation

from app.core.datetime_utils import to_iso_utc



logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/dev-admin",
    tags=["dev-admin"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria"}))],
)

#-------------------------------------
# HELPERS
#-------------------------------------
def _sha256(s: str) -> str:
    import hashlib
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _generate_manual_code() -> str:
    return f"{uuid4().int % 1_000_000:06d}"


def _ensure_dev_mode() -> None:
    if not settings.dev_bypass_auth:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "DEV_MODE_REQUIRED",
                "message": "Este endpoint só pode ser usado com VITE_DEV_BYPASS_AUTH=true. Veja 01_source/order_pickup_service/.env",
            },
        )


def _normalize_region(value: str) -> str:
    region = str(value or "").strip().upper()
    if region not in {"SP", "PT"}:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_REGION",
                "message": "region deve ser SP ou PT.",
            },
        )
    return region


def _validate_locker_region(*, region: str, locker_id: str) -> dict:
    locker = backend_client.get_locker_registry_item(locker_id)
    if not locker:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {locker_id}",
                "locker_id": locker_id,
            },
        )

    locker_region = str(locker.get("region") or "").strip().upper()
    if locker_region != region:
        raise HTTPException(
            status_code=409,
            detail={
                "type": "LOCKER_REGION_MISMATCH",
                "message": "O locker informado não pertence à região enviada.",
                "locker_id": locker_id,
                "payload_region": region,
                "locker_region": locker_region,
            },
        )

    return locker


def _resolve_effective_pickup_deadline(db: Session, *, order: Order) -> tuple[datetime | None, str | None]:
    deadline = getattr(order, "pickup_deadline_at", None)
    if deadline is not None:
        return deadline, "order.pickup_deadline_at"

    latest_pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )
    if latest_pickup and getattr(latest_pickup, "expires_at", None):
        return latest_pickup.expires_at, "pickup.expires_at"
    return None, None


def _assert_order_reconciliation_allowed(db: Session, *, order: Order) -> None:
    allowed_statuses = {
        OrderStatus.PAYMENT_PENDING,
        OrderStatus.FAILED,
        OrderStatus.CANCELLED,
        OrderStatus.EXPIRED,
        OrderStatus.EXPIRED_CREDIT_50,
    }
    if order.status in allowed_statuses:
        return

    if order.status == OrderStatus.PAID_PENDING_PICKUP:
        deadline, deadline_source = _resolve_effective_pickup_deadline(db, order=order)
        now = datetime.now(timezone.utc)

        if deadline is None:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "RECONCILIATION_NOT_ALLOWED",
                    "message": (
                        "Pedido em status PAID_PENDING_PICKUP sem deadline efetivo "
                        "(order/pickup) não pode ser reconciliado por segurança."
                    ),
                    "current_status": order.status.value,
                },
            )

        if getattr(deadline, "tzinfo", None) is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if deadline > now:
            raise HTTPException(
                status_code=409,
                detail={
                    "type": "RECONCILIATION_NOT_ALLOWED",
                    "message": (
                        "Pedido em status PAID_PENDING_PICKUP ainda dentro do prazo de retirada "
                        "não pode ser reconciliado."
                    ),
                    "current_status": order.status.value,
                    "effective_deadline_at": to_iso_utc(deadline),
                    "effective_deadline_source": deadline_source,
                },
            )
        return

    raise HTTPException(
        status_code=409,
        detail={
            "type": "RECONCILIATION_NOT_ALLOWED",
            "message": f"Pedido em status {order.status.value} não pode ser reconciliado.",
            "current_status": order.status.value,
        },
    )


@router.post("/reconcile-order", response_model=DevReconcileOrderOut)
def dev_reconcile_order(
    payload: DevReconcileOrderIn,
    db: Session = Depends(get_db),
):
    order_id = str(payload.order_id or "").strip()
    if not order_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "ORDER_ID_REQUIRED",
                "message": "order_id é obrigatório.",
            },
        )

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(
            status_code=404,
            detail={
                "type": "ORDER_NOT_FOUND",
                "message": "Pedido não encontrado.",
                "order_id": order_id,
            },
        )

    _assert_order_reconciliation_allowed(db, order=order)

    allocation = resolve_latest_allocation(db, order=order)
    pickup = resolve_latest_pickup(db, order=order)
    compensation = reconcile_order_compensation(
        db=db,
        order=order,
        allocation=allocation,
        pickup=pickup,
        cancel_reason="ops_order_reconciliation",
    )

    if order.status != OrderStatus.CANCELLED:
        order.mark_as_cancelled()
    else:
        order.touch()

    db.commit()

    return DevReconcileOrderOut(
        ok=True,
        order_id=order.id,
        status=order.status.value,
        message="Reconciliação operacional executada com sucesso.",
        compensation={
            "credit_restored": compensation.credit_restored,
            "slot_release_attempted": compensation.slot_release_attempted,
            "slot_release_ok": compensation.slot_release_ok,
            "slot_release_error": compensation.slot_release_error,
            "allocation_id": compensation.allocation_id,
            "allocation_state": compensation.allocation_state,
        },
    )


@router.post("/release-regional-allocations", response_model=DevReleaseRegionalAllocationsOut)
def dev_release_regional_allocations(
    payload: DevReleaseRegionalAllocationsIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    region = _normalize_region(payload.region)
    locker_id = str(payload.locker_id or "").strip()
    if not locker_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_ID_REQUIRED",
                "message": "locker_id é obrigatório.",
            },
        )

    _validate_locker_region(region=region, locker_id=locker_id)

    allocation_ids = [
        str(item or "").strip()
        for item in (payload.allocation_ids or [])
        if str(item or "").strip()
    ]

    if not allocation_ids and payload.auto_collect_from_local_db:
        allocations = (
            db.query(Allocation)
            .join(Order, Order.id == Allocation.order_id)
            .filter(
                Allocation.locker_id == locker_id,
                Order.region == region,
            )
            .order_by(Allocation.created_at.asc(), Allocation.id.asc())
            .all()
        )

        allocation_ids = list(dict.fromkeys([
            str(allocation.id).strip()
            for allocation in allocations
            if str(allocation.id or "").strip()
        ]))

    if not allocation_ids:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "ALLOCATION_IDS_REQUIRED",
                "message": (
                    "Informe ao menos um allocation_id para liberação regional "
                    "ou mantenha auto_collect_from_local_db=true com allocations locais existentes."
                ),
            },
        )

    results: list[dict[str, Any]] = []
    released_count = 0
    failed_count = 0

    for allocation_id in allocation_ids:
        try:
            response = backend_client.locker_release(
                region=region,
                allocation_id=allocation_id,
                locker_id=locker_id,
            )
            results.append(
                {
                    "allocation_id": allocation_id,
                    "ok": True,
                    "response": response,
                }
            )
            released_count += 1
        except Exception as exc:
            results.append(
                {
                    "allocation_id": allocation_id,
                    "ok": False,
                    "error": str(exc),
                }
            )
            failed_count += 1

    return DevReleaseRegionalAllocationsOut(
        ok=failed_count == 0,
        region=region,
        locker_id=locker_id,
        results=results,
        released_count=released_count,
        failed_count=failed_count,
        message=(
            "Liberação DEV das allocations regionais concluída. "
            "Use isso para limpar conflitos órfãos do backend regional."
        ),
    )


@router.post("/reset-locker", response_model=DevResetLockerOut)
def dev_reset_locker(
    payload: DevResetLockerIn,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    region = _normalize_region(payload.region)
    locker_id = str(payload.locker_id or "").strip()
    if not locker_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_ID_REQUIRED",
                "message": "locker_id é obrigatório.",
            },
        )

    locker = _validate_locker_region(region=region, locker_id=locker_id)
    slots_total = int(locker.get("slots") or 24)

    released_allocations: list[str] = []
    slot_reset_results: list[dict[str, Any]] = []

    allocations = (
        db.query(Allocation)
        .join(Order, Order.id == Allocation.order_id)
        .filter(
            Allocation.locker_id == locker_id,
            Order.region == region,
        )
        .order_by(Allocation.created_at.asc(), Allocation.id.asc())
        .all()
    )

    try:
        if payload.release_known_allocations_first:
            for allocation in allocations:
                try:
                    backend_client.locker_release(
                        region=region,
                        allocation_id=allocation.id,
                        locker_id=locker_id,
                    )

                    if not payload.purge_local_data:
                        allocation.mark_released()

                    released_allocations.append(allocation.id)
                except Exception as exc:
                    released_allocations.append(f"{allocation.id} (erro: {str(exc)})")

        if not payload.purge_local_data:
            db.flush()

        for slot in range(1, slots_total + 1):
            try:
                response = backend_client.locker_set_state(
                    region=region,
                    slot=slot,
                    state="AVAILABLE",
                    locker_id=locker_id,
                )
                slot_reset_results.append(
                    {
                        "slot": slot,
                        "ok": True,
                        "response": response,
                    }
                )
            except Exception as exc:
                slot_reset_results.append(
                    {
                        "slot": slot,
                        "ok": False,
                        "error": str(exc),
                    }
                )

        deleted_pickups = 0
        deleted_allocations = 0
        deleted_orders = 0

        if payload.purge_local_data:
            order_ids = [
                row[0]
                for row in db.query(Order.id)
                .filter(Order.totem_id == locker_id, Order.region == region)
                .all()
            ]

            if order_ids:
                deleted_pickups = (
                    db.query(Pickup)
                    .filter(Pickup.order_id.in_(order_ids))
                    .delete(synchronize_session=False)
                )

                deleted_allocations = (
                    db.query(Allocation)
                    .filter(Allocation.order_id.in_(order_ids))
                    .delete(synchronize_session=False)
                )

                deleted_orders = (
                    db.query(Order)
                    .filter(Order.id.in_(order_ids))
                    .delete(synchronize_session=False)
                )
            else:
                deleted_allocations = (
                    db.query(Allocation)
                    .filter(Allocation.locker_id == locker_id)
                    .delete(synchronize_session=False)
                )

        db.commit()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "type": "DEV_LOCKER_RESET_FAILED",
                "message": "Falha ao executar reset DEV do locker.",
                "region": region,
                "locker_id": locker_id,
                "error": str(exc),
            },
        ) from exc

    return DevResetLockerOut(
        ok=True,
        region=region,
        locker_id=locker_id,
        slots_total=slots_total,
        released_allocations=released_allocations,
        slot_reset_results=slot_reset_results,
        deleted_pickups=deleted_pickups,
        deleted_allocations=deleted_allocations,
        deleted_orders=deleted_orders,
        message=(
            "Reset DEV concluído. Todas as gavetas do locker foram forçadas para AVAILABLE "
            "e os dados locais foram removidos conforme solicitado. "
            "Para conflitos órfãos do backend regional, use também /dev-admin/release-regional-allocations."
        ),
    )

# 15/04/2026
@router.post("/simulate-online-payment-legacy-not-use")
def simulate_payment(
    order_id: str,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allocation = (
        db.query(Allocation)
        .filter(Allocation.order_id == order.id)
        .first()
    )
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    now = datetime.now(timezone.utc)

    if str(order.payment_status or "") != "APPROVED":
        order.payment_status = "APPROVED"
        order.status = "PAID_PENDING_PICKUP"
        order.paid_at = now
        order.payment_updated_at = now

    pickup = (
        db.query(Pickup)
        .filter(Pickup.order_id == order.id)
        .order_by(Pickup.created_at.desc(), Pickup.id.desc())
        .first()
    )

    if not pickup:
        pickup = Pickup(
            id=f"pk_{uuid4().hex}",
            order_id=order.id,
            channel=PickupChannel.ONLINE,
            region=order.region,
            locker_id=allocation.locker_id or order.totem_id,
            machine_id=order.totem_id,
            slot=allocation.slot,
            status=PickupStatus.ACTIVE,
            lifecycle_stage=PickupLifecycleStage.READY_FOR_PICKUP,
            activated_at=now,
            ready_at=now,
            # pickup_window_sec=7200,  # 2h - isso existe no conceito (lógica), mas no seu sistema o correto é: expires_at
            expires_at=now + timedelta(hours=2),
            created_at=now,
            updated_at=now,
        )
        db.add(pickup)
        db.flush()
    else:
        pickup.channel = PickupChannel.ONLINE
        pickup.region = order.region
        pickup.locker_id = allocation.locker_id or order.totem_id
        pickup.machine_id = order.totem_id
        pickup.slot = allocation.slot
        pickup.status = PickupStatus.ACTIVE
        pickup.lifecycle_stage = PickupLifecycleStage.READY_FOR_PICKUP
        pickup.activated_at = pickup.activated_at or now
        pickup.ready_at = pickup.ready_at or now
        pickup.expires_at = pickup.expires_at or (now + timedelta(hours=2))
        pickup.touch()
        db.flush()

    manual_code = _generate_manual_code()
    token_hash = _sha256(manual_code)

    tok = PickupToken(
        id=str(uuid4()),
        pickup_id=pickup.id,
        token_hash=token_hash,
        expires_at=pickup.expires_at.replace(tzinfo=None),
        used_at=None,
    )
    db.add(tok)
    db.flush()

    pickup.current_token_id = tok.id
    pickup.touch()

    db.commit()
    db.refresh(order)
    db.refresh(pickup)

    return {
        "message": "Pagamento simulado + pickup/token criados",
        "order_id": order.id,
        "pickup_id": pickup.id,
        "token_id": tok.id,
        "manual_code": manual_code,
        "status": order.status,
        "payment_status": order.payment_status,
        "locker_id": pickup.locker_id,
        "slot": pickup.slot,
        "expires_at": pickup.expires_at.isoformat() if pickup.expires_at else None,
    }


# 15/04/2026 - criada e funcional - foi substituída por 17/04/2026
@router.post("/simulate-online-payment")
def simulate_payment_legacy_funcional(
    order_id: str,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allocation = _ensure_allocation(db, order.id)

    now = datetime.now(timezone.utc)

    if str(order.payment_status or "") != "APPROVED":
        order.payment_status = "APPROVED"
        order.status = "PAID_PENDING_PICKUP"
        order.paid_at = now
        order.payment_updated_at = now

    deadline_utc = now + timedelta(hours=2)

    # pickup = _ensure_online_pickup(
    #     db,
    #     order=order,
    #     allocation=allocation,
    #     deadline_utc=deadline_utc,
    # )
    # 
    try:
        pickup = _ensure_online_pickup(
            db,
            order=order,
            allocation=allocation,
            deadline_utc=deadline_utc,
        )
    except Exception:
        try:
            backend_client.locker_release(
                order.region,
                allocation.id,
                locker_id=order.totem_id,
            )
        except Exception:
            logger.exception(
                "simulate_payment_release_after_pickup_setup_failed",
                extra={
                    "order_id": order.id,
                    "allocation_id": allocation.id,
                    "locker_id": order.totem_id,
                },
            )

        try:
            allocation.mark_released()
        except Exception:
            allocation.state = AllocationState.RELEASED

        order.status = OrderStatus.FAILED
        order.updated_at = datetime.now(timezone.utc)
        db.flush()
        db.commit()
        raise


    token_data = _create_pickup_token(
        db,
        pickup_id=pickup.id,
        expires_at_utc=deadline_utc,
    )

    pickup.current_token_id = token_data["token_id"]
    pickup.touch()

    logger.error(f"🔥 TOKEN CRIADO COM AES dev_admin - token_data={token_data}")


    db.commit()
    db.refresh(order)
    db.refresh(pickup)

    return {
        "message": "Pagamento simulado + pickup/token criados",
        "order_id": order.id,
        "pickup_id": pickup.id,
        "token_id": token_data["token_id"],
        "manual_code": token_data["manual_code"],
        "status": order.status,
        "payment_status": order.payment_status,
        "locker_id": pickup.locker_id,
        "slot": pickup.slot,
        "expires_at": pickup.expires_at.isoformat() if pickup.expires_at else None,
    }



# 17/04/2026 
@router.post("/simulate-online-payment")
def simulate_payment(
    order_id: str,
    db: Session = Depends(get_db),
):
    _ensure_dev_mode()

    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    allocation = _ensure_allocation(db, order.id)

    now = datetime.now(timezone.utc)

    # 🔥 1. Marca pagamento aprovado
    order.payment_status = "APPROVED"
    order.status = "PAID_PENDING_PICKUP"
    order.paid_at = now
    order.payment_updated_at = now

    # 🔥 2. EXECUTA PIPELINE REAL (ESSENCIAL)
    result = fulfill_payment_post_approval(
        db=db,
        order=order,
        allocation=allocation,
        pickup_window_hours=2,
    )

    pickup = result["pickup"]

    # 🔥 3. SINCRONIZA CAMPOS NA ORDER (CRÍTICO)
    order.slot = allocation.slot
    order.allocation_id = allocation.id
    order.allocation_expires_at = allocation.locked_until

    db.commit()
    db.refresh(order)
    db.refresh(pickup)

    return {
        "message": "Pagamento simulado (pipeline real executado)",
        "order_id": order.id,
        "pickup_id": pickup.id,
        "token_id": result.get("token_id"),
        "manual_code": result.get("manual_code"),
        "status": order.status,
        "payment_status": order.payment_status,
        "locker_id": pickup.locker_id,
        "slot": pickup.slot,
        "expires_at": pickup.expires_at.isoformat() if pickup.expires_at else None,
    }


