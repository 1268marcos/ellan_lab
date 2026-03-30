# 01_source/backend/runtime/app/core/slot_topology.py
"""
Responsabilidade

Calcular slots válidos por locker a partir de:

slot_configs
slots válidos
soma de slot_count
mapa físico por tamanho (P/M/G/XG) - tamanhos por slot
mapeamento lógico do locker
"""

def get_valid_slot_ids(locker_ctx: dict) -> list[int]:
    return list(locker_ctx.get("slot_ids", []))


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