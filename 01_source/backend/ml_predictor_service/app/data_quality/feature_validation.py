"""Integridade referencial, amostras mínimas e taxa de positivos do label."""
from __future__ import annotations

import logging
from typing import Any

from app import db

logger = logging.getLogger(__name__)

_ORPHANS_SQL = """
SELECT m.id, m.locker_id, m.feature_date
FROM ml_features_daily m
LEFT JOIN lockers l ON l.id = m.locker_id
WHERE l.id IS NULL
LIMIT 500
"""

_LOW_SAMPLE_SQL = """
SELECT m.locker_id, COUNT(*)::int AS n_samples
FROM ml_features_daily m
INNER JOIN lockers l ON l.id = m.locker_id
WHERE COALESCE(m.failure_label_70d, m.failure_label_7d, 0) IN (0, 1)
GROUP BY m.locker_id
HAVING COUNT(*) < %s
ORDER BY n_samples ASC
"""

_POS_RATE_SQL = """
SELECT
  COUNT(*)::bigint AS total,
  SUM(CASE WHEN COALESCE(m.failure_label_70d, m.failure_label_7d, 0) = 1 THEN 1 ELSE 0 END)::bigint AS positives
FROM ml_features_daily m
INNER JOIN lockers l ON l.id = m.locker_id
WHERE m.feature_date >= (CURRENT_DATE - INTERVAL '90 days')
"""


def check_referential_integrity() -> list[dict[str, Any]]:
    rows = db.fetch_all(_ORPHANS_SQL)
    if rows:
        logger.error("validation event=orphan_rows count=%s", len(rows))
    return rows


def check_min_samples_per_locker(min_n: int = 20) -> list[dict[str, Any]]:
    return db.fetch_all(_LOW_SAMPLE_SQL, (min_n,))


def check_positive_rate_failure_label(
    *, min_rate: float = 0.01, window_days: int = 90
) -> dict[str, Any]:
    _ = window_days
    row = db.fetch_one(_POS_RATE_SQL)
    total = int(row["total"] or 0) if row else 0
    pos = int(row["positives"] or 0) if row else 0
    rate = (pos / total) if total else 0.0
    ok = True if total == 0 else rate >= min_rate
    if not ok:
        logger.error(
            "validation event=low_positive_rate rate=%.5f min=%s total=%s pos=%s",
            rate,
            min_rate,
            total,
            pos,
        )
    return {"total": total, "positives": pos, "rate": rate, "ok": ok, "delay_training": not ok}


def should_delay_training(
    *,
    min_rate: float = 0.01,
    min_samples: int = 20,
    orphans: list[dict[str, Any]] | None = None,
    low: list[dict[str, Any]] | None = None,
    pr: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    o = orphans if orphans is not None else check_referential_integrity()
    if o:
        return True, f"orphan_ml_features_daily_rows={len(o)}"
    ls = low if low is not None else check_min_samples_per_locker(min_samples)
    if ls:
        return True, f"lockers_below_{min_samples}_samples={len(ls)}"
    p = pr if pr is not None else check_positive_rate_failure_label(min_rate=min_rate)
    if not p["ok"]:
        return True, f"failure_label_positive_rate={p['rate']:.5f}<{min_rate}"
    return False, "ok"


def run_all_checks(
    *, min_samples: int = 20, min_positive_rate: float = 0.01
) -> dict[str, Any]:
    orphans = check_referential_integrity()
    low = check_min_samples_per_locker(min_samples)
    pr = check_positive_rate_failure_label(min_rate=min_positive_rate)
    delay, reason = should_delay_training(
        min_rate=min_positive_rate,
        min_samples=min_samples,
        orphans=orphans,
        low=low,
        pr=pr,
    )
    logger.info(
        "validation event=report orphans=%s low_sample_lockers=%s pos_rate=%.5f delay=%s",
        len(orphans),
        len(low),
        float(pr.get("rate") or 0),
        delay,
    )
    return {
        "orphan_rows": orphans[:50],
        "orphan_count": len(orphans),
        "low_sample_lockers": low[:50],
        "low_sample_count": len(low),
        "positive_label": pr,
        "delay_training": delay,
        "delay_reason": reason,
    }
