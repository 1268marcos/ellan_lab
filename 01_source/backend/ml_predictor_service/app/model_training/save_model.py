"""Persistência joblib + registro versionado em ml_model_metadata."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import joblib
import psycopg2.extensions
from psycopg2.extras import Json

from app.db_ml import ml_connection


def _model_dir(explicit: str | None) -> str:
    return explicit or os.environ.get("ML_MODEL_DIR", "models")


def save_trained_model(
    model: object,
    metrics: dict,
    *,
    model_dir: str | None = None,
) -> str:
    """Grava .pkl, marca ACTIVE e demais STALE. Retorna model_version."""
    d = _model_dir(model_dir)
    os.makedirs(d, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    version = f"rf_{ts}"
    fname = f"{version}.pkl"
    path = os.path.join(d, fname)
    joblib.dump(model, path)
    payload = dict(metrics)
    payload["model_artifact"] = fname
    with ml_connection() as conn:
        _insert_metadata(conn, version, payload)
    return version


def _insert_metadata(conn: psycopg2.extensions.connection, version: str, metrics: dict) -> None:
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE public.ml_model_metadata SET status = 'STALE' WHERE status = 'ACTIVE'"
        )
        cur.execute(
            """
            INSERT INTO public.ml_model_metadata (model_version, metrics_json, status)
            VALUES (%s, %s, 'ACTIVE')
            """,
            (version, Json(metrics)),
        )


def load_model_from_disk(version: str, metrics_json: dict | None, model_dir: str | None) -> object:
    d = _model_dir(model_dir)
    art = (metrics_json or {}).get("model_artifact") if metrics_json else None
    fname = art or f"{version}.pkl"
    path = os.path.join(d, fname)
    return joblib.load(path)
