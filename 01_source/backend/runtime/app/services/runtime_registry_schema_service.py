# 01_source/backend/runtime/app/services/runtime_registry_schema_service.py
from __future__ import annotations

import psycopg2
from fastapi import HTTPException

from app.core.config import settings


RUNTIME_REGISTRY_SQL = """
BEGIN;

CREATE TABLE IF NOT EXISTS runtime_lockers (
    locker_id               VARCHAR(120) PRIMARY KEY,
    machine_id              VARCHAR(120) NOT NULL UNIQUE,
    display_name            VARCHAR(255) NOT NULL,
    region                  VARCHAR(16) NOT NULL,
    country                 VARCHAR(8) NOT NULL,
    timezone                VARCHAR(64) NOT NULL,
    operator_id             VARCHAR(120),
    temperature_zone        VARCHAR(32) NOT NULL DEFAULT 'AMBIENT',
    security_level          VARCHAR(32) NOT NULL DEFAULT 'STANDARD',

    active                  BOOLEAN NOT NULL DEFAULT TRUE,
    runtime_enabled         BOOLEAN NOT NULL DEFAULT TRUE,

    mqtt_region             VARCHAR(32) NOT NULL,
    mqtt_locker_id          VARCHAR(120) NOT NULL,

    topology_version        INTEGER NOT NULL DEFAULT 1,
    slot_count_total        INTEGER NOT NULL,

    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_runtime_lockers_region
    ON runtime_lockers(region);

CREATE INDEX IF NOT EXISTS idx_runtime_lockers_active
    ON runtime_lockers(active, runtime_enabled);

CREATE TABLE IF NOT EXISTS runtime_locker_slots (
    locker_id               VARCHAR(120) NOT NULL REFERENCES runtime_lockers(locker_id) ON DELETE CASCADE,
    slot_number             INTEGER NOT NULL,
    slot_size               VARCHAR(16) NOT NULL,
    width_cm                INTEGER,
    height_cm               INTEGER,
    depth_cm                INTEGER,
    max_weight_kg           NUMERIC(10, 3),
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMP NOT NULL DEFAULT NOW(),

    PRIMARY KEY (locker_id, slot_number)
);

CREATE INDEX IF NOT EXISTS idx_runtime_locker_slots_active
    ON runtime_locker_slots(locker_id, is_active, slot_number);

CREATE TABLE IF NOT EXISTS runtime_locker_features (
    locker_id                       VARCHAR(120) PRIMARY KEY REFERENCES runtime_lockers(locker_id) ON DELETE CASCADE,
    supports_online                 BOOLEAN NOT NULL DEFAULT TRUE,
    supports_kiosk                  BOOLEAN NOT NULL DEFAULT TRUE,
    supports_pickup_qr              BOOLEAN NOT NULL DEFAULT TRUE,
    supports_manual_code            BOOLEAN NOT NULL DEFAULT TRUE,
    supports_open_command           BOOLEAN NOT NULL DEFAULT TRUE,
    supports_light_command          BOOLEAN NOT NULL DEFAULT TRUE,
    supports_paid_pending_pickup    BOOLEAN NOT NULL DEFAULT TRUE,
    supports_refrigerated_items     BOOLEAN NOT NULL DEFAULT FALSE,
    supports_frozen_items           BOOLEAN NOT NULL DEFAULT FALSE,
    supports_high_value_items       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMIT;
"""


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
        return psycopg2.connect(dsn)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=_build_error(
                err_type="CENTRAL_DB_CONNECTION_FAILED",
                message="Failed to connect to central Postgres for runtime schema bootstrap.",
                retryable=True,
                error=str(exc),
            ),
        ) from exc


def ensure_runtime_registry_schema() -> dict:
    conn = _get_connection()

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(RUNTIME_REGISTRY_SQL)

        return {
            "ok": True,
            "message": "Runtime registry schema ensured successfully.",
            "schema_objects": [
                "runtime_lockers",
                "runtime_locker_slots",
                "runtime_locker_features",
            ],
        }

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="RUNTIME_SCHEMA_BOOTSTRAP_FAILED",
                message="Failed to apply runtime registry schema bootstrap.",
                retryable=True,
                error=str(exc),
            ),
        ) from exc
    finally:
        conn.close()