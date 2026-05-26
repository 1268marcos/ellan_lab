from __future__ import annotations

from collections import Counter
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.channel_players_catalog import CHANNEL_PLAYERS_CATALOG
from app.data.player_relationships_catalog import PLAYER_RELATIONSHIPS
from app.data.player_segments_catalog import PARTNER_SEGMENT_MAP, PLAYER_SEGMENTS
from app.data.world_corridors_catalog import CORRIDOR_PLAYER_LINKS, WORLD_CORRIDORS
from app.models.marketplace_extended import MarketplaceChannelPartner
from app.models.marketplace_player_ecosystem import (
    MarketplaceChannelPartnerSegment,
    MarketplaceCorridor,
    MarketplaceCorridorPlayer,
    MarketplacePlayerRelationship,
    MarketplacePlayerSegment,
    SellerPlayerIntegrationPlan,
)
from app.schemas.marketplace_player_ecosystem import SellerIntegrationPlanCreateIn
from app.services.crypto_util import new_id
from app.services.seller_service import get_seller_or_404


def _partner_code_map(db: Session) -> dict[str, str]:
    return {p.id: p.code for p in db.query(MarketplaceChannelPartner).all()}


def seed_player_ecosystem(db: Session) -> dict[str, int]:
    counts = {
        "segments": 0,
        "partner_segments": 0,
        "relationships": 0,
        "corridors": 0,
        "corridor_players": 0,
        "integration_plans_demo": 0,
    }

    for spec in PLAYER_SEGMENTS:
        if not db.get(MarketplacePlayerSegment, spec["code"]):
            db.add(MarketplacePlayerSegment(**spec))
            counts["segments"] += 1

    partners_by_code = {p.code: p for p in db.query(MarketplaceChannelPartner).all()}

    for code, segment_codes in PARTNER_SEGMENT_MAP.items():
        partner = partners_by_code.get(code)
        if not partner:
            continue
        for i, seg in enumerate(segment_codes):
            exists = (
                db.query(MarketplaceChannelPartnerSegment)
                .filter(
                    MarketplaceChannelPartnerSegment.channel_partner_id == partner.id,
                    MarketplaceChannelPartnerSegment.segment_code == seg,
                )
                .first()
            )
            if exists:
                continue
            db.add(
                MarketplaceChannelPartnerSegment(
                    id=new_id(),
                    channel_partner_id=partner.id,
                    segment_code=seg,
                    is_primary=(i == 0),
                )
            )
            counts["partner_segments"] += 1

    for from_id, to_id, rel_type, corridor, notes in PLAYER_RELATIONSHIPS:
        exists = (
            db.query(MarketplacePlayerRelationship)
            .filter(
                MarketplacePlayerRelationship.from_partner_id == from_id,
                MarketplacePlayerRelationship.to_partner_id == to_id,
                MarketplacePlayerRelationship.relationship_type == rel_type,
            )
            .first()
        )
        if exists:
            continue
        if not db.get(MarketplaceChannelPartner, from_id) or not db.get(MarketplaceChannelPartner, to_id):
            continue
        db.add(
            MarketplacePlayerRelationship(
                id=new_id(),
                from_partner_id=from_id,
                to_partner_id=to_id,
                relationship_type=rel_type,
                corridor_code=corridor,
                notes=notes,
            )
        )
        counts["relationships"] += 1

    for spec in WORLD_CORRIDORS:
        if not db.get(MarketplaceCorridor, spec["code"]):
            db.add(MarketplaceCorridor(**spec))
            counts["corridors"] += 1

    for corridor_code, partner_id, role, prio in CORRIDOR_PLAYER_LINKS:
        if not db.get(MarketplaceChannelPartner, partner_id):
            continue
        exists = (
            db.query(MarketplaceCorridorPlayer)
            .filter(
                MarketplaceCorridorPlayer.corridor_code == corridor_code,
                MarketplaceCorridorPlayer.channel_partner_id == partner_id,
                MarketplaceCorridorPlayer.player_role_in_corridor == role,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            MarketplaceCorridorPlayer(
                id=new_id(),
                corridor_code=corridor_code,
                channel_partner_id=partner_id,
                player_role_in_corridor=role,
                priority=prio,
            )
        )
        counts["corridor_players"] += 1

    demo_plans = [
        ("mk-seller-demo-001", "mcp-meli", "OAUTH_MARKETPLACE", "ACTIVE", "ORDERS_POLL", None, "BR-BR-MARKETPLACE-LOCKER"),
        ("mk-seller-demo-001", "mcp-magalu", "OAUTH_MARKETPLACE", "ACTIVE", "ORDERS_WEBHOOK", None, "BR-BR-MARKETPLACE-LOCKER"),
        ("mk-seller-demo-001", "mcp-melhor-envio", "AGGREGATOR_HUB", "ACTIVE", "LABEL_API", "mcp-correios", "BR-BR-MARKETPLACE-LOCKER"),
        ("mk-seller-demo-001", "mcp-inpost", "LOCKER_NETWORK_API", "PLANNED", "LOCKER_INVENTORY", None, "EU-PL-LOCKER-HUB"),
        ("mk-seller-demo-001", "mcp-dhl", "CARRIER_DIRECT", "PLANNED", "LABEL_API", None, "EU-UK-CROSS-BORDER"),
        ("mk-seller-demo-001", "mcp-sendcloud", "AGGREGATOR_HUB", "PLANNED", "LABEL_API", "mcp-dpd", "EU-NL-BENELUX-AGG"),
    ]
    for seller_id, pid, path, st, cap, via, corridor in demo_plans:
        if not db.get(MarketplaceChannelPartner, pid):
            continue
        exists = (
            db.query(SellerPlayerIntegrationPlan)
            .filter(
                SellerPlayerIntegrationPlan.seller_id == seller_id,
                SellerPlayerIntegrationPlan.channel_partner_id == pid,
                SellerPlayerIntegrationPlan.integration_path == path,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            SellerPlayerIntegrationPlan(
                id=new_id(),
                seller_id=seller_id,
                channel_partner_id=pid,
                integration_path=path,
                status=st,
                primary_capability=cap,
                via_partner_id=via,
                corridor_code=corridor,
            )
        )
        counts["integration_plans_demo"] += 1

    db.commit()
    return counts


def list_segments(db: Session) -> list[dict]:
    seg_counts = dict(
        db.query(MarketplaceChannelPartnerSegment.segment_code, func.count())
        .group_by(MarketplaceChannelPartnerSegment.segment_code)
        .all()
    )
    rows = db.query(MarketplacePlayerSegment).order_by(MarketplacePlayerSegment.sort_order).all()
    return [{**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "partner_count": seg_counts.get(r.code, 0)} for r in rows]


def list_relationships(db: Session, partner_id: str | None = None) -> list[dict]:
    q = db.query(MarketplacePlayerRelationship).filter(MarketplacePlayerRelationship.active.is_(True))
    if partner_id:
        q = q.filter(
            (MarketplacePlayerRelationship.from_partner_id == partner_id)
            | (MarketplacePlayerRelationship.to_partner_id == partner_id)
        )
    codes = _partner_code_map(db)
    out = []
    for r in q.all():
        out.append(
            {
                **{c.name: getattr(r, c.name) for c in r.__table__.columns},
                "from_partner_code": codes.get(r.from_partner_id),
                "to_partner_code": codes.get(r.to_partner_id),
            }
        )
    return out


def list_corridors(db: Session) -> list[dict]:
    counts = dict(
        db.query(MarketplaceCorridorPlayer.corridor_code, func.count())
        .filter(MarketplaceCorridorPlayer.active.is_(True))
        .group_by(MarketplaceCorridorPlayer.corridor_code)
        .all()
    )
    rows = db.query(MarketplaceCorridor).order_by(MarketplaceCorridor.code).all()
    return [{**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "player_count": counts.get(r.code, 0)} for r in rows]


def get_corridor_detail(db: Session, code: str) -> dict:
    row = db.get(MarketplaceCorridor, code)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="corridor_not_found")
    partners = {p.id: p for p in db.query(MarketplaceChannelPartner).all()}
    players = []
    for cp in (
        db.query(MarketplaceCorridorPlayer)
        .filter(MarketplaceCorridorPlayer.corridor_code == code, MarketplaceCorridorPlayer.active.is_(True))
        .order_by(MarketplaceCorridorPlayer.priority)
        .all()
    ):
        p = partners.get(cp.channel_partner_id)
        players.append(
            {
                **{c.name: getattr(cp, c.name) for c in cp.__table__.columns},
                "partner_code": p.code if p else None,
                "partner_name": p.name if p else None,
            }
        )
    return {
        **{c.name: getattr(row, c.name) for c in row.__table__.columns},
        "player_count": len(players),
        "players": players,
    }


def list_seller_integration_plans(db: Session, seller_id: str) -> list[dict]:
    get_seller_or_404(db, seller_id)
    codes = _partner_code_map(db)
    rows = (
        db.query(SellerPlayerIntegrationPlan)
        .filter(SellerPlayerIntegrationPlan.seller_id == seller_id)
        .order_by(SellerPlayerIntegrationPlan.status, SellerPlayerIntegrationPlan.integration_path)
        .all()
    )
    return [
        {
            **{c.name: getattr(r, c.name) for c in r.__table__.columns},
            "partner_code": codes.get(r.channel_partner_id),
        }
        for r in rows
    ]


def create_integration_plan(db: Session, body: SellerIntegrationPlanCreateIn) -> SellerPlayerIntegrationPlan:
    get_seller_or_404(db, body.seller_id)
    if not db.get(MarketplaceChannelPartner, body.channel_partner_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_partner_not_found")
    exists = (
        db.query(SellerPlayerIntegrationPlan)
        .filter(
            SellerPlayerIntegrationPlan.seller_id == body.seller_id,
            SellerPlayerIntegrationPlan.channel_partner_id == body.channel_partner_id,
            SellerPlayerIntegrationPlan.integration_path == body.integration_path,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="integration_plan_exists")
    row = SellerPlayerIntegrationPlan(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def world_ecosystem_map(db: Session) -> dict:
    parent_groups = Counter(p.get("parent_group", "MARKETPLACE") for p in CHANNEL_PLAYERS_CATALOG)
    return {
        "segments_total": db.query(MarketplacePlayerSegment).count(),
        "partners_total": db.query(MarketplaceChannelPartner).filter(MarketplaceChannelPartner.active.is_(True)).count(),
        "relationships_total": db.query(MarketplacePlayerRelationship).filter(MarketplacePlayerRelationship.active.is_(True)).count(),
        "corridors_total": db.query(MarketplaceCorridor).filter(MarketplaceCorridor.active.is_(True)).count(),
        "catalog_players_total": len(CHANNEL_PLAYERS_CATALOG),
        "parent_groups": dict(parent_groups),
    }
