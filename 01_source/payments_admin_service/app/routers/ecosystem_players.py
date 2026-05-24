from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.cross_domain import (
    PaymentEcosystemPlayerIn,
    PaymentEcosystemPlayerListOut,
    PaymentEcosystemPlayerOut,
    PaymentEcosystemPlayerUpdate,
)
from app.services import cross_domain_service

router = APIRouter(prefix="/ecosystem-players", tags=["ecosystem-players"])


@router.get("", response_model=PaymentEcosystemPlayerListOut)
def list_items(
    segment: str | None = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> PaymentEcosystemPlayerListOut:
    items = cross_domain_service.list_ecosystem_players(db, segment=segment, active_only=active_only, limit=limit)
    out = [PaymentEcosystemPlayerOut.model_validate(i) for i in items]
    return PaymentEcosystemPlayerListOut(items=out, total=len(out))


@router.post("", response_model=PaymentEcosystemPlayerOut, status_code=status.HTTP_201_CREATED)
def create_item(body: PaymentEcosystemPlayerIn, db: Session = Depends(get_db)) -> PaymentEcosystemPlayerOut:
    return PaymentEcosystemPlayerOut.model_validate(cross_domain_service.create_ecosystem_player(db, body))


@router.patch("/{player_id}", response_model=PaymentEcosystemPlayerOut)
def update_item(
    player_id: str, body: PaymentEcosystemPlayerUpdate, db: Session = Depends(get_db)
) -> PaymentEcosystemPlayerOut:
    return PaymentEcosystemPlayerOut.model_validate(
        cross_domain_service.update_ecosystem_player(db, player_id, body)
    )
