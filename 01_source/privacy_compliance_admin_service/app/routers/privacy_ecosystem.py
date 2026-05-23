from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.data.privacy_ecosystem_catalog import PLAYER_SEGMENTS, REGULATION_PLAYER_SUMMARY, RELATION_TYPES
from app.models.privacy_ecosystem import PrivacyEcosystemPlayer, PrivacyEcosystemRelation, PrivacyPlayerRegulationLink
from app.models.privacy_player_legal import PrivacyPlayerLegalDocument
from app.schemas.privacy_ecosystem import (
    EcosystemMetaOut,
    EcosystemPlayerListOut,
    EcosystemPlayerOut,
    EcosystemRelationListOut,
    EcosystemRelationOut,
    LockerNetworkPlayerListOut,
    LockerNetworkPlayerOut,
)
from app.schemas.privacy_regulatory import PlayerLegalDocumentListOut, PlayerLegalDocumentOut
from app.services import privacy_ecosystem_service as svc

router = APIRouter(tags=["privacy-ecosystem"])


def _links_by_player(db: Session, player_ids: list[str]) -> dict[str, list[PrivacyPlayerRegulationLink]]:
    if not player_ids:
        return {}
    links = db.query(PrivacyPlayerRegulationLink).filter(PrivacyPlayerRegulationLink.player_id.in_(player_ids)).all()
    out: dict[str, list[PrivacyPlayerRegulationLink]] = {}
    for lk in links:
        out.setdefault(lk.player_id, []).append(lk)
    return out


def _player_out(player: PrivacyEcosystemPlayer, links: list[PrivacyPlayerRegulationLink]) -> EcosystemPlayerOut:
    return EcosystemPlayerOut(
        id=player.id,
        code=player.code,
        name=player.name,
        player_segment=player.player_segment,
        network_type=player.network_type,
        region_group=player.region_group,
        countries=json.loads(player.countries_json or "[]"),
        regulation_codes=[lk.regulation_code for lk in links],
        privacy_roles=list({lk.privacy_role for lk in links}),
        data_shared=list({d for lk in links for d in json.loads(lk.data_shared_json or "[]")}),
        hardware_vendor=player.hardware_vendor,
        global_player_code=player.global_player_code,
        website_url=player.website_url,
        privacy_contact_email=player.privacy_contact_email,
        rental_network_id=player.rental_network_id,
        active=player.active,
    )


@router.get("/ecosystem/players", response_model=EcosystemPlayerListOut)
def list_ecosystem_players(
    regulation_code: str | None = Query(None),
    player_segment: str | None = Query(None),
    region_group: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> EcosystemPlayerListOut:
    rows = svc.list_players(
        db,
        regulation_code=regulation_code,
        player_segment=player_segment,
        region_group=region_group,
        limit=limit,
    )
    link_map = _links_by_player(db, [r.id for r in rows])
    items = [_player_out(r, link_map.get(r.id, [])) for r in rows]
    summary = REGULATION_PLAYER_SUMMARY.get(regulation_code.upper()) if regulation_code else None
    return EcosystemPlayerListOut(
        items=items,
        total=len(items),
        regulation_code=regulation_code.upper() if regulation_code else None,
        player_segment=player_segment.upper() if player_segment else None,
        region_group=region_group.upper() if region_group else None,
        summary=summary,
    )


@router.get("/ecosystem/relations", response_model=EcosystemRelationListOut)
def list_ecosystem_relations(
    player_code: str | None = Query(None),
    limit: int = Query(200, le=500),
    db: Session = Depends(get_db),
) -> EcosystemRelationListOut:
    rows = svc.list_relations(db, player_code=player_code, limit=limit)
    players = {p.id: p for p in db.query(PrivacyEcosystemPlayer).all()}
    items = []
    for rel in rows:
        fp = players.get(rel.from_player_id)
        tp = players.get(rel.to_player_id)
        if not fp or not tp:
            continue
        items.append(
            EcosystemRelationOut(
                id=rel.id,
                from_player_code=fp.code,
                from_player_name=fp.name,
                to_player_code=tp.code,
                to_player_name=tp.name,
                relation_type=rel.relation_type,
                integration_mode=rel.integration_mode,
                description=rel.description,
                active=rel.active,
            )
        )
    return EcosystemRelationListOut(items=items, total=len(items))


@router.get("/ecosystem/meta", response_model=EcosystemMetaOut)
def ecosystem_meta(db: Session = Depends(get_db)) -> EcosystemMetaOut:
    return EcosystemMetaOut(
        player_segments=PLAYER_SEGMENTS,
        relation_types=RELATION_TYPES,
        regulation_summaries=REGULATION_PLAYER_SUMMARY,
        player_count=db.query(PrivacyEcosystemPlayer).filter(PrivacyEcosystemPlayer.active.is_(True)).count(),
        relation_count=db.query(PrivacyEcosystemRelation).filter(PrivacyEcosystemRelation.active.is_(True)).count(),
    )


@router.get("/locker-networks", response_model=LockerNetworkPlayerListOut)
def list_locker_networks(
    regulation_code: str | None = Query(None, description="Filtrar por marco (GDPR, LGPD, CCPA, …)"),
    player_segment: str | None = Query(None),
    db: Session = Depends(get_db),
) -> LockerNetworkPlayerListOut:
    rows = svc.list_players(db, regulation_code=regulation_code, player_segment=player_segment, limit=200)
    link_map = _links_by_player(db, [r.id for r in rows])
    items = []
    for r in rows:
        links = link_map.get(r.id, [])
        items.append(
            LockerNetworkPlayerOut(
                id=r.id,
                code=r.code,
                name=r.name,
                network_type=r.network_type,
                player_segment=r.player_segment,
                region_group=r.region_group,
                countries=json.loads(r.countries_json or "[]"),
                regulation_codes=[lk.regulation_code for lk in links],
                privacy_role=links[0].privacy_role if links else None,
                data_shared=list({d for lk in links for d in json.loads(lk.data_shared_json or "[]")}),
                website_url=r.website_url,
            )
        )
    summary = REGULATION_PLAYER_SUMMARY.get(regulation_code.upper()) if regulation_code else None
    return LockerNetworkPlayerListOut(
        items=items,
        total=len(items),
        regulation_code=regulation_code.upper() if regulation_code else None,
        summary=summary,
    )


@router.get("/ecosystem/player-legal-documents", response_model=PlayerLegalDocumentListOut)
def list_player_legal_documents(
    player_code: str | None = Query(None),
    regulation_code: str | None = Query(None),
    limit: int = Query(100, le=300),
    db: Session = Depends(get_db),
) -> PlayerLegalDocumentListOut:
    q = db.query(PrivacyPlayerLegalDocument).filter(PrivacyPlayerLegalDocument.active.is_(True))
    if player_code:
        q = q.filter(PrivacyPlayerLegalDocument.player_code == player_code.upper())
    if regulation_code:
        q = q.filter(PrivacyPlayerLegalDocument.regulation_code == regulation_code.upper())
    rows = q.order_by(PrivacyPlayerLegalDocument.player_code, PrivacyPlayerLegalDocument.version.desc()).limit(limit).all()
    return PlayerLegalDocumentListOut(
        items=[PlayerLegalDocumentOut.model_validate(r) for r in rows],
        total=len(rows),
        player_code=player_code.upper() if player_code else None,
    )


@router.get("/ecosystem/players/{player_code}/legal-documents", response_model=PlayerLegalDocumentListOut)
def list_player_legal_documents_by_code(
    player_code: str,
    db: Session = Depends(get_db),
) -> PlayerLegalDocumentListOut:
    rows = (
        db.query(PrivacyPlayerLegalDocument)
        .filter(
            PrivacyPlayerLegalDocument.player_code == player_code.upper(),
            PrivacyPlayerLegalDocument.active.is_(True),
        )
        .order_by(PrivacyPlayerLegalDocument.version.desc())
        .all()
    )
    return PlayerLegalDocumentListOut(
        items=[PlayerLegalDocumentOut.model_validate(r) for r in rows],
        total=len(rows),
        player_code=player_code.upper(),
    )
