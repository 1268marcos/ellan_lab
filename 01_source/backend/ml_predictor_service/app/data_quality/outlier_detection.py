"""IQR por locker, alertas em monitoring.ml_feature_alerts e imputação por mediana."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from app.db_ml import ml_connection

logger = logging.getLogger(__name__)

DEFAULT_IQR_COLS = ("temperature_avg_70d", "humidity_avg_70d", "battery_min_70d")

_DDL = """
CREATE SCHEMA IF NOT EXISTS monitoring;
CREATE TABLE IF NOT EXISTS monitoring.ml_feature_alerts (
  id bigserial PRIMARY KEY,
  locker_id varchar(36) NOT NULL,
  feature_date date NOT NULL,
  metric_name text NOT NULL,
  old_value numeric,
  new_value numeric,
  fence_low numeric,
  fence_high numeric,
  method text NOT NULL DEFAULT 'IQR_k3',
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_ml_feature_alerts_locker ON monitoring.ml_feature_alerts (locker_id, created_at DESC);
"""

_LOAD_SQL = """
SELECT m.id, m.locker_id, m.feature_date,
       COALESCE(m.temperature_avg_70d, m.temperature_mean) AS temperature_avg_70d,
       COALESCE(m.humidity_avg_70d, m.humidity_mean) AS humidity_avg_70d,
       COALESCE(m.battery_min_70d, m.battery_min) AS battery_min_70d
FROM ml_features_daily m
WHERE m.feature_date >= (CURRENT_DATE - INTERVAL '180 days')
"""


def ensure_alerts_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(_DDL)


def detect_outliers_iqr(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    *,
    locker_col: str = "locker_id",
    k: float = 3.0,
) -> pd.DataFrame:
    """Marca outliers por locker: fora de [Q1 - k*IQR, Q3 + k*IQR]."""
    cols = tuple(columns) if columns else DEFAULT_IQR_COLS
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            continue
        q1 = out.groupby(locker_col, observed=True)[c].transform(lambda s: s.quantile(0.25))
        q3 = out.groupby(locker_col, observed=True)[c].transform(lambda s: s.quantile(0.75))
        iqr = q3 - q1
        lo, hi = q1 - k * iqr, q3 + k * iqr
        bad = out[c].notna() & iqr.notna() & (iqr > 0) & ((out[c] < lo) | (out[c] > hi))
        out[f"_out_{c}"] = bad.fillna(False)
        out[f"_lo_{c}"] = lo
        out[f"_hi_{c}"] = hi
    return out


def run_outlier_pipeline(
    *,
    dry_run: bool = True,
    columns: list[str] | None = None,
    commit_every: int = 100,
) -> dict[str, Any]:
    cols = tuple(columns) if columns else DEFAULT_IQR_COLS
    allowed = set(DEFAULT_IQR_COLS)
    for c in cols:
        if c not in allowed:
            raise ValueError(f"coluna não permitida para UPDATE: {c}")
    with ml_connection() as conn:
        ensure_alerts_table(conn)
        df = pd.read_sql(_LOAD_SQL, conn)
    if df.empty:
        logger.info("outlier_pipeline event=empty")
        return {"rows": 0, "alerts": 0, "updates": 0, "dry_run": dry_run}
    tagged = detect_outliers_iqr(df, list(cols))
    med = {
        c: tagged.groupby("locker_id", observed=True)[c].transform("median")
        for c in cols
        if c in tagged.columns
    }
    alerts = updates = 0
    ins = """
        INSERT INTO monitoring.ml_feature_alerts
          (locker_id, feature_date, metric_name, old_value, new_value, fence_low, fence_high)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    batches: list[tuple] = []
    for c in cols:
        oc = f"_out_{c}"
        if c not in tagged.columns or oc not in tagged.columns:
            continue
        for idx, row in tagged.iterrows():
            if not bool(row[oc]):
                continue
            alerts += 1
            old_v = row[c]
            nv = float(med[c].loc[idx])
            if pd.isna(nv):
                nv = float(tagged[c].median())
            flo = row.get(f"_lo_{c}")
            fhi = row.get(f"_hi_{c}")
            batches.append(
                (
                    str(row["locker_id"]),
                    row["feature_date"],
                    c,
                    None if pd.isna(old_v) else float(old_v),
                    nv,
                    None if pd.isna(flo) else float(flo),
                    None if pd.isna(fhi) else float(fhi),
                    int(row["id"]),
                )
            )
    if dry_run or not batches:
        logger.info(
            "outlier_pipeline event=summary dry_run=%s rows=%s alerts=%s updates=0",
            dry_run,
            len(df),
            alerts,
        )
        return {"rows": len(df), "alerts": alerts, "updates": 0, "dry_run": dry_run}
    n = 0
    with ml_connection() as conn:
        ensure_alerts_table(conn)
        cur = conn.cursor()
        for t in batches:
            lid, fd, c, ov, nv, lo, hi, rid = t
            cur.execute(ins, (lid, fd, c, ov, nv, lo, hi))
            cur.execute(f"UPDATE ml_features_daily SET {c} = %s WHERE id = %s", (nv, rid))
            updates += 1
            n += 1
            if n % commit_every == 0:
                conn.commit()
        conn.commit()
    logger.info("outlier_pipeline event=done rows=%s alerts=%s updates=%s", len(df), alerts, updates)
    return {"rows": len(df), "alerts": alerts, "updates": updates, "dry_run": dry_run}
