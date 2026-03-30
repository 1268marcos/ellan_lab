# 01_source/backend/runtime/app/core/locker_runtime_resolver.py
"""
Esse arquivo é importante - Responsável por resolver, por request, a partir do X-Locker-Id:
locker_id, region, country, timezone, machine_id físico/lógico, 
topologia de slots, parâmetros MQTT, configuração operacional necessária

Esse arquivo vira o coração da identidade multi-locker.

Responsabilidade

Receber X-Locker-Id e devolver um objeto resolvido com:

{
  "locker_id": "...",
  "machine_id": "...",
  "region": "...",
  "country": "...",
  "timezone": "...",
  "mqtt_region": "...",
  "mqtt_locker_id": "...",
  "slot_count_total": ...,
  "slot_map": [...],
}

"""

from fastapi import HTTPException


def resolve_runtime_locker(x_locker_id: str | None) -> dict:
    locker_id = (x_locker_id or "").strip()
    if not locker_id:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "LOCKER_ID_REQUIRED",
                "message": "X-Locker-Id is required",
                "retryable": False,
            },
        )

    # Stub inicial.
    # Depois este resolver deve consultar a fonte central real.
    return {
        "locker_id": locker_id,
        "machine_id": locker_id,
        "region": locker_id.split("-")[0] if "-" in locker_id else "UNKNOWN",
        "country": "UNKNOWN",
        "timezone": "UTC",
        "slot_count_total": 24,
        "slot_ids": list(range(1, 25)),
    }
