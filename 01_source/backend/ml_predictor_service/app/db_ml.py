"""TimescaleDB/Postgres connection and parameterized ML feature refresh."""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg2
import psycopg2.extensions

# libpq URL or discrete envs
DSN_ENV = "ML_DATABASE_URL"


def _dsn() -> str:
    u = os.environ.get(DSN_ENV) or os.environ.get("DATABASE_URL")
    if not u:
        raise RuntimeError(f"Set {DSN_ENV} or DATABASE_URL")
    return u


@contextmanager
def ml_connection() -> Iterator[psycopg2.extensions.connection]:
    conn = psycopg2.connect(_dsn())
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def refresh_mat_view(conn: psycopg2.extensions.connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "REFRESH MATERIALIZED VIEW CONCURRENTLY public.ml_features_daily_mv"
        )


def refresh_features_70d(
    conn: psycopg2.extensions.connection, d0: str, d1: str
) -> int:
    """Calls DB function refresh_ml_features_daily_70d (bound params, no string SQL)."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT public.refresh_ml_features_daily_70d(%s::date, %s::date)",
            (d0, d1),
        )
        row = cur.fetchone()
    return int(row[0]) if row and row[0] is not None else 0


def upsert_ml_features_daily_row(
    conn: psycopg2.extensions.connection,
    locker_id: str,
    feature_date: str,
    temperature_mean: float | None,
    humidity_mean: float | None,
    battery_min: float | None,
) -> None:
    """Narrow upsert for same-day aggregates when telemetry is ingested out-of-band."""
    stmt = """
    INSERT INTO public.ml_features_daily (
      locker_id, feature_date, temperature_mean, humidity_mean, battery_min,
      door_failures_7d, usage_events_7d, uptime_hours_7d, failure_label_7d
    ) VALUES (
      %s, %s::date, %s, %s, %s, 0, 0, 0, 0
    )
    ON CONFLICT (locker_id, feature_date) DO UPDATE SET
      temperature_mean = COALESCE(EXCLUDED.temperature_mean, ml_features_daily.temperature_mean),
      humidity_mean = COALESCE(EXCLUDED.humidity_mean, ml_features_daily.humidity_mean),
      battery_min = COALESCE(EXCLUDED.battery_min, ml_features_daily.battery_min)
    """
    with conn.cursor() as cur:
        cur.execute(
            stmt,
            (locker_id, feature_date, temperature_mean, humidity_mean, battery_min),
        )
