from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ml_core import MlPredictionsLogIn, MlPredictionsLogListOut, MlPredictionsLogOut
from app.services import ml_core_service

router = APIRouter(prefix="/ml-predictions-log", tags=["ml-predictions-log"])


@router.get("", response_model=MlPredictionsLogListOut)
def list_predictions(
    locker_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> MlPredictionsLogListOut:
    items = ml_core_service.list_predictions(db, locker_id=locker_id, limit=limit)
    out = [MlPredictionsLogOut.model_validate(p) for p in items]
    return MlPredictionsLogListOut(items=out, total=len(out))


@router.post("", response_model=MlPredictionsLogOut, status_code=status.HTTP_201_CREATED)
def create_prediction(body: MlPredictionsLogIn, db: Session = Depends(get_db)) -> MlPredictionsLogOut:
    return MlPredictionsLogOut.model_validate(ml_core_service.create_prediction(db, body))
