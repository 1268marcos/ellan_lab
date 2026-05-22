from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ml_core import MlFeaturesDailyIn, MlFeaturesDailyListOut, MlFeaturesDailyOut
from app.services import ml_core_service

router = APIRouter(prefix="/ml-features-daily", tags=["ml-features-daily"])


@router.get("", response_model=MlFeaturesDailyListOut)
def list_features(
    locker_id: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> MlFeaturesDailyListOut:
    items = ml_core_service.list_features(db, locker_id=locker_id, limit=limit)
    out = [MlFeaturesDailyOut.model_validate(f) for f in items]
    return MlFeaturesDailyListOut(items=out, total=len(out))


@router.post("", response_model=MlFeaturesDailyOut, status_code=status.HTTP_201_CREATED)
def create_feature(body: MlFeaturesDailyIn, db: Session = Depends(get_db)) -> MlFeaturesDailyOut:
    return MlFeaturesDailyOut.model_validate(ml_core_service.create_feature(db, body))


@router.delete("/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feature(feature_id: int, db: Session = Depends(get_db)) -> None:
    ml_core_service.delete_feature(db, feature_id)
