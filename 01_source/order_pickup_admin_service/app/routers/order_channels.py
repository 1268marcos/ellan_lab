from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order_ops import (
    ChannelCreateIn,
    ChannelListOut,
    ChannelOut,
    ChannelUpdateIn,
    WorldPlayersReviewOut,
)
from app.services import orders_domain_service

router = APIRouter(prefix="/integration-channels", tags=["integration-channels"])


@router.get("", response_model=ChannelListOut)
def list_channels(
    player_type: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> ChannelListOut:
    items, total = orders_domain_service.list_channels(
        db, player_type=player_type, active=active, limit=limit, offset=offset
    )
    return ChannelListOut(items=items, total=total)


@router.post("", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
def create_channel(body: ChannelCreateIn, db: Session = Depends(get_db)) -> ChannelOut:
    return orders_domain_service.create_channel(db, body)


@router.patch("/{channel_id}", response_model=ChannelOut)
def update_channel(channel_id: str, body: ChannelUpdateIn, db: Session = Depends(get_db)) -> ChannelOut:
    return orders_domain_service.update_channel(db, channel_id, body)


@router.get("/world-review", response_model=WorldPlayersReviewOut)
def world_review(db: Session = Depends(get_db)) -> WorldPlayersReviewOut:
    return WorldPlayersReviewOut.model_validate(orders_domain_service.world_players_review(db))


@router.post("/sync-world-players", response_model=dict)
def sync_world_players(db: Session = Depends(get_db)) -> dict:
    return orders_domain_service.sync_world_player_catalog(db)


@router.post("/seed-catalog", response_model=dict)
def seed_catalog(db: Session = Depends(get_db)) -> dict:
    return orders_domain_service.sync_world_player_catalog(db)
