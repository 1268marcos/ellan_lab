from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data.global_locker_players_catalog import GLOBAL_LOCKER_PLAYERS
from app.schemas.integration import (
    HardwareEcosystemPlayerRelationListOut,
    HardwareEcosystemPlayerRelationOut,
    HardwareIntegrationHubSummaryOut,
    HardwareIntegrationReadinessListOut,
    HardwareIntegrationReadinessOut,
    HardwareLockerChannelBindingListOut,
    HardwareLockerChannelBindingOut,
    HardwareMarketplaceBridgeOut,
    HardwarePlayerIntegrationCapabilityListOut,
    HardwarePlayerIntegrationCapabilityOut,
    HardwarePlayerSegmentListOut,
    HardwarePlayerSegmentOut,
)
from app.services import integration_service

router = APIRouter(prefix="/integration-hub", tags=["integration-hub"])


@router.get("/summary", response_model=HardwareIntegrationHubSummaryOut)
def integration_hub_summary(db: Session = Depends(get_db)) -> HardwareIntegrationHubSummaryOut:
    return integration_service.get_integration_hub_summary(db)


@router.get("/segments", response_model=HardwarePlayerSegmentListOut)
def list_segments(db: Session = Depends(get_db)) -> HardwarePlayerSegmentListOut:
    items = integration_service.list_segments(db)
    out = [HardwarePlayerSegmentOut.model_validate(i) for i in items]
    return HardwarePlayerSegmentListOut(items=out, total=len(out))


@router.get("/capabilities", response_model=HardwarePlayerIntegrationCapabilityListOut)
def list_capabilities(
    player_code: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwarePlayerIntegrationCapabilityListOut:
    items = integration_service.list_capabilities(db, player_code=player_code)
    out = [HardwarePlayerIntegrationCapabilityOut.model_validate(i) for i in items]
    return HardwarePlayerIntegrationCapabilityListOut(items=out, total=len(out))


@router.get("/player-relations", response_model=HardwareEcosystemPlayerRelationListOut)
def list_player_relations(
    player_code: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareEcosystemPlayerRelationListOut:
    items = integration_service.list_player_relations(db, player_code=player_code)
    out = [HardwareEcosystemPlayerRelationOut.model_validate(i) for i in items]
    return HardwareEcosystemPlayerRelationListOut(items=out, total=len(out))


@router.get("/channel-bindings", response_model=HardwareLockerChannelBindingListOut)
def list_channel_bindings(
    locker_id: str | None = Query(None),
    channel_type: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HardwareLockerChannelBindingListOut:
    items = integration_service.list_channel_bindings(db, locker_id=locker_id, channel_type=channel_type)
    out = [HardwareLockerChannelBindingOut.model_validate(i) for i in items]
    return HardwareLockerChannelBindingListOut(items=out, total=len(out))


@router.get("/integration-readiness", response_model=HardwareIntegrationReadinessListOut)
def list_integration_readiness(
    band: str | None = Query(None),
    db: Session = Depends(get_db),
) -> HardwareIntegrationReadinessListOut:
    items = integration_service.list_integration_readiness(db, band=band)
    return HardwareIntegrationReadinessListOut(items=items, total=len(items))


@router.get("/marketplace-bridge", response_model=HardwareMarketplaceBridgeOut)
def marketplace_bridge(db: Session = Depends(get_db)) -> HardwareMarketplaceBridgeOut:
    return integration_service.compute_marketplace_bridge(db)


@router.post("/sync-marketplace-mirror")
def sync_marketplace_mirror(db: Session = Depends(get_db)) -> dict:
    stats = integration_service.sync_capabilities_from_catalog(db, GLOBAL_LOCKER_PLAYERS, refresh_existing=True)
    bridge = integration_service.compute_marketplace_bridge(db, GLOBAL_LOCKER_PLAYERS)
    return {
        **stats,
        "capabilities_in_sync": bridge.capabilities_in_sync,
        "marketplace_capability_gaps": bridge.marketplace_capability_gaps,
        "capabilities_catalog_expected": bridge.capabilities_catalog_expected,
        "capabilities_db_enabled": bridge.capabilities_db_enabled,
    }


@router.post("/mirror-marketplace-channel-partners")
def mirror_marketplace_channel_partners(db: Session = Depends(get_db)) -> dict:
    return integration_service.mirror_marketplace_channel_partners(db)
