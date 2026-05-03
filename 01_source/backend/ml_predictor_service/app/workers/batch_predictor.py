"""Predição em lote e incremental para ml_predictions_log."""
from __future__ import annotations

import logging
import time
from typing import Any

import psycopg2.extensions

from app.config import settings
from app.db_ml import ml_connection
from app.model_inference.predict import load_active_model_bundle, predict_from_values

logger = logging.getLogger(__name__)

COMMIT_EVERY = settings.predict_commit_batch_size

_ACTIVE_LOCKERS = """
SELECT id::text FROM lockers
WHERE COALESCE(active, true) = true
ORDER BY id
"""
# _LATEST_FEATURES = """
# SELECT temperature_avg_70d, humidity_avg_70d, battery_min_70d,
#        door_failures_70d, usage_events_70d, uptime_hours_70d
# FROM ml_features_daily
# WHERE locker_id = %s
# ORDER BY feature_date DESC
# LIMIT 1
# """
_LATEST_FEATURES = """
SELECT temperature_mean, humidity_mean, battery_min,
       door_failures_7d, usage_events_7d, uptime_hours_7d
FROM ml_features_daily
WHERE locker_id = %s
  AND temperature_mean IS NOT NULL
ORDER BY feature_date DESC
LIMIT 1
"""


_GLOBAL_MEANS = """
SELECT
  AVG(temperature_avg_70d)::float,
  AVG(humidity_avg_70d)::float,
  AVG(battery_min_70d)::float,
  AVG(door_failures_70d::double precision)::float,
  AVG(usage_events_70d::double precision)::float,
  AVG(uptime_hours_70d)::float
FROM ml_features_daily
WHERE feature_date >= (CURRENT_DATE - INTERVAL '90 days')
  AND temperature_avg_70d IS NOT NULL
  AND humidity_avg_70d IS NOT NULL
  AND battery_min_70d IS NOT NULL
  AND door_failures_70d IS NOT NULL
  AND usage_events_70d IS NOT NULL
  AND uptime_hours_70d IS NOT NULL
"""
_RECENT_TELEMETRY_LOCKERS = """
SELECT DISTINCT t.locker_id::text
FROM locker_telemetry t
INNER JOIN lockers l ON l.id = t.locker_id AND COALESCE(l.active, true) = true
WHERE t.occurred_at >= (NOW() AT TIME ZONE 'UTC' - INTERVAL '24 hours')
ORDER BY 1
"""


def _fetch_global_means(cur: Any) -> tuple[float, float, float, float, float, float] | None:
    cur.execute(_GLOBAL_MEANS)
    row = cur.fetchone()
    if not row or any(x is None for x in row):
        return None
    return tuple(float(x) for x in row)


def _resolve_features(
    raw: tuple | None,
    global_means: tuple[float, float, float, float, float, float] | None,
) -> tuple[float, float, float, float, float, float] | None:
    if raw is None:
        if global_means is None:
            return None
        return global_means
    out: list[float] = []
    for i in range(6):
        v = raw[i]
        if v is not None:
            out.append(float(v))
        elif global_means is not None and global_means[i] is not None:
            out.append(float(global_means[i]))
        else:
            return None
    return tuple(out)


def _predict_one(
    conn: psycopg2.extensions.connection,
    cur: Any,
    locker_id: str,
    model: object,
    ver: str,
    global_means: tuple[float, float, float, float, float, float] | None,
) -> str:
    cur.execute(_LATEST_FEATURES, (locker_id,))
    raw = cur.fetchone()
    vec = _resolve_features(raw, global_means)
    if vec is None:
        logger.info(
            "batch_predict event=skip reason=no_features locker_id=%s",
            locker_id,
        )
        return "skip"
    predict_from_values(conn, locker_id, vec, model, ver, skip_log=False)
    logger.debug(
        "batch_predict event=ok locker_id=%s model_version=%s",
        locker_id,
        ver,
    )
    return "ok"


def _run_batch(locker_ids: list[str]) -> dict[str, int]:
    ok = skip = err = 0
    mdir = settings.ml_model_dir
    with ml_connection() as conn:
        with conn.cursor() as cur:
            global_means = _fetch_global_means(cur)
            if global_means:
                logger.info("batch_predict global_means_loaded=1")
            else:
                logger.info("batch_predict global_means_loaded=0")
            model, ver = load_active_model_bundle(conn, mdir)
            n = 0
            for lid in locker_ids:
                try:
                    r = _predict_one(conn, cur, lid, model, ver, global_means)
                    if r == "ok":
                        ok += 1
                    else:
                        skip += 1
                except Exception:
                    err += 1
                    logger.exception(
                        "batch_predict event=error locker_id=%s model_version=%s",
                        lid,
                        ver,
                    )
                n += 1
                if n % COMMIT_EVERY == 0:
                    conn.commit()
                    logger.info(
                        "batch_predict event=commit phase=partial processed=%s ok=%s skip=%s err=%s",
                        n,
                        ok,
                        skip,
                        err,
                    )
            conn.commit()
    logger.info(
        "batch_predict event=done total=%s ok=%s skip=%s err=%s",
        len(locker_ids),
        ok,
        skip,
        err,
    )
    return {"ok": ok, "skip": skip, "err": err, "total": len(locker_ids)}


def _list_locker_ids(sql: str) -> list[str]:
    with ml_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            return [str(r[0]) for r in cur.fetchall()]


def batch_predict_all_lockers() -> dict[str, int]:
    """Todos os lockers ativos; commit a cada N; imputação com médias globais quando possível."""
    ids = _list_locker_ids(_ACTIVE_LOCKERS)
    logger.info("batch_predict phase=start scope=all_lockers count=%s", len(ids))
    return _run_batch(ids)


def update_predictions_incremental() -> dict[str, int]:
    """Só lockers com telemetria nas últimas 24h (UTC)."""
    ids = _list_locker_ids(_RECENT_TELEMETRY_LOCKERS)
    logger.info("batch_predict phase=start scope=incremental count=%s", len(ids))
    if not ids:
        return {"ok": 0, "skip": 0, "err": 0, "total": 0}
    return _run_batch(ids)


def run_batch_predict_with_retry() -> dict[str, int]:
    """Até 3 tentativas com backoff exponencial (1s, 2s)."""
    last_exc: BaseException | None = None
    for attempt in range(1, 4):
        try:
            return batch_predict_all_lockers()
        except Exception as exc:
            last_exc = exc
            logger.exception(
                "batch_predict event=retry_failed attempt=%s max=3",
                attempt,
            )
            if attempt < 3:
                delay = 2 ** (attempt - 1)
                logger.info("batch_predict event=backoff_sleep seconds=%s", delay)
                time.sleep(delay)
    assert last_exc is not None
    logger.error("batch_predict event=aborted after=3_attempts")
    raise last_exc
