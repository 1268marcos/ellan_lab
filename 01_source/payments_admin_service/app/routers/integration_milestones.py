from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.value_features import (
    IntegrationMilestoneIn,
    IntegrationMilestoneListOut,
    IntegrationMilestoneOut,
    IntegrationMilestoneUpdate,
)
from app.services import value_features_service

router = APIRouter(prefix="/integration-milestones", tags=["integration-milestones"])


@router.get("", response_model=IntegrationMilestoneListOut)
def list_items(
    player_code: str | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> IntegrationMilestoneListOut:
    items = value_features_service.list_milestones(
        db, player_code=player_code, status=status, limit=limit
    )
    out = [IntegrationMilestoneOut.model_validate(i) for i in items]
    return IntegrationMilestoneListOut(items=out, total=len(out))


@router.get("/{milestone_id}", response_model=IntegrationMilestoneOut)
def get_item(milestone_id: str, db: Session = Depends(get_db)) -> IntegrationMilestoneOut:
    row = value_features_service.get_milestone(db, milestone_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="milestone_not_found")
    return IntegrationMilestoneOut.model_validate(row)


@router.post("", response_model=IntegrationMilestoneOut, status_code=status.HTTP_201_CREATED)
def create_item(body: IntegrationMilestoneIn, db: Session = Depends(get_db)) -> IntegrationMilestoneOut:
    return IntegrationMilestoneOut.model_validate(value_features_service.create_milestone(db, body))


@router.patch("/{milestone_id}", response_model=IntegrationMilestoneOut)
def update_item(
    milestone_id: str, body: IntegrationMilestoneUpdate, db: Session = Depends(get_db)
) -> IntegrationMilestoneOut:
    row = value_features_service.update_milestone(db, milestone_id, body)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="milestone_not_found")
    return IntegrationMilestoneOut.model_validate(row)


@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(milestone_id: str, db: Session = Depends(get_db)) -> None:
    if not value_features_service.delete_milestone(db, milestone_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="milestone_not_found")
