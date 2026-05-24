from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.value_features import PlayerComplianceListOut, PlayerComplianceOut
from app.services import value_features_service

router = APIRouter(prefix="/player-compliance", tags=["player-compliance"])


@router.get("", response_model=PlayerComplianceListOut)
def list_items(
    player_code: str | None = Query(None),
    country_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> PlayerComplianceListOut:
    items = value_features_service.list_compliance(
        db, player_code=player_code, country_code=country_code, limit=limit
    )
    out = [PlayerComplianceOut.model_validate(i) for i in items]
    return PlayerComplianceListOut(items=out, total=len(out))
