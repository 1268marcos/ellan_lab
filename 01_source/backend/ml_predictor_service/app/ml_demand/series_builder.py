"""Painel horário a partir de locker_slot_hourly_occupancy, inbound_deliveries, orders, locker_telemetry."""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

from app import db

SEQ_LEN = 168
HORIZON = 24
N_FEATURES = 10


def locker_slots_total(locker_id: str) -> int:
    row = db.fetch_one("SELECT COALESCE(slots_count, 16)::int AS n FROM lockers WHERE id = %s", (locker_id,))
    if not row or not row.get("n"):
        return 16
    return max(1, int(row["n"]))


def fetch_hourly_panel(locker_id: str, hours_back: int, hours_forward: int = 0) -> pd.DataFrame:
    """
    Uma linha por hora UTC com features alinhadas ao schema.
    `hours_back` horas no passado + `hours_forward` no futuro (para rótulos y no treino).
    """
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    t_end = now + timedelta(hours=hours_forward)
    t_start = now - timedelta(hours=hours_back)
    slots_n = locker_slots_total(locker_id)

    occ_rows = db.fetch_all(
        """
        SELECT
          date_trunc('hour', hour_bucket AT TIME ZONE 'UTC') AS hb,
          COUNT(*) FILTER (WHERE is_occupied) AS occ_slots,
          AVG(occupied_duration_minutes)::float AS avg_dur
        FROM locker_slot_hourly_occupancy
        WHERE locker_id = %s
          AND hour_bucket >= %s
          AND hour_bucket < %s
        GROUP BY 1
        ORDER BY 1
        """,
        (locker_id, t_start, t_end),
    )

    def _hour_key(ts: Any) -> pd.Timestamp:
        t = pd.Timestamp(ts)
        if t.tzinfo is None:
            t = t.tz_localize("UTC")
        return t.tz_convert("UTC").floor("h")

    occ_map = {_hour_key(r["hb"]): r for r in occ_rows}

    pick_rows = db.fetch_all(
        """
        SELECT date_trunc('hour', o.picked_up_at AT TIME ZONE 'UTC') AS hb, COUNT(*)::int AS c
        FROM orders o
        JOIN allocations a ON a.order_id = o.id AND a.locker_id = %s
        WHERE o.picked_up_at IS NOT NULL
          AND o.picked_up_at >= %s
          AND o.picked_up_at < %s
        GROUP BY 1
        """,
        (locker_id, t_start, t_end),
    )
    pick_map = {_hour_key(r["hb"]): int(r["c"] or 0) for r in pick_rows}

    inb_rows = db.fetch_all(
        """
        SELECT date_trunc('hour', COALESCE(stored_at, created_at) AT TIME ZONE 'UTC') AS hb, COUNT(*)::int AS c
        FROM inbound_deliveries
        WHERE locker_id = %s
          AND COALESCE(stored_at, created_at) >= %s
          AND COALESCE(stored_at, created_at) < %s
          AND status NOT IN ('PICKED_UP', 'RETURNED', 'EXPIRED')
        GROUP BY 1
        """,
        (locker_id, t_start, t_end),
    )
    inb_map = {_hour_key(r["hb"]): int(r["c"] or 0) for r in inb_rows}

    tel_rows = db.fetch_all(
        """
        SELECT date_trunc('hour', occurred_at AT TIME ZONE 'UTC') AS hb, COUNT(*)::int AS c
        FROM locker_telemetry
        WHERE locker_id = %s
          AND occurred_at >= %s
          AND occurred_at < %s
          AND (
            LOWER(event_type) LIKE '%%door%%'
            OR LOWER(event_type) LIKE '%%open%%'
            OR LOWER(event_type) LIKE '%%slot%%'
          )
        GROUP BY 1
        """,
        (locker_id, t_start, t_end),
    )
    tel_map = {_hour_key(r["hb"]): int(r["c"] or 0) for r in tel_rows}

    rows = []
    h = t_start
    max_pick = max(pick_map.values(), default=1)
    max_inb = max(inb_map.values(), default=1)
    max_tel = max(tel_map.values(), default=1)
    while h < t_end:
        hk = _hour_key(h)
        o = occ_map.get(hk)
        occ_slots = float(o["occ_slots"] or 0) if o else 0.0
        avg_dur = float(o["avg_dur"] or 0) / 60.0 if o else 0.0
        occ_rate = min(1.0, occ_slots / float(slots_n))
        hod = hk.hour + hk.minute / 60.0
        dow = int(hk.dayofweek)
        h_rad = 2 * math.pi * hod / 24.0
        d_rad = 2 * math.pi * dow / 7.0
        peak = 1.0 if 9 <= hk.hour < 18 else 0.0
        rows.append(
            {
                "hour_bucket": pd.Timestamp(hk),
                "occ_rate": occ_rate,
                "sin_hour": math.sin(h_rad),
                "cos_hour": math.cos(h_rad),
                "sin_dow": math.sin(d_rad),
                "cos_dow": math.cos(d_rad),
                "peak_9_18": peak,
                "avg_duration_h": avg_dur,
                "pickups_norm": pick_map.get(hk, 0) / max_pick,
                "inbound_norm": inb_map.get(hk, 0) / max_inb,
                "telemetry_norm": tel_map.get(hk, 0) / max_tel,
            }
        )
        h += timedelta(hours=1)

    return pd.DataFrame(rows)


def dataframe_to_sequences(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Janelas SEQ_LEN -> alvo próximos HORIZON `occ_rate`."""
    feat_cols = [
        "occ_rate",
        "sin_hour",
        "cos_hour",
        "sin_dow",
        "cos_dow",
        "peak_9_18",
        "avg_duration_h",
        "pickups_norm",
        "inbound_norm",
        "telemetry_norm",
    ]
    mat = df[feat_cols].values.astype(np.float32)
    X, y = [], []
    for i in range(len(mat) - SEQ_LEN - HORIZON + 1):
        X.append(mat[i : i + SEQ_LEN])
        y.append(mat[i + SEQ_LEN : i + SEQ_LEN + HORIZON, 0])  # futuro occ_rate
    if not X:
        return np.zeros((0, SEQ_LEN, N_FEATURES), np.float32), np.zeros((0, HORIZON), np.float32)
    return np.stack(X), np.stack(y)


def collect_training_arrays(min_lockers: int = 8, max_hours: int = 4000) -> tuple[np.ndarray, np.ndarray]:
    """Amostra lockers ativos com histórico e empilha janelas."""
    lockers = db.fetch_all(
        """
        SELECT DISTINCT l.id
        FROM lockers l
        INNER JOIN locker_slot_hourly_occupancy o ON o.locker_id = l.id
        WHERE l.active = true
          AND o.hour_bucket >= NOW() - INTERVAL '30 days'
        LIMIT %s
        """,
        (min_lockers * 12,),
    )
    X_all, y_all = [], []
    for row in lockers[: max(min_lockers * 3, len(lockers))]:
        lid = str(row["id"])
        try:
            df = fetch_hourly_panel(lid, hours_back=max_hours, hours_forward=0)
        except Exception:
            continue
        if len(df) < SEQ_LEN + HORIZON + 48:
            continue
        X, y = dataframe_to_sequences(df)
        if len(X) == 0:
            continue
        X_all.append(X)
        y_all.append(y)
    if not X_all:
        return np.zeros((0, SEQ_LEN, N_FEATURES), np.float32), np.zeros((0, HORIZON), np.float32)
    return np.concatenate(X_all, axis=0), np.concatenate(y_all, axis=0)


def synthetic_training_data(n: int = 512, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    """Fallback quando o banco não tem séries suficientes (dev/tests)."""
    rng = np.random.default_rng(seed)
    X = rng.normal(0, 1, (n, SEQ_LEN, N_FEATURES)).astype(np.float32)
    X[:, :, 0] = np.clip(rng.uniform(0, 1, (n, SEQ_LEN)), 0, 1).astype(np.float32)
    y = np.zeros((n, HORIZON), np.float32)
    for i in range(n):
        base = float(np.mean(X[i, :, 0]))
        for h in range(HORIZON):
            y[i, h] = float(np.clip(base + 0.08 * rng.standard_normal(), 0.0, 1.0))
    return X, y
