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

from __future__ import annotations

import json
import os

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


def _default_machine_id() -> str:
    return os.getenv("MACHINE_ID", "CACIFO-SP-001")


def _parse_slot_ids_json(raw: str | None) -> list[int] | None:
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="INVALID_SLOT_IDS_JSON",
                message="SLOT_IDS_JSON is not valid JSON.",
                retryable=False,
                raw_value=raw,
                error=str(exc),
            ),
        ) from exc

    if not isinstance(data, list):
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="INVALID_SLOT_IDS_JSON_TYPE",
                message="SLOT_IDS_JSON must be a JSON array of integers.",
                retryable=False,
                parsed_type=type(data).__name__,
            ),
        )

    slot_ids: list[int] = []
    for item in data:
        try:
            slot_ids.append(int(item))
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="INVALID_SLOT_ID_VALUE",
                    message="All SLOT_IDS_JSON values must be integers.",
                    retryable=False,
                    bad_value=item,
                    error=str(exc),
                ),
            ) from exc

    return sorted(set(slot_ids))


def resolve_runtime_locker(x_locker_id: str | None) -> dict:
    """
    Resolver inicial do runtime multi-locker.

    Regra atual:
    1. Usa X-Locker-Id como identidade principal.
    2. Fallback legado: MACHINE_ID.
    3. Topologia:
       - SLOT_IDS_JSON, se existir
       - senão LOCKER_SLOT_COUNT
       - senão fallback legado 24
    """
    locker_id = (x_locker_id or "").strip()
    if not locker_id:
        locker_id = _default_machine_id()

    if not locker_id:
        raise HTTPException(
            status_code=400,
            detail=_build_error(
                err_type="LOCKER_ID_REQUIRED",
                message="X-Locker-Id is required.",
                retryable=False,
            ),
        )

    env_slot_ids = _parse_slot_ids_json(os.getenv("SLOT_IDS_JSON"))

    if env_slot_ids:
        slot_ids = env_slot_ids
    else:
        slot_count_raw = os.getenv("LOCKER_SLOT_COUNT", "24")
        try:
            slot_count = int(slot_count_raw)
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="INVALID_LOCKER_SLOT_COUNT",
                    message="LOCKER_SLOT_COUNT must be an integer.",
                    retryable=False,
                    raw_value=slot_count_raw,
                    error=str(exc),
                ),
            ) from exc

        if slot_count <= 0:
            raise HTTPException(
                status_code=500,
                detail=_build_error(
                    err_type="INVALID_LOCKER_SLOT_COUNT",
                    message="LOCKER_SLOT_COUNT must be greater than zero.",
                    retryable=False,
                    slot_count=slot_count,
                ),
            )

        slot_ids = list(range(1, slot_count + 1))

    region = locker_id.split("-")[0] if "-" in locker_id else "UNKNOWN"

    return {
        "locker_id": locker_id,
        "machine_id": locker_id,
        "region": region,
        "country": "UNKNOWN",
        "timezone": os.getenv("TZ", "UTC"),
        "slot_ids": slot_ids,
        "slot_count_total": len(slot_ids),
    }