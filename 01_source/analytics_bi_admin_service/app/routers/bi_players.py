from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.bi_players import (
    BiLockerNetworkPlayerIn,
    BiLockerNetworkPlayerListOut,
    BiLockerNetworkPlayerOut,
    BiPlayerRelationIn,
    BiPlayerRelationListOut,
    BiPlayerRelationOut,
)
from app.services import bi_players_service
import json

router = APIRouter(prefix="/bi-locker-network-players", tags=["bi-players"])


def _player_out(row) -> dict:
    data = {c.name: getattr(row, c.name) for c in row.__table__.columns}
    data["regions"] = json.loads(row.regions_json or "[]")
    return data


@router.get("", response_model=BiLockerNetworkPlayerListOut)
def list_players(
    priority_only: bool = Query(False), db: Session = Depends(get_db)
) -> BiLockerNetworkPlayerListOut:
    rows = bi_players_service.list_players(db, priority_only=priority_only)
    return BiLockerNetworkPlayerListOut(
        players=[BiLockerNetworkPlayerOut.model_validate(_player_out(r)) for r in rows],
        total=len(rows),
    )


@router.post("", response_model=BiLockerNetworkPlayerOut, status_code=status.HTTP_201_CREATED)
def create_player(body: BiLockerNetworkPlayerIn, db: Session = Depends(get_db)) -> BiLockerNetworkPlayerOut:
    row = bi_players_service.create_player(db, body)
    return BiLockerNetworkPlayerOut.model_validate(_player_out(row))


@router.post("/seed-global-catalog")
def seed_catalog(db: Session = Depends(get_db)) -> dict:
    return bi_players_service.seed_players(db)


@router.get("/tier1-coverage")
def tier1_coverage(db: Session = Depends(get_db)) -> dict:
    return bi_players_service.tier1_coverage_report(db)


@router.get("/relations", response_model=BiPlayerRelationListOut)
def list_relations(db: Session = Depends(get_db)) -> BiPlayerRelationListOut:
    rows = bi_players_service.list_relations(db)
    return BiPlayerRelationListOut(
        relations=[BiPlayerRelationOut.model_validate(r) for r in rows],
        total=len(rows),
    )


@router.post("/relations", response_model=BiPlayerRelationOut, status_code=status.HTTP_201_CREATED)
def create_relation(body: BiPlayerRelationIn, db: Session = Depends(get_db)) -> BiPlayerRelationOut:
    return BiPlayerRelationOut.model_validate(bi_players_service.create_relation(db, body))
