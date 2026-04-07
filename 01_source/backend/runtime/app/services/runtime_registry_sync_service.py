# 01_source/backend/runtime/app/services/runtime_registry_sync_service.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
import psycopg2
from psycopg2.extras import RealDictCursor

from fastapi import HTTPException

from app.core.config import settings


SLOT_SIZE_ORDER = {
    "P": 10,
    "M": 20,
    "G": 30,
    "XG": 40,
}


@dataclass
class CentralLockerRow:
    locker_id: str
    display_name: str
    region: str
    country: str
    timezone: str
    operator_id: str | None
    temperature_zone: str
    security_level: str
    active: bool


@dataclass
class CentralSlotConfigRow:
    locker_id: str
    slot_size: str
    slot_count: int
    width_cm: int | None
    height_cm: int | None
    depth_cm: int | None
    max_weight_kg: float | None


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
                message="CENTRAL_POSTGRES_DSN is required.",
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
                message="Failed to connect to central Postgres.",
                retryable=True,
                error=str(exc),
            ),
        ) from exc


def _fetch_central_lockers(conn, locker_id: str | None = None) -> list[CentralLockerRow]:
    where_sql = ""
    params: list[Any] = []

    if locker_id:
        where_sql = "WHERE l.id = %s"
        params.append(locker_id)

    sql = f"""
        SELECT
            l.id AS locker_id,
            l.display_name,
            l.region,
            l.country,
            l.timezone,
            l.operator_id,
            l.temperature_zone,
            l.security_level,
            l.active
        FROM lockers l
        {where_sql}
        ORDER BY l.id
    """

    with conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        CentralLockerRow(
            locker_id=str(row["locker_id"]),
            display_name=str(row["display_name"]),
            region=str(row["region"]),
            country=str(row["country"]),
            timezone=str(row["timezone"]),
            operator_id=row["operator_id"],
            temperature_zone=str(row["temperature_zone"]),
            security_level=str(row["security_level"]),
            active=bool(row["active"]),
        )
        for row in rows
    ]


def _fetch_central_slot_configs(
    conn,
    locker_ids: list[str],
) -> list[CentralSlotConfigRow]:
    if not locker_ids:
        return []

    sql = """
        SELECT
            sc.locker_id,
            sc.slot_size,
            sc.slot_count,
            sc.width_cm,
            sc.height_cm,
            sc.depth_cm,
            sc.max_weight_kg
        FROM locker_slot_configs sc
        WHERE sc.locker_id = ANY(%s)
        ORDER BY
            sc.locker_id,
            CASE sc.slot_size
                WHEN 'P' THEN 10
                WHEN 'M' THEN 20
                WHEN 'G' THEN 30
                WHEN 'XG' THEN 40
                ELSE 999
            END,
            sc.slot_size
    """

    with conn.cursor() as cur:
        cur.execute(sql, (locker_ids,))
        rows = cur.fetchall()

    out: list[CentralSlotConfigRow] = []
    for row in rows:
        slot_count = int(row["slot_count"])
        if slot_count <= 0:
            continue

        out.append(
            CentralSlotConfigRow(
                locker_id=str(row["locker_id"]),
                slot_size=str(row["slot_size"]),
                slot_count=slot_count,
                width_cm=row["width_cm"],
                height_cm=row["height_cm"],
                depth_cm=row["depth_cm"],
                max_weight_kg=float(row["max_weight_kg"]) if row["max_weight_kg"] is not None else None,
            )
        )
    return out


def _fetch_central_payment_methods(
    conn,
    locker_ids: list[str],
) -> dict[str, list[str]]:
    if not locker_ids:
        return {}

    sql = """
        SELECT
            pm.locker_id,
            pm.method
        FROM locker_payment_methods pm
        WHERE pm.locker_id = ANY(%s)
          AND pm.is_active = TRUE
        ORDER BY pm.locker_id, pm.method
    """

    with conn.cursor() as cur:
        cur.execute(sql, (locker_ids,))
        rows = cur.fetchall()

    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(str(row["locker_id"]), []).append(str(row["method"]))

    return grouped


def _group_slot_configs_by_locker(
    slot_configs: list[CentralSlotConfigRow],
) -> dict[str, list[CentralSlotConfigRow]]:
    grouped: dict[str, list[CentralSlotConfigRow]] = {}
    for row in slot_configs:
        grouped.setdefault(row.locker_id, []).append(row)
    return grouped


def _expand_concrete_slots(
    slot_configs: list[CentralSlotConfigRow],
) -> list[dict[str, Any]]:
    """
    Expande:
      P x 8, M x 8, G x 6...
    em slots concretos:
      1..N

    Regra atual:
    - numeração sequencial por ordem de tamanho P, M, G, XG
    - se no futuro existir necessidade física exata por gaveta,
      o modelo pode evoluir para tabela explícita de slots.
    """
    ordered = sorted(
        slot_configs,
        key=lambda x: (
            SLOT_SIZE_ORDER.get(x.slot_size, 999),
            x.slot_size,
        ),
    )

    concrete_slots: list[dict[str, Any]] = []
    next_slot = 1

    for cfg in ordered:
        for _ in range(cfg.slot_count):
            concrete_slots.append(
                {
                    "slot_number": next_slot,
                    "slot_size": cfg.slot_size,
                    "width_cm": cfg.width_cm,
                    "height_cm": cfg.height_cm,
                    "depth_cm": cfg.depth_cm,
                    "max_weight_kg": cfg.max_weight_kg,
                    "is_active": True,
                }
            )
            next_slot += 1

    return concrete_slots


def _upsert_runtime_locker(
    conn,
    *,
    locker: CentralLockerRow,
    slot_count_total: int,
    payment_methods: list[str],
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO runtime_lockers (
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
                slot_count_total,
                payment_methods_json
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (locker_id)
            DO UPDATE SET
                machine_id = EXCLUDED.machine_id,
                display_name = EXCLUDED.display_name,
                region = EXCLUDED.region,
                country = EXCLUDED.country,
                timezone = EXCLUDED.timezone,
                operator_id = EXCLUDED.operator_id,
                temperature_zone = EXCLUDED.temperature_zone,
                security_level = EXCLUDED.security_level,
                active = EXCLUDED.active,
                runtime_enabled = EXCLUDED.runtime_enabled,
                mqtt_region = EXCLUDED.mqtt_region,
                mqtt_locker_id = EXCLUDED.mqtt_locker_id,
                topology_version = runtime_lockers.topology_version + 1,
                slot_count_total = EXCLUDED.slot_count_total,
                payment_methods_json = EXCLUDED.payment_methods_json,
                updated_at = NOW()
            """,
            (
                locker.locker_id,
                locker.locker_id,          # machine_id
                locker.display_name,
                locker.region,
                locker.country,
                locker.timezone,
                locker.operator_id,
                locker.temperature_zone,
                locker.security_level,
                locker.active,
                True,                      # runtime_enabled
                locker.region,             # mqtt_region
                locker.locker_id,          # mqtt_locker_id
                1,
                slot_count_total,
                json.dumps(payment_methods),
            ),
        )


def _replace_runtime_locker_slots(
    conn,
    *,
    locker_id: str,
    concrete_slots: list[dict[str, Any]],
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM runtime_locker_slots WHERE locker_id = %s",
            (locker_id,),
        )

        for slot in concrete_slots:
            cur.execute(
                """
                INSERT INTO runtime_locker_slots (
                    locker_id,
                    slot_number,
                    slot_size,
                    width_cm,
                    height_cm,
                    depth_cm,
                    max_weight_kg,
                    is_active
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    locker_id,
                    int(slot["slot_number"]),
                    str(slot["slot_size"]),
                    slot["width_cm"],
                    slot["height_cm"],
                    slot["depth_cm"],
                    slot["max_weight_kg"],
                    bool(slot["is_active"]),
                ),
            )


def sync_runtime_registry_from_central(
    *,
    locker_id: str | None = None,
    prune_missing: bool = False,
) -> dict[str, Any]:
    conn = _get_connection()

    try:
        with conn:
            central_lockers = _fetch_central_lockers(conn, locker_id=locker_id)

            if locker_id and not central_lockers:
                raise HTTPException(
                    status_code=404,
                    detail=_build_error(
                        err_type="LOCKER_NOT_FOUND_IN_CENTRAL_SOURCE",
                        message="Locker not found in central source tables.",
                        retryable=False,
                        locker_id=locker_id,
                    ),
                )

            if not central_lockers:
                return {
                    "ok": True,
                    "message": "No lockers found in central source.",
                    "sync_scope": "all",
                    "lockers_processed": 0,
                    "slots_generated": 0,
                    "prune_missing": prune_missing,
                }

            locker_ids = [item.locker_id for item in central_lockers]
            slot_configs = _fetch_central_slot_configs(conn, locker_ids)
            slot_cfg_by_locker = _group_slot_configs_by_locker(slot_configs)

            payment_methods_by_locker = _fetch_central_payment_methods(conn, locker_ids)

            lockers_processed = 0
            slots_generated_total = 0
            sync_details: list[dict[str, Any]] = []

            for locker in central_lockers:
                configs = slot_cfg_by_locker.get(locker.locker_id, [])
                if not configs:
                    raise HTTPException(
                        status_code=503,
                        detail=_build_error(
                            err_type="LOCKER_WITHOUT_SLOT_CONFIG",
                            message="Locker has no slot configuration in central source.",
                            retryable=False,
                            locker_id=locker.locker_id,
                        ),
                    )

                concrete_slots = _expand_concrete_slots(configs)
                slot_count_total = len(concrete_slots)

                if slot_count_total <= 0:
                    raise HTTPException(
                        status_code=503,
                        detail=_build_error(
                            err_type="LOCKER_WITHOUT_CONCRETE_SLOTS",
                            message="Locker generated zero concrete slots during sync.",
                            retryable=False,
                            locker_id=locker.locker_id,
                        ),
                    )

                payment_methods = payment_methods_by_locker.get(locker.locker_id, [])

                _upsert_runtime_locker(
                    conn,
                    locker=locker,
                    slot_count_total=slot_count_total,
                    payment_methods=payment_methods,
                )

                _replace_runtime_locker_slots(
                    conn,
                    locker_id=locker.locker_id,
                    concrete_slots=concrete_slots,
                )

                lockers_processed += 1
                slots_generated_total += slot_count_total

                sync_details.append(
                    {
                        "locker_id": locker.locker_id,
                        "region": locker.region,
                        "country": locker.country,
                        "active": locker.active,
                        "payment_methods": payment_methods,
                        "slot_count_total": slot_count_total,
                        "slot_sizes": [
                            {
                                "slot_size": cfg.slot_size,
                                "slot_count": cfg.slot_count,
                            }
                            for cfg in configs
                        ],
                    }
                )

            if prune_missing and not locker_id:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM runtime_lockers
                        WHERE locker_id NOT IN (
                            SELECT id FROM lockers
                        )
                        """
                    )

            return {
                "ok": True,
                "message": "Runtime registry synchronized successfully from central source.",
                "sync_scope": locker_id if locker_id else "all",
                "lockers_processed": lockers_processed,
                "slots_generated": slots_generated_total,
                "prune_missing": prune_missing,
                "details": sync_details,
            }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="RUNTIME_REGISTRY_SYNC_FAILED",
                message="Unexpected failure during runtime registry synchronization.",
                retryable=True,
                locker_id=locker_id,
                prune_missing=prune_missing,
                error=str(exc),
            ),
        ) from exc
    finally:
        conn.close()