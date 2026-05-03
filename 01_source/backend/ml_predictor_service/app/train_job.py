from __future__ import annotations

import json
import logging
from pathlib import Path

from app.config import settings
from app import db
from app.model_rf import load_model, new_model_version, save_model, train_from_rows

logger = logging.getLogger(__name__)


TRAIN_SQL = """
    SELECT temperature_mean, humidity_mean, battery_min,
           door_failures_7d, usage_events_7d, uptime_hours_7d,
           failure_label_7d
    FROM ml_features_daily
    WHERE feature_date < CURRENT_DATE
      AND feature_date >= CURRENT_DATE - INTERVAL '90 days'
"""


def run_training_job() -> dict:
    """Treina com dados até ontem, grava artefato e ml_model_metadata."""
    try:
        db.refresh_materialized_view_concurrent()
    except Exception as exc:
        logger.warning("refresh MV skipped or failed: %s", exc)

    rows = db.fetch_all(TRAIN_SQL)
    if len(rows) < 10:
        raise RuntimeError(f"not enough training rows: {len(rows)}")

    clf, metrics = train_from_rows(rows)
    version = new_model_version()
    path = Path(settings.model_artifact_path)
    save_model(clf, path)

    db.execute(
        "UPDATE ml_model_metadata SET status = 'STALE' WHERE status = 'ACTIVE'",
    )
    db.execute(
        """
        INSERT INTO ml_model_metadata (model_version, trained_at, metrics_json, status)
        VALUES (%s, NOW(), %s::jsonb, 'ACTIVE')
        """,
        (version, json.dumps(metrics)),
    )
    logger.info("trained model %s metrics=%s", version, metrics)
    return {"model_version": version, "metrics": metrics, "n_samples": len(rows)}


def load_active_classifier():
    path = Path(settings.model_artifact_path)
    if not path.exists():
        return None, None
    return load_model(path), path
