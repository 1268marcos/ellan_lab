"""Previsão rolling 24h (multi-horizon) + alertas de ocupação > 85% por 3h consecutivas."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd

from app.ml_demand.lstm_demand_model import load_bundle
from app.ml_demand.series_builder import (
    HORIZON,
    N_FEATURES,
    SEQ_LEN,
    fetch_hourly_panel,
    locker_slots_total,
)

logger = logging.getLogger(__name__)

ALERT_THRESHOLD = 0.85
ALERT_CONSECUTIVE_H = 3


def _heuristic_forecast(locker_id: str, hours: int) -> np.ndarray:
    """Fallback sem TensorFlow: média por hora do dia na janela 7d + leve tendência."""
    df = fetch_hourly_panel(locker_id, hours_back=SEQ_LEN + 168, hours_forward=0)
    if df.empty or "occ_rate" not in df.columns:
        return np.full(min(hours, HORIZON), 0.4, dtype=np.float32)
    tail = df.tail(min(len(df), SEQ_LEN + 168)).copy()
    tail["hour_bucket"] = pd.to_datetime(tail["hour_bucket"], utc=True)
    by_h = tail.groupby(tail["hour_bucket"].dt.hour)["occ_rate"].mean()
    last = float(tail.tail(SEQ_LEN)["occ_rate"].mean()) if len(tail) >= 8 else 0.35
    out = []
    t0 = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    for h in range(min(hours, HORIZON)):
        th = (t0 + timedelta(hours=h + 1)).hour
        base = float(by_h[th]) if th in by_h.index else float(by_h.mean()) if len(by_h) else last
        out.append(float(min(1.0, max(0.0, base + 0.02 * (h % 3 - 1)))))
    return np.array(out, dtype=np.float32)


def build_alerts(occ_frac: list[float], threshold: float = ALERT_THRESHOLD, consecutive: int = ALERT_CONSECUTIVE_H) -> list[dict[str, Any]]:
    """Alertas quando occ_frac >= threshold por `consecutive` horas seguidas."""
    alerts = []
    run_start = None
    run_len = 0
    for i, v in enumerate(occ_frac):
        if v >= threshold:
            if run_start is None:
                run_start = i
            run_len += 1
        else:
            if run_len >= consecutive:
                alerts.append(
                    {
                        "from_hour_index": run_start,
                        "to_hour_index": run_start + run_len - 1,
                        "hours": run_len,
                        "peak_occupancy_fraction": round(max(occ_frac[run_start : run_start + run_len]), 4),
                    }
                )
            run_start = None
            run_len = 0
    if run_len >= consecutive:
        alerts.append(
            {
                "from_hour_index": run_start,
                "to_hour_index": run_start + run_len - 1,
                "hours": run_len,
                "peak_occupancy_fraction": round(max(occ_frac[run_start : run_start + run_len]), 4),
            }
        )
    return alerts


def predict_occupancy_hours(locker_id: str, hours: int = 24) -> dict[str, Any]:
    hours = max(1, min(int(hours), HORIZON))
    slots_n = locker_slots_total(locker_id)
    df = fetch_hourly_panel(locker_id, hours_back=max(SEQ_LEN * 2, 400), hours_forward=0)
    df = df.tail(SEQ_LEN).reset_index(drop=True)
    if len(df) < SEQ_LEN:
        pad = SEQ_LEN - len(df)
        if len(df) == 0:
            df = pd.DataFrame(
                {
                    "hour_bucket": pd.date_range(
                        datetime.now(timezone.utc) - timedelta(hours=SEQ_LEN),
                        periods=SEQ_LEN,
                        freq="h",
                        tz="UTC",
                    ),
                    "occ_rate": [0.35] * SEQ_LEN,
                    "sin_hour": [0.0] * SEQ_LEN,
                    "cos_hour": [1.0] * SEQ_LEN,
                    "sin_dow": [0.0] * SEQ_LEN,
                    "cos_dow": [1.0] * SEQ_LEN,
                    "peak_9_18": [0.0] * SEQ_LEN,
                    "avg_duration_h": [0.0] * SEQ_LEN,
                    "pickups_norm": [0.0] * SEQ_LEN,
                    "inbound_norm": [0.0] * SEQ_LEN,
                    "telemetry_norm": [0.0] * SEQ_LEN,
                }
            )
        else:
            head = pd.concat([df.iloc[[0]].copy()] * pad, ignore_index=True)
            df = pd.concat([head, df], ignore_index=True).tail(SEQ_LEN).reset_index(drop=True)

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
    X = df[feat_cols].values.astype(np.float32).reshape(1, SEQ_LEN, N_FEATURES)
    used_lstm = True
    try:
        model, x_sc, y_sc, meta = load_bundle()
        Xf = X.reshape(-1, N_FEATURES)
        Xs = x_sc.transform(Xf).reshape(1, SEQ_LEN, N_FEATURES).astype(np.float32)
        y_hat_s = model.predict(Xs, verbose=0)[0]
        y_hat = y_sc.inverse_transform(y_hat_s.reshape(1, -1)).ravel()
    except Exception as exc:
        logger.warning("LSTM indisponível (%s); usando heurística", exc)
        y_hat = _heuristic_forecast(locker_id, HORIZON)
        used_lstm = False
        meta = {}

    y_hat = np.clip(y_hat[:HORIZON], 0.0, 1.0)
    y_out = y_hat[:hours]
    t0 = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    forecast = []
    for h in range(len(y_out)):
        ts = t0 + timedelta(hours=h + 1)
        frac = float(y_out[h])
        forecast.append(
            {
                "hour_start": ts.isoformat(),
                "occupied_slots_fraction": round(frac, 4),
                "occupied_pct_slots": round(100.0 * frac, 2),
                "occupied_slots_est": round(frac * slots_n, 2),
                "slots_total": slots_n,
            }
        )

    occ_fracs = [f["occupied_slots_fraction"] for f in forecast]
    alerts = build_alerts(occ_fracs)

    return {
        "locker_id": locker_id,
        "hours": len(forecast),
        "model": "lstm_keras" if used_lstm else "heuristic_fallback",
        "meta": meta,
        "forecast": forecast,
        "alerts": alerts,
        "alert_policy": {
            "threshold_fraction": ALERT_THRESHOLD,
            "consecutive_hours": ALERT_CONSECUTIVE_H,
            "description": "Ocupação prevista ≥85% por 3 horas seguidas",
        },
    }
