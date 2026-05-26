from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ml_efficiency import (
    MlEfficiencyScorecardOut,
    MlFeatureFreshnessBreachOut,
    MlInferenceUsageOut,
    MlOpsRecommendationOut,
)
from app.services import ml_efficiency_service

router = APIRouter(prefix="/efficiency", tags=["ml-efficiency"])


@router.get("/scorecard", response_model=MlEfficiencyScorecardOut)
def scorecard(db: Session = Depends(get_db)) -> MlEfficiencyScorecardOut:
    return MlEfficiencyScorecardOut.model_validate(ml_efficiency_service.efficiency_scorecard(db))


@router.get("/inference-usage")
def list_usage(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db)) -> dict:
    rows = ml_efficiency_service.list_inference_usage(db, days=days)
    return {
        "usage": [MlInferenceUsageOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.get("/freshness-breaches")
def list_breaches(status: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    rows = ml_efficiency_service.list_freshness_breaches(db, status=status)
    return {
        "breaches": [MlFeatureFreshnessBreachOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.get("/recommendations")
def list_recs(status: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    rows = ml_efficiency_service.list_recommendations(db, status=status)
    return {
        "recommendations": [MlOpsRecommendationOut.model_validate(r) for r in rows],
        "total": len(rows),
    }


@router.post("/recommendations/generate")
def generate_recs(db: Session = Depends(get_db)) -> dict:
    return ml_efficiency_service.generate_recommendations(db)


@router.post("/recommendations/{rec_id}/dismiss", response_model=MlOpsRecommendationOut)
def dismiss_rec(rec_id: str, db: Session = Depends(get_db)) -> MlOpsRecommendationOut:
    row = ml_efficiency_service.dismiss_recommendation(db, rec_id)
    if not row:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="recommendation not found")
    return MlOpsRecommendationOut.model_validate(row)


@router.post("/seed")
def seed_efficiency(db: Session = Depends(get_db)) -> dict:
    return ml_efficiency_service.seed_efficiency(db)
