"""Pontuação em tempo real + bloqueio (fraud_flag) quando anomaly_score >= 0.9."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

import numpy as np

from app import db
from app.ml_fraud.feature_pickup import FEATURE_NAMES, fetch_pickup_feature_row, row_to_vector
from app.ml_fraud.fraud_detection_pipeline import load_bundle

logger = logging.getLogger(__name__)

BLOCK_THRESHOLD = 0.9


def _norm_point(v: float, p5: float, p95: float) -> float:
    span = max(p95 - p5, 1e-9)
    return float(np.clip((v - p5) / span, 0.0, 1.0))


def _anomaly_vector(Xs: np.ndarray, bundle: dict[str, Any]) -> tuple[float, float, float, float]:
    iforest = bundle["iforest"]
    ae = bundle["ae"]
    raw_iso = float(-iforest.decision_function(Xs)[0])
    recon = ae.predict(Xs, verbose=0)
    raw_ae = float(np.mean((Xs - recon) ** 2))
    n_iso = _norm_point(raw_iso, bundle["p_iso_5"], bundle["p_iso_95"])
    n_ae = _norm_point(raw_ae, bundle["p_ae_5"], bundle["p_ae_95"])
    ens = 0.45 * n_iso + 0.55 * n_ae
    score = float(np.clip(ens, 0.0, 1.0))
    return score, n_iso, n_ae, ens


def score_pickup_realtime(pickup_id: str) -> dict[str, Any]:
    row = fetch_pickup_feature_row(pickup_id)
    if row is None:
        raise ValueError("pickup não encontrado")
    bundle = load_bundle()
    scaler = bundle["scaler"]
    X = row_to_vector(row)
    Xs = scaler.transform(X)

    score, n_iso, n_ae, ens = _anomaly_vector(Xs, bundle)
    dynamic_thr = float(bundle.get("calibration_p95", 0.95))

    return {
        "pickup_id": pickup_id,
        "anomaly_score": round(score, 6),
        "dynamic_threshold_percentile_95": round(dynamic_thr, 6),
        "components": {
            "isolation_forest_norm": round(n_iso, 6),
            "autoencoder_norm": round(n_ae, 6),
            "ensemble_score": round(ens, 6),
        },
        "feature_snapshot": {k: round(float(row[k]), 4) for k in FEATURE_NAMES},
        "block_threshold": BLOCK_THRESHOLD,
        "should_block": score >= BLOCK_THRESHOLD,
        "threshold_note": "Score 0–1 (IF+AE); percentil 95 do treino em dynamic_threshold; bloqueio fixo ≥0.9.",
    }


def apply_fraud_block_and_alert(pickup_id: str, score: float, reasons: str) -> dict[str, Any]:
    """Marca fraud_flag, fraud_reason e grava audit_logs para OPS."""
    if score < BLOCK_THRESHOLD:
        return {"blocked": False, "pickup_id": pickup_id}
    reason_line = f"ML_FRAUD score={score:.4f}; {reasons[:400]}"
    upd = db.fetch_one(
        """
        UPDATE pickups
        SET fraud_flag = true,
            fraud_reason = LEFT(%s || COALESCE(E'\n' || fraud_reason, ''), 2000),
            updated_at = NOW()
        WHERE id = %s AND fraud_flag = false
        RETURNING id
        """,
        (reason_line, pickup_id),
    )
    blocked = upd is not None
    if blocked:
        try:
            db.execute(
                """
                INSERT INTO audit_logs (id, actor_id, actor_role, action, target_type, target_id, new_state)
                VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    str(uuid.uuid4()),
                    "system-ml",
                    "ML_SERVICE",
                    "PICKUP_FRAUD_BLOCK_ML",
                    "pickup",
                    pickup_id,
                    json.dumps({"anomaly_score": score, "reason": reasons[:500]}),
                ),
            )
        except Exception as exc:
            logger.warning("audit_logs insert failed: %s", exc)
    logger.warning("pickup fraud block pickup_id=%s score=%s blocked=%s", pickup_id, score, blocked)
    return {"blocked": blocked, "pickup_id": pickup_id, "fraud_flag_set": blocked}
