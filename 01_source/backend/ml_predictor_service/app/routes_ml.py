"""Endpoints /ml/* — predição, dashboard OPS e retreino."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app import db
from app.model_inference.predict import predict_failure
from app.model_training.train_rf import run_sklearn_training

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ml", tags=["ml"])


class MlPredictOut(BaseModel):
    locker_id: str
    failure_probability: float
    health_score: float
    model_version: str


class MlTrainOut(BaseModel):
    ok: bool
    model_version: str | None = None
    metrics: dict | None = None
    n_rows: int | None = None
    error: str | None = None


@router.get("/predict/{locker_id}", response_model=MlPredictOut)
def ml_predict(locker_id: str) -> MlPredictOut:
    row = db.fetch_one(
        """
        SELECT id FROM lockers
        WHERE id = %s AND active = true
        LIMIT 1
        """,
        (locker_id,),
    )
    if not row:
        raise HTTPException(404, "locker not found or inactive")
    try:
        p, h, ver = predict_failure(locker_id)
    except RuntimeError as e:
        raise HTTPException(503, str(e)) from e
    except ValueError as e:
        raise HTTPException(404, str(e)) from e
    return MlPredictOut(
        locker_id=locker_id,
        failure_probability=p,
        health_score=h,
        model_version=ver,
    )


@router.get("/dashboard")
def ml_dashboard() -> dict:
    at_risk = db.fetch_all(
        """
        WITH lf AS (
            SELECT DISTINCT ON (locker_id)
                locker_id, feature_date, battery_min_70d, door_failures_70d
            FROM ml_features_daily
            WHERE battery_min_70d IS NOT NULL
            ORDER BY locker_id, feature_date DESC
        ),
        lp AS (
            SELECT DISTINCT ON (locker_id)
                locker_id, failure_probability, health_score, model_version, predicted_at
            FROM ml_predictions_log
            ORDER BY locker_id, predicted_at DESC
        )
        SELECT lf.locker_id,
               lp.health_score,
               lf.battery_min_70d AS battery_min,
               lf.door_failures_70d,
               lp.failure_probability
        FROM lf
        INNER JOIN lp ON lp.locker_id = lf.locker_id
        WHERE lp.health_score < 30 AND lf.battery_min_70d <= 20
        ORDER BY lp.health_score ASC
        LIMIT 200
        """
    )
    series = db.fetch_all(
        """
        SELECT (date_trunc('day', predicted_at AT TIME ZONE 'UTC'))::date AS d,
               AVG(health_score)::float AS avg_health_score
        FROM ml_predictions_log
        WHERE predicted_at >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '7 days'
        GROUP BY 1
        ORDER BY 1
        """
    )
    top_doors = db.fetch_all(
        """
        SELECT locker_id, door_failures_70d
        FROM (
            SELECT DISTINCT ON (locker_id)
                locker_id, door_failures_70d, feature_date
            FROM ml_features_daily
            WHERE door_failures_70d IS NOT NULL
            ORDER BY locker_id, feature_date DESC
        ) u
        ORDER BY door_failures_70d DESC NULLS LAST
        LIMIT 10
        """
    )
    return {
        "at_risk_lockers": at_risk,
        "avg_health_score_series": series,
        "top_door_failures_70d": top_doors,
    }


@router.post("/train", response_model=MlTrainOut)
def ml_train() -> MlTrainOut:
    try:
        out = run_sklearn_training()
        return MlTrainOut(
            ok=True,
            model_version=str(out["model_version"]),
            metrics=out["metrics"] if isinstance(out["metrics"], dict) else None,
            n_rows=int(out["n_rows"]) if out.get("n_rows") is not None else None,
        )
    except Exception as exc:
        logger.exception("ml train failed")
        return MlTrainOut(ok=False, error=str(exc))
