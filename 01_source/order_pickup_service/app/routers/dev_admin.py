# 01_source/order_pickup_service/app/routers/dev_admin.py
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.allocation import Allocation
from app.models.order import Order
from app.models.pickup import Pickup
from app.schemas.dev_admin import (
    DevReleaseRegionalAllocationsIn,
    DevReleaseRegionalAllocationsOut,
    DevResetLockerIn,
    DevResetLockerOut,
)
from app.services import backend_client

router = APIRouter(prefix="/dev-admin", tags=["dev-admin"])


def _ensure_dev_mode() -> None:
    dev_bypass = os.getenv("DEV_BYPASS_AUTH", "false").lower() == "true"
    if not dev_bypass:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "DEV_MODE_REQUIRED",
                "message": "Este endpoint só pode ser usado com DEV_BYPASS_AUTH=true.",
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

    if not allocation_ids:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "ALLOCATION_IDS_REQUIRED",
                "message": "Informe ao menos um allocation_id para liberação regional.",
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