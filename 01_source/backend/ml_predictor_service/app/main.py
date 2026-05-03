from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.config import settings
from app import db
from app.model_rf import health_score, predict_failure_prob
from app.train_job import load_active_classifier, run_training_job

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _start_scheduler() -> None:
    global _scheduler
    if not settings.enable_train_scheduler:
        return
    tz = ZoneInfo(settings.scheduler_timezone)
    _scheduler = BackgroundScheduler(timezone=tz)
    _scheduler.add_job(
        lambda: run_training_job_safe(),
        "cron",
        hour=settings.scheduler_hour,
        minute=0,
    )
    _scheduler.start()
    logger.info("scheduler: daily train at %s:00 %s", settings.scheduler_hour, settings.scheduler_timezone)


def run_training_job_safe() -> None:
    try:
        run_training_job()
    except Exception:
        logger.exception("scheduled train failed")


def _stop_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    _start_scheduler()
    yield
    _stop_scheduler()


app = FastAPI(title="ml_predictor_service", version="0.1.0", lifespan=lifespan)


class TrainResponse(BaseModel):
    ok: bool
    model_version: str | None = None
    metrics: dict | None = None
    error: str | None = None


class PredictResponse(BaseModel):
    locker_id: str
    feature_date: str | None
    failure_probability: float
    health_score: float
    model_version: str | None


@app.post("/train", response_model=TrainResponse)
def train() -> TrainResponse:
    try:
        out = run_training_job()
        return TrainResponse(ok=True, model_version=out["model_version"], metrics=out["metrics"])
    except Exception as exc:
        logger.exception("train failed")
        return TrainResponse(ok=False, error=str(exc))


@app.get("/predict/{locker_id}", response_model=PredictResponse)
def predict(locker_id: str) -> PredictResponse:
    clf, path = load_active_classifier()
    if clf is None:
        raise HTTPException(503, "model not available; run POST /train first")
    row = db.fetch_one(
        """
        SELECT feature_date, temperature_mean, humidity_mean, battery_min,
               door_failures_7d, usage_events_7d, uptime_hours_7d
        FROM ml_features_daily
        WHERE locker_id = %s
        ORDER BY feature_date DESC
        LIMIT 1
        """,
        (locker_id,),
    )
    if not row:
        raise HTTPException(404, "no features for locker")
    p = predict_failure_prob(clf, row)
    hs = health_score(p)
    meta = db.fetch_one(
        "SELECT model_version FROM ml_model_metadata WHERE status = 'ACTIVE' ORDER BY trained_at DESC LIMIT 1"
    )
    version = meta["model_version"] if meta else path.name
    db.execute(
        """
        INSERT INTO ml_predictions_log (locker_id, failure_probability, health_score, model_version)
        VALUES (%s, %s, %s, %s)
        """,
        (locker_id, p, hs, version),
    )
    fd = row.get("feature_date")
    return PredictResponse(
        locker_id=locker_id,
        feature_date=str(fd) if fd is not None else None,
        failure_probability=p,
        health_score=hs,
        model_version=str(version) if version else None,
    )


@app.get("/health")
def health():
    path = Path(settings.model_artifact_path)
    meta = db.fetch_one(
        "SELECT model_version, status, trained_at FROM ml_model_metadata WHERE status = 'ACTIVE' ORDER BY trained_at DESC LIMIT 1"
    )
    try:
        db.fetch_one("SELECT 1 AS ok")
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "service": "ml_predictor_service",
        "model_file_exists": path.exists(),
        "database_ok": db_ok,
        "active_model": dict(meta) if meta else None,
    }


@app.get("/metrics")
def metrics():
    row = db.fetch_one(
        "SELECT model_version, trained_at, metrics_json FROM ml_model_metadata WHERE status = 'ACTIVE' ORDER BY trained_at DESC LIMIT 1"
    )
    if not row:
        raise HTTPException(404, "no trained model metadata")
    return {
        "model_version": row["model_version"],
        "trained_at": row["trained_at"].isoformat() if row.get("trained_at") else None,
        "metrics": row["metrics_json"],
    }


@app.get("/intelligence/dashboard")
def intelligence_dashboard(days: int = 14):
    """Dados agregados para OPS /ops/intelligence (leitura em ml_predictions_log)."""
    series = db.fetch_all(
        """
        SELECT date_trunc('day', predicted_at AT TIME ZONE 'UTC')::date AS d,
               AVG(failure_probability)::float AS avg_failure_p,
               AVG(health_score)::float AS avg_health
        FROM ml_predictions_log
        WHERE predicted_at >= NOW() - (%s * INTERVAL '1 day')
        GROUP BY 1
        ORDER BY 1
        """,
        (max(1, min(days, 90)),),
    )
    at_risk = db.fetch_all(
        """
        WITH latest AS (
            SELECT DISTINCT ON (locker_id)
                locker_id, predicted_at, failure_probability, health_score, model_version
            FROM ml_predictions_log
            ORDER BY locker_id, predicted_at DESC
        )
        SELECT * FROM latest WHERE health_score < 30
        ORDER BY health_score ASC
        LIMIT 200
        """
    )
    return {"at_risk": at_risk, "series": series}
