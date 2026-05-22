from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ml_core import MlFeaturesDaily, MlModelMetadata, MlPredictionFeedback, MlPredictionsLog
from app.schemas.ml_core import (
    MlDashboardOut,
    MlFeaturesDailyIn,
    MlModelMetadataIn,
    MlModelMetadataUpdate,
    MlPredictionsLogIn,
)
from app.services.crypto_util import new_id

VALID_MODEL_STATUS = {"ACTIVE", "STALE", "FAILED"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_models(db: Session) -> list[MlModelMetadata]:
    return db.query(MlModelMetadata).order_by(MlModelMetadata.trained_at.desc()).all()


def create_model(db: Session, body: MlModelMetadataIn) -> MlModelMetadata:
    if body.status not in VALID_MODEL_STATUS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")
    if db.query(MlModelMetadata).filter(MlModelMetadata.model_version == body.model_version).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="model_version_exists")
    if body.status == "ACTIVE":
        db.query(MlModelMetadata).filter(MlModelMetadata.status == "ACTIVE").update({"status": "STALE"})
    row = MlModelMetadata(
        model_version=body.model_version,
        metrics_json=json.dumps(body.metrics),
        status=body.status,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_model(db: Session, model_id: int, body: MlModelMetadataUpdate) -> MlModelMetadata:
    row = db.get(MlModelMetadata, model_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model_not_found")
    if body.status is not None:
        if body.status not in VALID_MODEL_STATUS:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_status")
        if body.status == "ACTIVE":
            db.query(MlModelMetadata).filter(MlModelMetadata.status == "ACTIVE").update({"status": "STALE"})
        row.status = body.status
    if body.metrics is not None:
        row.metrics_json = json.dumps(body.metrics)
    db.commit()
    db.refresh(row)
    return row


def delete_model(db: Session, model_id: int) -> None:
    row = db.get(MlModelMetadata, model_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="model_not_found")
    db.delete(row)
    db.commit()


def list_features(db: Session, locker_id: str | None = None, limit: int = 100) -> list[MlFeaturesDaily]:
    q = db.query(MlFeaturesDaily)
    if locker_id:
        q = q.filter(MlFeaturesDaily.locker_id == locker_id)
    return q.order_by(MlFeaturesDaily.feature_date.desc()).limit(limit).all()


def create_feature(db: Session, body: MlFeaturesDailyIn) -> MlFeaturesDaily:
    if body.failure_label_7d not in (0, 1):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_failure_label")
    existing = (
        db.query(MlFeaturesDaily)
        .filter(
            MlFeaturesDaily.locker_id == body.locker_id,
            MlFeaturesDaily.feature_date == body.feature_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="feature_day_exists")
    row = MlFeaturesDaily(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_feature(db: Session, feature_id: int) -> None:
    row = db.get(MlFeaturesDaily, feature_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="feature_not_found")
    db.delete(row)
    db.commit()


def list_predictions(db: Session, locker_id: str | None = None, limit: int = 100) -> list[MlPredictionsLog]:
    q = db.query(MlPredictionsLog)
    if locker_id:
        q = q.filter(MlPredictionsLog.locker_id == locker_id)
    return q.order_by(MlPredictionsLog.predicted_at.desc()).limit(limit).all()


def create_prediction(db: Session, body: MlPredictionsLogIn) -> MlPredictionsLog:
    row = MlPredictionsLog(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_feedback(db: Session, limit: int = 100) -> list[MlPredictionFeedback]:
    return db.query(MlPredictionFeedback).order_by(MlPredictionFeedback.created_at.desc()).limit(limit).all()


def run_validate_feedback(db: Session) -> dict:
    """Replica validate_ml_predictions() — feedback para predições > 7 dias."""
    cutoff = _utcnow() - timedelta(days=7)
    preds = (
        db.query(MlPredictionsLog)
        .filter(MlPredictionsLog.predicted_at <= cutoff)
        .order_by(MlPredictionsLog.predicted_at.desc())
        .limit(500)
        .all()
    )
    inserted = 0
    for p in preds:
        exists = (
            db.query(MlPredictionFeedback)
            .filter(MlPredictionFeedback.prediction_id == p.id)
            .first()
        )
        if exists:
            continue
        actual = 1.0 if float(p.failure_probability) >= 0.5 else 0.0
        predicted = float(p.failure_probability)
        error_pct = abs(actual - predicted) * 100.0
        status_label = "GOOD" if error_pct < 15 else "DRIFT"
        db.add(
            MlPredictionFeedback(
                id=new_id(),
                prediction_id=p.id,
                actual_value=actual,
                error_pct=error_pct,
                feedback_at=_utcnow(),
                model_performance_status=status_label,
            )
        )
        inserted += 1
    db.commit()
    return {"inserted": inserted, "candidates": len(preds)}


def dashboard(db: Session) -> MlDashboardOut:
    from app.models.partner import MlDataPartner
    from app.services import ml_ops_service

    since = _utcnow() - timedelta(hours=24)
    from app.services import network_players_service, readiness_service

    ops = ml_ops_service.ops_dashboard_counts(db)
    net = network_players_service.network_dashboard_counts(db)
    return MlDashboardOut(
        active_models=db.query(MlModelMetadata).filter(MlModelMetadata.status == "ACTIVE").count(),
        predictions_24h=db.query(MlPredictionsLog).filter(MlPredictionsLog.predicted_at >= since).count(),
        features_rows=db.query(MlFeaturesDaily).count(),
        feedback_rows=db.query(MlPredictionFeedback).count(),
        partners=db.query(MlDataPartner).count(),
        use_cases=ops["use_cases"],
        registry_production=ops["registry_production"],
        training_running=ops["training_running"],
        drift_critical=ops["drift_critical"],
        feature_definitions=ops["feature_definitions"],
        alert_rules=ops["alert_rules"],
        deployments_7d=ops["deployments_7d"],
        locker_network_players=net["locker_network_players"],
        locker_network_priority=net["locker_network_priority"],
        network_ml_profiles=net["network_ml_profiles"],
        player_capabilities=net.get("player_capabilities", 0),
        player_relations=net.get("player_relations", 0),
        market_presence_rows=net.get("market_presence_rows", 0),
        tier1_players=net.get("tier1_players", 0),
        **readiness_service.readiness_dashboard_counts(db),
    )
