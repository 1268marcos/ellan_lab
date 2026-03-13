# 01_source/payment_gateway/app/routers/lockers.py
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.locker_registry import locker_registry

router = APIRouter(prefix="/lockers", tags=["lockers"])


@router.get("")
def list_lockers(region: str | None = Query(default=None)):
    """
    Lista lockers do registry central do gateway.

    Regras:
    - sem region: retorna todos
    - com region: retorna apenas lockers da região informada
    """
    if region:
        normalized_region = str(region or "").strip().upper()
        if normalized_region not in {"SP", "PT"}:
            raise HTTPException(
                status_code=400,
                detail={
                    "type": "INVALID_REGION",
                    "message": "region deve ser SP ou PT.",
                    "region": region,
                },
            )

        items = locker_registry.list_public_summaries_by_region(normalized_region)
        return {
            "items": items,
            "total": len(items),
            "region": normalized_region,
        }

    items = locker_registry.all_public_summaries()
    return {
        "items": items,
        "total": len(items),
    }


@router.get("/{locker_id}")
def get_locker(locker_id: str):
    """
    Retorna um locker específico do registry central.
    """
    normalized_locker_id = str(locker_id or "").strip()
    if not normalized_locker_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_ID_REQUIRED",
                "message": "locker_id é obrigatório.",
            },
        )

    if not locker_registry.exists(normalized_locker_id):
        raise HTTPException(
            status_code=404,
            detail={
                "type": "LOCKER_NOT_FOUND",
                "message": f"Locker não encontrado: {normalized_locker_id}",
                "locker_id": normalized_locker_id,
            },
        )

    return locker_registry.get_public_summary(normalized_locker_id)