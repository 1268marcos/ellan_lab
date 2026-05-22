from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ml_core import (
    MlModelMetadataIn,
    MlModelMetadataListOut,
    MlModelMetadataOut,
    MlModelMetadataUpdate,
)
from app.services import ml_core_service

router = APIRouter(prefix="/ml-model-metadata", tags=["ml-model-metadata"])


@router.get("", response_model=MlModelMetadataListOut)
def list_models(db: Session = Depends(get_db)) -> MlModelMetadataListOut:
    items = ml_core_service.list_models(db)
    out = [MlModelMetadataOut.model_validate(m) for m in items]
    return MlModelMetadataListOut(items=out, total=len(out))


@router.post("", response_model=MlModelMetadataOut, status_code=status.HTTP_201_CREATED)
def create_model(body: MlModelMetadataIn, db: Session = Depends(get_db)) -> MlModelMetadataOut:
    return MlModelMetadataOut.model_validate(ml_core_service.create_model(db, body))


@router.patch("/{model_id}", response_model=MlModelMetadataOut)
def update_model(
    model_id: int, body: MlModelMetadataUpdate, db: Session = Depends(get_db)
) -> MlModelMetadataOut:
    return MlModelMetadataOut.model_validate(ml_core_service.update_model(db, model_id, body))


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: int, db: Session = Depends(get_db)) -> None:
    ml_core_service.delete_model(db, model_id)
