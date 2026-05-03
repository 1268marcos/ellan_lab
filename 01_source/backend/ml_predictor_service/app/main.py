from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app import db
from app.routes_ml import router as ml_router
from app.routes_intelligence import router as intelligence_router
from app.routes_churn import router as churn_router
from app.routes_pricing import router as pricing_router
from app.routes_ops_demand import router as ops_demand_router
from app.routes_pickup_fraud import router as pickup_fraud_router
from app.routes_logistics import router as logistics_router
from app.routes_ltv import router as ltv_router
from app.routes_feedback import router as feedback_router
from app.model_rf import health_score, predict_failure_prob
from app.train_job import load_active_classifier, run_training_job
from app.workers.batch_predictor import run_batch_predict_with_retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _start_scheduler() -> None:
    global _scheduler
    if not settings.enable_train_scheduler and not settings.enable_batch_predict_scheduler:
        return
    tz = ZoneInfo(settings.scheduler_timezone)
    _scheduler = BackgroundScheduler(timezone=tz)
    if settings.enable_train_scheduler:
        _scheduler.add_job(
            lambda: run_training_job_safe(),
            "cron",
            hour=settings.scheduler_hour,
            minute=0,
        )
        logger.info("scheduler: train cron hour=%s tz=%s", settings.scheduler_hour, settings.scheduler_timezone)
    if settings.enable_batch_predict_scheduler:
        _scheduler.add_job(
            lambda: run_batch_predict_safe(),
            "cron",
            hour=settings.batch_predict_hour,
            minute=settings.batch_predict_minute,
        )
        logger.info(
            "scheduler: batch_predict cron hour=%s minute=%s tz=%s",
            settings.batch_predict_hour,
            settings.batch_predict_minute,
            settings.scheduler_timezone,
        )
    _scheduler.start()


def run_batch_predict_safe() -> None:
    try:
        run_batch_predict_with_retry()
    except Exception:
        logger.exception("scheduled batch_predict failed after retries")


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# @app.get("/intelligence/dashboard")
# async def intelligence_dashboard_http():
#     return {"at_risk": [], "series": []}


@app.get("/intelligence/models")
async def intelligence_models_http():
    return {"models": []}


app.include_router(ml_router)
app.include_router(intelligence_router)
app.include_router(churn_router)
app.include_router(pricing_router)
app.include_router(ops_demand_router)
app.include_router(pickup_fraud_router)
app.include_router(logistics_router)
app.include_router(ltv_router)
app.include_router(feedback_router)


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
