from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.value_features import IntegrationIncidentListOut, IntegrationIncidentOut
from app.services import value_features_service

router = APIRouter(prefix="/integration-incidents", tags=["integration-incidents"])


@router.get("", response_model=IntegrationIncidentListOut)
def list_items(
    status: str | None = Query(None),
    player_code: str | None = Query(None),
    limit: int = Query(100, le=300),
    db: Session = Depends(get_db),
) -> IntegrationIncidentListOut:
    items = value_features_service.list_incidents(
        db, status=status, player_code=player_code, limit=limit
    )
    out = [IntegrationIncidentOut.model_validate(i) for i in items]
    return IntegrationIncidentListOut(items=out, total=len(out))
