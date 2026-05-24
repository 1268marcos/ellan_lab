from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.value_features import SettlementCorridorListOut, SettlementCorridorOut
from app.services import value_features_service

router = APIRouter(prefix="/settlement-corridors", tags=["settlement-corridors"])


@router.get("", response_model=SettlementCorridorListOut)
def list_items(
    origin_country: str | None = Query(None),
    active_only: bool = Query(True),
    limit: int = Query(100, le=300),
    db: Session = Depends(get_db),
) -> SettlementCorridorListOut:
    items = value_features_service.list_corridors(
        db, origin_country=origin_country, active_only=active_only, limit=limit
    )
    out = [SettlementCorridorOut.model_validate(i) for i in items]
    return SettlementCorridorListOut(items=out, total=len(out))
