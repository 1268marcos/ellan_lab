from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.marketplace_player_ecosystem import (
    CorridorDetailOut,
    CorridorListOut,
    CorridorOut,
    CorridorPlayerOut,
    PlayerRelationshipListOut,
    PlayerRelationshipOut,
    PlayerSegmentListOut,
    PlayerSegmentOut,
    SellerIntegrationPlanCreateIn,
    SellerIntegrationPlanListOut,
    SellerIntegrationPlanOut,
    WorldEcosystemMapOut,
)
from app.services import player_ecosystem_service

router = APIRouter(tags=["marketplace-player-ecosystem"])


@router.post("/player-ecosystem/seed")
def seed_ecosystem(db: Session = Depends(get_db)) -> dict:
    return player_ecosystem_service.seed_player_ecosystem(db)


@router.get("/player-ecosystem/world-map", response_model=WorldEcosystemMapOut)
def world_map(db: Session = Depends(get_db)) -> WorldEcosystemMapOut:
    return WorldEcosystemMapOut.model_validate(player_ecosystem_service.world_ecosystem_map(db))


@router.get("/player-ecosystem/segments", response_model=PlayerSegmentListOut)
def list_segments(db: Session = Depends(get_db)) -> PlayerSegmentListOut:
    rows = player_ecosystem_service.list_segments(db)
    segs = [PlayerSegmentOut.model_validate(r) for r in rows]
    return PlayerSegmentListOut(segments=segs, total=len(segs))


@router.get("/player-ecosystem/relationships", response_model=PlayerRelationshipListOut)
def list_relationships(
    partner_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> PlayerRelationshipListOut:
    rows = player_ecosystem_service.list_relationships(db, partner_id=partner_id)
    rels = [PlayerRelationshipOut.model_validate(r) for r in rows]
    return PlayerRelationshipListOut(relationships=rels, total=len(rels))


@router.get("/player-ecosystem/corridors", response_model=CorridorListOut)
def list_corridors(db: Session = Depends(get_db)) -> CorridorListOut:
    rows = player_ecosystem_service.list_corridors(db)
    corridors = [CorridorOut.model_validate(r) for r in rows]
    return CorridorListOut(corridors=corridors, total=len(corridors))


@router.get("/player-ecosystem/corridors/{corridor_code}", response_model=CorridorDetailOut)
def get_corridor(corridor_code: str, db: Session = Depends(get_db)) -> CorridorDetailOut:
    data = player_ecosystem_service.get_corridor_detail(db, corridor_code)
    players = [CorridorPlayerOut.model_validate(p) for p in data.pop("players", [])]
    return CorridorDetailOut.model_validate({**data, "players": players})


@router.get("/sellers/{seller_id}/integration-plans", response_model=SellerIntegrationPlanListOut)
def list_seller_plans(seller_id: str, db: Session = Depends(get_db)) -> SellerIntegrationPlanListOut:
    rows = player_ecosystem_service.list_seller_integration_plans(db, seller_id)
    plans = [SellerIntegrationPlanOut.model_validate(r) for r in rows]
    return SellerIntegrationPlanListOut(plans=plans, total=len(plans))


@router.post(
    "/sellers/{seller_id}/integration-plans",
    response_model=SellerIntegrationPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def create_seller_plan(
    seller_id: str,
    body: SellerIntegrationPlanCreateIn,
    db: Session = Depends(get_db),
) -> SellerIntegrationPlanOut:
    payload = body.model_copy(update={"seller_id": seller_id})
    row = player_ecosystem_service.create_integration_plan(db, payload)
    codes = player_ecosystem_service._partner_code_map(db)
    return SellerIntegrationPlanOut.model_validate(
        {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "partner_code": codes.get(row.channel_partner_id)}
    )
