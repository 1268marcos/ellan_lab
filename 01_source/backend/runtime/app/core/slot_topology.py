# 01_source/backend/runtime/app/core/slot_topology.py

from __future__ import annotations

"""
Responsabilidade

Calcular slots válidos por locker a partir de:

slot_configs
slots válidos
soma de slot_count
mapa físico por tamanho (P/M/G/XG) - tamanhos por slot
mapeamento lógico do locker
"""


from fastapi import HTTPException


def _build_error(
    *,
    err_type: str,
    message: str,
    retryable: bool,
    **extra,
) -> dict:
    detail = {
        "type": err_type,
        "message": message,
        "retryable": retryable,
    }
    if extra:
        detail.update(extra)
    return detail


def get_valid_slot_ids(locker_ctx: dict) -> list[int]:
    # return list(locker_ctx.get("slot_ids", []))

    slot_ids = locker_ctx.get("slot_ids") or []

    try:
        normalized = sorted({int(x) for x in slot_ids})
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="INVALID_LOCKER_SLOT_TOPOLOGY",
                message="Locker topology contains invalid slot ids.",
                retryable=False,
                locker_id=locker_ctx.get("locker_id"),
                error=str(exc),
            ),
        ) from exc

    if not normalized:
        raise HTTPException(
            status_code=503,
            detail=_build_error(
                err_type="LOCKER_WITHOUT_SLOTS",
                message="Locker has no valid slots.",
                retryable=False,
                locker_id=locker_ctx.get("locker_id"),
            ),
        )

    return normalized


def get_slot_metadata(locker_ctx: dict, slot: int) -> dict:
    slots = locker_ctx.get("slots") or []
    for item in slots:
        if int(item["slot_number"]) == int(slot):
            return item

    raise HTTPException(
        status_code=400,
        detail=_build_error(
            err_type="INVALID_SLOT_FOR_LOCKER",
            message="Slot is not present in locker topology.",
            retryable=False,
            locker_id=locker_ctx.get("locker_id"),
            slot=int(slot),
            valid_slots=get_valid_slot_ids(locker_ctx),
        ),
    )


def ensure_valid_slot(locker_ctx: dict, slot: int) -> None:
    get_slot_metadata(locker_ctx, slot)



"""
def ensure_valid_slot(locker_ctx: dict, slot: int) -> None:
    valid_slots = set(get_valid_slot_ids(locker_ctx))
    if slot not in valid_slots:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_SLOT",
                "message": "slot is not valid for this locker",
                "retryable": False,
                "slot": slot,
                "locker_id": locker_ctx.get("locker_id"),
                "valid_slots": sorted(valid_slots),
            },
        )
"""
