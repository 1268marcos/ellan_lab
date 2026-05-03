"""Inferência com modelo ACTIVE mais recente."""
from __future__ import annotations

import json
import os
from typing import Any

import numpy as np
import psycopg2.extensions

from app.db_ml import ml_connection
from app.model_training.save_model import load_model_from_disk

FEATURE_COLS = (
    "temperature_avg_70d",
    "humidity_avg_70d",
    "battery_min_70d",
    "door_failures_70d",
    "usage_events_70d",
    "uptime_hours_70d",
)

_PREDICT_SQL = """
SELECT m.temperature_avg_70d, m.humidity_avg_70d, m.battery_min_70d,
       m.door_failures_70d, m.usage_events_70d, m.uptime_hours_70d
FROM public.ml_features_daily m
WHERE m.locker_id = %s
ORDER BY m.feature_date DESC
LIMIT 1
"""
_ACTIVE_SQL = """
SELECT model_version, metrics_json::text
FROM public.ml_model_metadata
WHERE status = 'ACTIVE'
ORDER BY trained_at DESC
LIMIT 1
"""
_LOG_SQL = """
INSERT INTO public.ml_predictions_log
  (locker_id, failure_probability, health_score, model_version)
VALUES (%s, %s, %s, %s)
"""


def _active_model(conn: psycopg2.extensions.connection) -> tuple[str, dict | None]:
    with conn.cursor() as cur:
        cur.execute(_ACTIVE_SQL)
        row = cur.fetchone()
    if not row:
        raise RuntimeError("Nenhum modelo ACTIVE em ml_model_metadata")
    mj = json.loads(row[1]) if row[1] else None
    return str(row[0]), mj


def _row_to_x(row: tuple[Any, ...]) -> np.ndarray:
    def f(i: int) -> float:
        v = row[i]
        return float(v) if v is not None else 0.0

    return np.array([[f(i) for i in range(len(FEATURE_COLS))]], dtype=np.float64)


def predict_failure(
    locker_id: str,
    *,
    conn: psycopg2.extensions.connection | None = None,
    model_dir: str | None = None,
    skip_log: bool = False,
) -> tuple[float, float, str]:
    """
    Última linha de features → (failure_probability, health_score, model_version).
    Regista em ml_predictions_log (commit automático se conn não for passado).
    """
    mdir = model_dir or os.environ.get("ML_MODEL_DIR")

    def _run(c: psycopg2.extensions.connection) -> tuple[float, float, str]:
        ver, mj = _active_model(c)
        model = load_model_from_disk(ver, mj, mdir)
        with c.cursor() as cur:
            cur.execute(_PREDICT_SQL, (locker_id,))
            frow = cur.fetchone()
        if not frow or any(x is None for x in frow):
            raise ValueError(f"Sem features completas para locker_id={locker_id}")
        X = _row_to_x(frow)
        pr = model.predict_proba(X)[0]
        cl = np.asarray(getattr(model, "classes_", np.arange(len(pr))))
        if not np.any(cl == 1):
            raise RuntimeError("Modelo sem classe 1 (falha)")
        pos = int(np.flatnonzero(cl == 1)[0])
        proba = float(pr[pos])
        health = round((1.0 - proba) * 100.0, 2)
        if not skip_log:
            with c.cursor() as cur:
                cur.execute(_LOG_SQL, (locker_id, proba, health, ver))
        return proba, health, ver

    if conn is not None:
        return _run(conn)
    with ml_connection() as c:
        return _run(c)
