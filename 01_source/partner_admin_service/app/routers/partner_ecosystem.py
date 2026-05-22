from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner_ecosystem import (
    EcosystemLinkCreateIn,
    EcosystemLinkListOut,
    EcosystemLinkOut,
    EcosystemPlayerListOut,
    EcosystemSummaryOut,
    EcosystemSyncOut,
    IntegrationMatrixGroupOut,
    MarketPresenceOut,
    PlayerCapabilityOut,
    PlayerRelationOut,
)
from app.services import partner_ecosystem_professional_service as pro
from app.services import partner_ecosystem_service as svc

router = APIRouter(tags=["partner-ecosystem"])
players_router = APIRouter(prefix="/ecosystem/players", tags=["partner-ecosystem-players"])


@players_router.get("", response_model=EcosystemPlayerListOut)
def list_ecosystem_players(
    active_only: bool = Query(False),
    parent_group: str | None = Query(None),
    country: str | None = Query(None),
    priority_only: bool = Query(False),
    global_tier: str | None = Query(None),
    supports_lockers: bool | None = Query(None),
    db: Session = Depends(get_db),
) -> EcosystemPlayerListOut:
    return svc.list_players(
        db,
        active_only=active_only,
        parent_group=parent_group,
        country=country,
        priority_only=priority_only,
        global_tier=global_tier,
        supports_lockers=supports_lockers,
    )


@players_router.post("/sync-catalog", response_model=EcosystemSyncOut)
def sync_ecosystem_catalog(db: Session = Depends(get_db)) -> EcosystemSyncOut:
    return svc.sync_catalog(db)


@players_router.post("/seed-priority-partners")
def seed_priority_partners(db: Session = Depends(get_db)) -> dict[str, int]:
    return svc.seed_priority_partner_records(db)


@players_router.post("/seed-professional")
def seed_professional_ecosystem(db: Session = Depends(get_db)) -> dict[str, Any]:
    out = pro.seed_professional_ecosystem(db)
    from app.services import partner_capability_webhook_service as cap_wh
    from app.services import partner_global_ops_service as global_ops

    out["capability_webhooks_mirror"] = cap_wh.mirror_webhooks_from_capabilities(db)
    out["global_ops"] = global_ops.seed_global_ops(db)
    return out


@players_router.get("/summary", response_model=EcosystemSummaryOut)
def ecosystem_summary(db: Session = Depends(get_db)) -> EcosystemSummaryOut:
    return EcosystemSummaryOut(**pro.ecosystem_summary(db))


@players_router.get("/integration-matrix", response_model=list[IntegrationMatrixGroupOut])
def ecosystem_integration_matrix(db: Session = Depends(get_db)) -> list[IntegrationMatrixGroupOut]:
    return [IntegrationMatrixGroupOut(**g) for g in pro.integration_matrix(db)]


@players_router.get("/capabilities", response_model=list[PlayerCapabilityOut])
def list_ecosystem_capabilities(
    player_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[PlayerCapabilityOut]:
    return [PlayerCapabilityOut(**r) for r in pro.list_player_capabilities(db, player_code)]


@players_router.get("/relations", response_model=list[PlayerRelationOut])
def list_ecosystem_relations(
    player_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[PlayerRelationOut]:
    return [PlayerRelationOut(**r) for r in pro.list_player_relations(db, player_code)]


@players_router.get("/market-presence", response_model=list[MarketPresenceOut])
def list_ecosystem_market_presence(
    country: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[MarketPresenceOut]:
    return [MarketPresenceOut(**r) for r in pro.list_market_presence(db, country)]


@router.get("/partners/{partner_id}/ecosystem-links", response_model=EcosystemLinkListOut)
def list_partner_ecosystem_links(
    partner_id: str,
    partner_type: str | None = Query(None),
    db: Session = Depends(get_db),
) -> EcosystemLinkListOut:
    return svc.list_links(db, partner_id, partner_type)


@router.post("/partners/{partner_id}/ecosystem-links", response_model=EcosystemLinkOut)
def create_partner_ecosystem_link(
    partner_id: str,
    body: EcosystemLinkCreateIn,
    db: Session = Depends(get_db),
) -> EcosystemLinkOut:
    return svc.create_link(db, partner_id, body)


@router.delete("/partners/{partner_id}/ecosystem-links/{link_id}", status_code=204)
def delete_partner_ecosystem_link(
    partner_id: str,
    link_id: str,
    db: Session = Depends(get_db),
) -> None:
    svc.delete_link(db, partner_id, link_id)
