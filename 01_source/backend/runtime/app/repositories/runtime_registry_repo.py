# 01_source/backend/runtime/app/repositories/runtime_registry_repo.py
# 01_source/backend/runtime/app/repositories/runtime_registry_repo.py
from __future__ import annotations

import threading
import time
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor

from fastapi import HTTPException

from app.core.config import settings


_cache_lock = threading.Lock()
_cache: dict[str, dict[str, Any]] = {}


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


def _get_connection():
    dsn = str(settings.central_postgres_dsn or "").strip()
    if not dsn:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="CENTRAL_POSTGRES_DSN_REQUIRED",
                message="CENTRAL_POSTGRES_DSN is required for backend runtime.",
                retryable=False,
            ),
        )

    try:
        return psycopg2.connect(dsn, cursor_factory=RealDictCursor)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=_build_error(
                err_type="CENTRAL_DB_CONNECTION_FAILED",
                message="Failed to connect to central runtime registry database.",
                retryable=True,
                error=str(exc),
            ),
        ) from exc


def _read_runtime_locker_from_db(locker_id: str) -> dict[str, Any]:
    conn = _get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    locker_id,
                    machine_id,
                    display_name,
                    region,
                    country,
                    timezone,
                    operator_id,
                    temperature_zone,
                    security_level,
                    active,
                    runtime_enabled,
                    mqtt_region,
                    mqtt_locker_id,
                    topology_version,
                    slot_count_total
                FROM runtime_lockers
                WHERE locker_id = %s
                """,
                (locker_id,),
            )
            locker = cur.fetchone()

            if not locker:
                raise HTTPException(
                    status_code=404,
                    detail=_build_error(
                        err_type="LOCKER_NOT_FOUND",
                        message="Locker not found in runtime registry.",
                        retryable=False,
                        locker_id=locker_id,
                    ),
                )

            cur.execute(
                """
                SELECT
                    slot_number,
                    slot_size,
                    width_cm,
                    height_cm,
                    depth_cm,
                    max_weight_kg,
                    is_active
                FROM runtime_locker_slots
                WHERE locker_id = %s
                ORDER BY slot_number
                """,
                (locker_id,),
            )
            slot_rows = cur.fetchall()

            if not slot_rows:
                raise HTTPException(
                    status_code=503,
                    detail=_build_error(
                        err_type="LOCKER_SLOT_TOPOLOGY_NOT_FOUND",
                        message="Locker has no slot topology registered in runtime registry.",
                        retryable=False,
                        locker_id=locker_id,
                    ),
                )

            active_slots = [row for row in slot_rows if bool(row["is_active"])]
            if not active_slots:
                raise HTTPException(
                    status_code=503,
                    detail=_build_error(
                        err_type="LOCKER_WITHOUT_ACTIVE_SLOTS",
                        message="Locker has no active slots in runtime registry.",
                        retryable=False,
                        locker_id=locker_id,
                    ),
                )

            slot_ids = [int(row["slot_number"]) for row in active_slots]

            runtime_ctx = {
                "locker_id": str(locker["locker_id"]),
                "machine_id": str(locker["machine_id"]),
                "display_name": str(locker["display_name"]),
                "region": str(locker["region"]),
                "country": str(locker["country"]),
                "timezone": str(locker["timezone"]),
                "operator_id": locker["operator_id"],
                "temperature_zone": str(locker["temperature_zone"]),
                "security_level": str(locker["security_level"]),
                "active": bool(locker["active"]),
                "runtime_enabled": bool(locker["runtime_enabled"]),
                "mqtt_region": str(locker["mqtt_region"]),
                "mqtt_locker_id": str(locker["mqtt_locker_id"]),
                "topology_version": int(locker["topology_version"]),
                "slot_count_total": int(locker["slot_count_total"]),
                "slot_ids": slot_ids,
                "slots": [
                    {
                        "slot_number": int(row["slot_number"]),
                        "slot_size": str(row["slot_size"]),
                        "width_cm": row["width_cm"],
                        "height_cm": row["height_cm"],
                        "depth_cm": row["depth_cm"],
                        "max_weight_kg": float(row["max_weight_kg"]) if row["max_weight_kg"] is not None else None,
                        "is_active": bool(row["is_active"]),
                    }
                    for row in active_slots
                ],
            }

            if not runtime_ctx["active"]:
                raise HTTPException(
                    status_code=409,
                    detail=_build_error(
                        err_type="LOCKER_INACTIVE",
                        message="Locker exists but is inactive in runtime registry.",
                        retryable=False,
                        locker_id=locker_id,
                        region=runtime_ctx["region"],
                    ),
                )

            if not runtime_ctx["runtime_enabled"]:
                raise HTTPException(
                    status_code=409,
                    detail=_build_error(
                        err_type="LOCKER_RUNTIME_DISABLED",
                        message="Locker exists but runtime is disabled for this locker.",
                        retryable=False,
                        locker_id=locker_id,
                        region=runtime_ctx["region"],
                    ),
                )

            return runtime_ctx

    finally:
        conn.close()


def get_runtime_locker(locker_id: str) -> dict[str, Any]:
    locker_id = str(locker_id or "").strip()
    if not locker_id:
        raise HTTPException(
            status_code=400,
            detail=_build_error(
                err_type="LOCKER_ID_REQUIRED",
                message="locker_id is required.",
                retryable=False,
            ),
        )

    now = time.monotonic()
    ttl = int(settings.runtime_registry_cache_ttl_sec)

    with _cache_lock:
        cached = _cache.get(locker_id)
        if cached and cached["expires_at"] > now:
            return cached["data"]

    data = _read_runtime_locker_from_db(locker_id)

    with _cache_lock:
        _cache[locker_id] = {
            "data": data,
            "expires_at": now + ttl,
        }

    return data


def invalidate_runtime_locker_cache(locker_id: str | None = None) -> None:
    with _cache_lock:
        if locker_id:
            _cache.pop(str(locker_id).strip(), None)
        else:
            _cache.clear()