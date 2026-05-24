from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data.locker_network_players_catalog import PRIORITY_LOCKER_CODES
from app.schemas.ml_network import (
    MlLockerNetworkPlayerListOut,
    MlLockerNetworkPlayerOut,
    MlNetworkMlProfileListOut,
    MlNetworkMlProfileOut,
    MlNetworkSeedResultOut,
)
from app.schemas.ml_ecosystem import (
    MlEcosystemSummaryOut,
    MlIntegrationCapabilityListOut,
    MlIntegrationCapabilityOut,
    MlMarketPresenceListOut,
    MlMarketPresenceOut,
    MlPlayerCapabilityListOut,
    MlPlayerCapabilityOut,
    MlPlayerRelationListOut,
    MlPlayerRelationOut,
)
from app.services import ecosystem_service, network_players_service

router = APIRouter(tags=["ml-network-players"])


@router.get("/ml-locker-network-players", response_model=MlLockerNetworkPlayerListOut)
def list_locker_network_players(
    active_only: bool = Query(False),
    parent_group: str | None = Query(None),
    country: str | None = Query(None),
    priority_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> MlLockerNetworkPlayerListOut:
    rows = network_players_service.list_network_players(
        db,
        active_only=active_only,
        parent_group=parent_group,
        country=country,
        priority_only=priority_only,
    )
    items = [MlLockerNetworkPlayerOut.model_validate(network_players_service._row_to_player_out(r)) for r in rows]
    return MlLockerNetworkPlayerListOut(
        items=items,
        total=len(items),
        priority_codes=sorted(PRIORITY_LOCKER_CODES),
    )


@router.get("/ml-locker-network-players/by-finance-code/{finance_catalog_code}", response_model=MlLockerNetworkPlayerOut)
def get_locker_network_player_by_finance_code(
    finance_catalog_code: str, db: Session = Depends(get_db)
) -> MlLockerNetworkPlayerOut:
    row = network_players_service.get_network_player_by_finance_code(db, finance_catalog_code)
    if not row:
        raise HTTPException(status_code=404, detail="ml_network_player_not_found")
    return MlLockerNetworkPlayerOut.model_validate(row)


@router.post("/ml-locker-network-players/seed-from-catalog", response_model=MlNetworkSeedResultOut)
def seed_locker_network_players(db: Session = Depends(get_db)) -> MlNetworkSeedResultOut:
    result = network_players_service.seed_from_catalog(db)
    return MlNetworkSeedResultOut(**result)


@router.get("/ml-network-ml-profiles", response_model=MlNetworkMlProfileListOut)
def list_network_ml_profiles(
    network_player_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> MlNetworkMlProfileListOut:
    items = [MlNetworkMlProfileOut.model_validate(x) for x in network_players_service.list_network_profiles(db, network_player_id)]
    return MlNetworkMlProfileListOut(items=items, total=len(items))


@router.get("/ml-ecosystem/summary", response_model=MlEcosystemSummaryOut)
def ecosystem_summary(db: Session = Depends(get_db)) -> MlEcosystemSummaryOut:
    return MlEcosystemSummaryOut(**ecosystem_service.ecosystem_counts(db))


@router.get("/ml-integration-capabilities", response_model=MlIntegrationCapabilityListOut)
def list_integration_capabilities(db: Session = Depends(get_db)) -> MlIntegrationCapabilityListOut:
    from app.models.ml_ecosystem import MlIntegrationCapabilityCatalog

    rows = db.query(MlIntegrationCapabilityCatalog).order_by(MlIntegrationCapabilityCatalog.sort_order).all()
    items = [MlIntegrationCapabilityOut.model_validate(r) for r in rows]
    return MlIntegrationCapabilityListOut(items=items, total=len(items))


@router.get("/ml-player-capabilities", response_model=MlPlayerCapabilityListOut)
def list_player_capabilities(
    network_player_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> MlPlayerCapabilityListOut:
    items = [MlPlayerCapabilityOut.model_validate(x) for x in ecosystem_service.list_player_capabilities(db, network_player_id)]
    return MlPlayerCapabilityListOut(items=items, total=len(items))


@router.get("/ml-player-relations", response_model=MlPlayerRelationListOut)
def list_player_relations(
    player_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> MlPlayerRelationListOut:
    items = [MlPlayerRelationOut.model_validate(x) for x in ecosystem_service.list_player_relations(db, player_code)]
    return MlPlayerRelationListOut(items=items, total=len(items))


@router.get("/ml-market-presence", response_model=MlMarketPresenceListOut)
def list_market_presence(
    country: str | None = Query(None, min_length=2, max_length=2),
    db: Session = Depends(get_db),
) -> MlMarketPresenceListOut:
    items = [MlMarketPresenceOut.model_validate(x) for x in ecosystem_service.list_market_presence(db, country)]
    return MlMarketPresenceListOut(items=items, total=len(items))
