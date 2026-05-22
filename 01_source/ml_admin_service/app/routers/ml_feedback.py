from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ml_core import MlDashboardOut, MlPredictionFeedbackListOut, MlPredictionFeedbackOut
from app.services import ml_core_service

router = APIRouter(tags=["ml-feedback-ops"])


@router.get("/ml-prediction-feedback", response_model=MlPredictionFeedbackListOut)
def list_feedback(
    limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)
) -> MlPredictionFeedbackListOut:
    items = ml_core_service.list_feedback(db, limit=limit)
    out = [MlPredictionFeedbackOut.model_validate(f) for f in items]
    return MlPredictionFeedbackListOut(items=out, total=len(out))


@router.post("/ops/validate-feedback")
def validate_feedback(db: Session = Depends(get_db)) -> dict:
    return ml_core_service.run_validate_feedback(db)


@router.get("/dashboard", response_model=MlDashboardOut)
def ml_dashboard(db: Session = Depends(get_db)) -> MlDashboardOut:
    return ml_core_service.dashboard(db)
