"""Features por pickup a partir do schema Ellan."""
from __future__ import annotations

import math
import numpy as np

from app import db

FEATURE_NAMES: list[str] = [
    "minutes_activated_to_redeem",
    "token_unused_expired_count",
    "ble_failure_ratio",
    "ble_device_id_changes",
    "off_hours_redeem",
    "pickup_events_burst",
    "audit_pickup_related_count",
    "risk_block_score_max",
    "kiosk_antifraud_count_30d",
    "device_extra_accounts",
]


def fetch_pickup_feature_row(pickup_id: str) -> dict[str, float] | None:
    p = db.fetch_one(
        """
        SELECT id, order_id, locker_id, activated_at, redeemed_at, site_id, region
        FROM pickups WHERE id = %s
        """,
        (pickup_id,),
    )
    if not p:
        return None
    oid = str(p.get("order_id") or "")
    lid = str(p.get("locker_id") or "")
    site = str(p.get("site_id") or "") or str(p.get("region") or "")

    minutes = 0.0
    if p.get("activated_at") and p.get("redeemed_at"):
        try:
            minutes = max(0.0, (p["redeemed_at"] - p["activated_at"]).total_seconds() / 60.0)
        except Exception:
            minutes = 0.0

    tok = db.fetch_one(
        """
        SELECT COUNT(*)::int AS c FROM pickup_tokens
        WHERE pickup_id = %s AND used_at IS NULL AND expires_at < NOW()
        """,
        (pickup_id,),
    )
    token_unused = float(tok["c"] if tok else 0)

    ble = db.fetch_one(
        """
        SELECT
          COUNT(*)::int AS n,
          COUNT(*) FILTER (WHERE UPPER(status) IS DISTINCT FROM 'SUCCESS')::int AS nf
        FROM ble_handshake_logs WHERE pickup_id = %s
        """,
        (pickup_id,),
    )
    n_ble = int(ble["n"] or 0) if ble else 0
    nf_ble = int(ble["nf"] or 0) if ble else 0
    ble_fail_ratio = float(nf_ble / max(n_ble, 1))
    ble_dev = db.fetch_one(
        "SELECT COUNT(DISTINCT ble_device_id)::int AS c FROM ble_handshake_logs WHERE pickup_id = %s AND ble_device_id IS NOT NULL",
        (pickup_id,),
    )
    ble_dev_changes = max(0.0, float((ble_dev or {}).get("c") or 0) - 1.0)

    off_hours = 0.0
    if p.get("redeemed_at"):
        h = p["redeemed_at"].hour if hasattr(p["redeemed_at"], "hour") else 12
        if not (8 <= h <= 19):
            off_hours = 1.0

    ev = db.fetch_one(
        """
        SELECT COUNT(*)::int AS c,
               EXTRACT(EPOCH FROM (MAX(occurred_at) - MIN(occurred_at))) / 3600.0 AS span_h
        FROM pickup_events WHERE pickup_id = %s
        """,
        (pickup_id,),
    )
    burst = 0.0
    if ev and ev.get("c") and int(ev["c"]) > 1:
        span = float(ev.get("span_h") or 0.01)
        burst = min(50.0, float(ev["c"]) / max(span, 0.01))

    aud = db.fetch_one(
        """
        SELECT COUNT(*)::int AS c FROM audit_logs
        WHERE (target_id = %s AND target_type ILIKE '%%pickup%%')
           OR (target_id = %s AND target_type ILIKE '%%order%%')
        """,
        (pickup_id, oid),
    )
    aud_c = min(100.0, float((aud or {}).get("c") or 0))

    rsk = None
    if lid:
        rsk = db.fetch_one(
            """
            SELECT COALESCE(MAX(score), 0)::float / 100.0 AS mx
            FROM risk_events r
            WHERE r.locker_id = %s
              AND (
                CASE WHEN r.created_at > 20000000000
                  THEN to_timestamp(r.created_at / 1000.0)
                  ELSE to_timestamp(r.created_at)
                END AT TIME ZONE 'UTC'
              ) >= (NOW() AT TIME ZONE 'UTC' - INTERVAL '7 days')
            """,
            (lid,),
        )
    risk_mx = float((rsk or {}).get("mx") or 0.0)

    kaf = db.fetch_one(
        """
        SELECT COUNT(*)::int AS c FROM kiosk_antifraud_events
        WHERE totem_id = %s AND created_at >= NOW() - INTERVAL '30 days'
        """,
        (site,),
    )
    kaf_c = min(500.0, float((kaf or {}).get("c") or 0))

    dev_ex = 0.0
    if oid:
        dev = db.fetch_one("SELECT device_id, user_id FROM orders WHERE id = %s", (oid,))
        if dev and dev.get("device_id"):
            du = db.fetch_one(
                """
                SELECT GREATEST(COUNT(DISTINCT user_id) - 1, 0)::int AS c
                FROM orders
                WHERE device_id = %s AND deleted_at IS NULL AND user_id IS NOT NULL
                """,
                (str(dev["device_id"]),),
            )
            dev_ex = min(50.0, float((du or {}).get("c") or 0))

    return {
        "minutes_activated_to_redeem": min(minutes, 10_000.0),
        "token_unused_expired_count": token_unused,
        "ble_failure_ratio": ble_fail_ratio,
        "ble_device_id_changes": ble_dev_changes,
        "off_hours_redeem": off_hours,
        "pickup_events_burst": burst,
        "audit_pickup_related_count": aud_c,
        "risk_block_score_max": risk_mx,
        "kiosk_antifraud_count_30d": kaf_c,
        "device_extra_accounts": dev_ex,
    }


def row_to_vector(row: dict[str, float]) -> np.ndarray:
    return np.array([[row[k] for k in FEATURE_NAMES]], dtype=np.float64)


def training_rows(limit: int = 8000) -> tuple[np.ndarray, list[str]]:
    rows = db.fetch_all(
        """
        SELECT id FROM pickups
        WHERE redeemed_at IS NOT NULL
          AND redeemed_at >= NOW() - INTERVAL '120 days'
        ORDER BY redeemed_at DESC
        LIMIT %s
        """,
        (limit,),
    )
    X_list: list[list[float]] = []
    pid_list: list[str] = []
    for r in rows:
        pid = str(r["id"])
        feat = fetch_pickup_feature_row(pid)
        if feat is None:
            continue
        X_list.append([feat[k] for k in FEATURE_NAMES])
        pid_list.append(pid)
    if not X_list:
        return np.zeros((0, len(FEATURE_NAMES)), dtype=np.float64), []
    return np.array(X_list, dtype=np.float64), pid_list
