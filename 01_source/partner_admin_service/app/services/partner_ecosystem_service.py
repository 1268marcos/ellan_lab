from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.locker_ecosystem_catalog import LOCKER_ECOSYSTEM_CATALOG, PRIORITY_ECOSYSTEM_CODES
from app.models.partner import EcommercePartner, LogisticsPartner
from app.models.partner_ecosystem import PartnerEcosystemLink, PartnerEcosystemPlayer
from app.schemas.partner_ecosystem import (
    EcosystemLinkCreateIn,
    EcosystemLinkListOut,
    EcosystemLinkOut,
    EcosystemPlayerListOut,
    EcosystemPlayerOut,
    EcosystemSyncOut,
)
from app.services.crypto_util import new_id

PRIORITY_GROUPS = frozenset({"LOCKER_NETWORK", "CARRIER_LAST_MILE", "MARKETPLACE"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _regions_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        return list(parsed) if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []


def _player_out(row: PartnerEcosystemPlayer) -> EcosystemPlayerOut:
    return EcosystemPlayerOut(
        id=row.id,
        code=row.code,
        name=row.name,
        player_role=row.player_role,
        parent_group=row.parent_group,
        country=row.country,
        regions=_regions_list(row.regions_json),
        supports_lockers=bool(row.supports_lockers),
        supports_marketplace=bool(row.supports_marketplace),
        integration_mode=row.integration_mode,
        marketplace_channel_id=row.marketplace_channel_id,
        marketplace_channel_code=row.marketplace_channel_code,
        locker_operator_ref=row.locker_operator_ref,
        ecommerce_partner_code=row.ecommerce_partner_code,
        api_docs_url=row.api_docs_url,
        notes=row.notes,
        global_tier=row.global_tier,
        sort_order=row.sort_order,
        active=row.active,
    )


def _resolve_partner(db: Session, partner_id: str) -> None:
    if db.get(EcommercePartner, partner_id) or db.get(LogisticsPartner, partner_id):
        return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="partner_not_found")


_PLAYER_COLUMNS = {
    "code",
    "name",
    "player_role",
    "parent_group",
    "country",
    "regions_json",
    "supports_lockers",
    "supports_marketplace",
    "integration_mode",
    "marketplace_channel_id",
    "marketplace_channel_code",
    "locker_operator_ref",
    "ecommerce_partner_code",
    "api_docs_url",
    "notes",
    "global_tier",
    "sort_order",
    "active",
    "integration_status",
    "website_url",
    "estimated_locker_count",
    "data_source",
}


def sync_catalog(db: Session) -> EcosystemSyncOut:
    inserted = updated = 0
    now = _utcnow()
    for entry in LOCKER_ECOSYSTEM_CATALOG:
        row = db.get(PartnerEcosystemPlayer, entry["id"])
        payload = {k: v for k, v in entry.items() if k != "id" and k in _PLAYER_COLUMNS}
        if row:
            for key, val in payload.items():
                setattr(row, key, val)
            row.updated_at = now
            updated += 1
        else:
            db.add(PartnerEcosystemPlayer(id=entry["id"], created_at=now, updated_at=now, **payload))
            inserted += 1
    db.commit()
    total = db.query(PartnerEcosystemPlayer).count()
    return EcosystemSyncOut(inserted=inserted, updated=updated, total=total)


def list_players(
    db: Session,
    *,
    active_only: bool = False,
    parent_group: str | None = None,
    country: str | None = None,
    priority_only: bool = False,
    global_tier: str | None = None,
    supports_lockers: bool | None = None,
) -> EcosystemPlayerListOut:
    q = db.query(PartnerEcosystemPlayer)
    if active_only:
        q = q.filter(PartnerEcosystemPlayer.active.is_(True))
    if parent_group:
        q = q.filter(PartnerEcosystemPlayer.parent_group == parent_group)
    if country:
        q = q.filter(PartnerEcosystemPlayer.country == country.upper())
    if global_tier:
        q = q.filter(PartnerEcosystemPlayer.global_tier == global_tier.upper())
    if supports_lockers is True:
        q = q.filter(PartnerEcosystemPlayer.supports_lockers.is_(True))
    if priority_only:
        q = q.filter(PartnerEcosystemPlayer.code.in_(PRIORITY_ECOSYSTEM_CODES))
    rows = q.order_by(PartnerEcosystemPlayer.sort_order, PartnerEcosystemPlayer.code).all()
    items = [_player_out(r) for r in rows]
    priority_count = sum(1 for i in items if i.code in PRIORITY_ECOSYSTEM_CODES)
    return EcosystemPlayerListOut(items=items, total=len(items), priority_count=priority_count)


def list_links(db: Session, partner_id: str, partner_type: str | None = None) -> EcosystemLinkListOut:
    _resolve_partner(db, partner_id)
    q = (
        db.query(PartnerEcosystemLink, PartnerEcosystemPlayer)
        .join(PartnerEcosystemPlayer, PartnerEcosystemLink.ecosystem_player_id == PartnerEcosystemPlayer.id)
        .filter(PartnerEcosystemLink.partner_id == partner_id)
    )
    if partner_type:
        q = q.filter(PartnerEcosystemLink.partner_type == partner_type.upper())
    rows = q.order_by(PartnerEcosystemLink.is_primary.desc(), PartnerEcosystemPlayer.sort_order).all()
    items: list[EcosystemLinkOut] = []
    for link, player in rows:
        items.append(
            EcosystemLinkOut(
                id=link.id,
                partner_id=link.partner_id,
                partner_type=link.partner_type,
                ecosystem_player_id=link.ecosystem_player_id,
                player_code=player.code,
                player_name=player.name,
                parent_group=player.parent_group,
                global_tier=player.global_tier,
                link_role=link.link_role,
                is_primary=link.is_primary,
                integration_status=link.integration_status,
                notes=link.notes,
                locker_operator_ref=player.locker_operator_ref,
                marketplace_channel_code=player.marketplace_channel_code,
                created_at=link.created_at,
            )
        )
    return EcosystemLinkListOut(partner_id=partner_id, items=items, total=len(items))


def create_link(db: Session, partner_id: str, body: EcosystemLinkCreateIn) -> EcosystemLinkOut:
    _resolve_partner(db, partner_id)
    player = db.get(PartnerEcosystemPlayer, body.ecosystem_player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ecosystem_player_not_found")
    ptype = body.partner_type.upper()
    exists = (
        db.query(PartnerEcosystemLink)
        .filter(
            PartnerEcosystemLink.partner_id == partner_id,
            PartnerEcosystemLink.partner_type == ptype,
            PartnerEcosystemLink.ecosystem_player_id == body.ecosystem_player_id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ecosystem_link_exists")
    now = _utcnow()
    if body.is_primary:
        db.query(PartnerEcosystemLink).filter(
            PartnerEcosystemLink.partner_id == partner_id,
            PartnerEcosystemLink.partner_type == ptype,
        ).update({"is_primary": False})
    row = PartnerEcosystemLink(
        id=new_id(),
        partner_id=partner_id,
        partner_type=ptype,
        ecosystem_player_id=body.ecosystem_player_id,
        link_role=body.link_role,
        is_primary=body.is_primary,
        integration_status=body.integration_status,
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return EcosystemLinkOut(
        id=row.id,
        partner_id=row.partner_id,
        partner_type=row.partner_type,
        ecosystem_player_id=row.ecosystem_player_id,
        player_code=player.code,
        player_name=player.name,
        parent_group=player.parent_group,
        global_tier=player.global_tier,
        link_role=row.link_role,
        is_primary=row.is_primary,
        integration_status=row.integration_status,
        notes=row.notes,
        locker_operator_ref=player.locker_operator_ref,
        marketplace_channel_code=player.marketplace_channel_code,
        created_at=row.created_at,
    )


def delete_link(db: Session, partner_id: str, link_id: str) -> None:
    row = db.get(PartnerEcosystemLink, link_id)
    if not row or row.partner_id != partner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ecosystem_link_not_found")
    db.delete(row)
    db.commit()


def count_links(db: Session, partner_id: str) -> int:
    return db.query(PartnerEcosystemLink).filter(PartnerEcosystemLink.partner_id == partner_id).count()


def _infer_partner_type(player: PartnerEcosystemPlayer) -> str:
    if player.parent_group == "MARKETPLACE" or player.player_role in ("ECOMMERCE_CHANNEL",):
        return "ECOMMERCE"
    return "LOGISTICS"


def _integration_type_for(mode: str) -> str:
    if "OAUTH" in (mode or "").upper():
        return "OAUTH2"
    if mode in ("WEBHOOK_INBOUND",):
        return "WEBHOOK"
    return "REST"


def _partner_code(player: PartnerEcosystemPlayer) -> str:
    return (player.ecommerce_partner_code or player.code)[:32]


def _partner_id_for(player: PartnerEcosystemPlayer, partner_type: str) -> str:
    slug = player.code.lower().replace("_", "-")
    prefix = "ec-pri" if partner_type == "ECOMMERCE" else "lg-pri"
    return f"{prefix}-{slug}"[:36]


def _link_role_for(player: PartnerEcosystemPlayer) -> str:
    if player.parent_group == "LOCKER_NETWORK":
        return "LOCKER_NETWORK"
    if player.parent_group == "CARRIER_LAST_MILE":
        return "CARRIER"
    if player.parent_group == "LOGISTICS_PLATFORM":
        return "AGGREGATOR"
    return "CHANNEL"


def _ensure_self_ecosystem_link(
    db: Session,
    *,
    partner_id: str,
    partner_type: str,
    player: PartnerEcosystemPlayer,
) -> bool:
    exists = (
        db.query(PartnerEcosystemLink)
        .filter(
            PartnerEcosystemLink.partner_id == partner_id,
            PartnerEcosystemLink.partner_type == partner_type,
            PartnerEcosystemLink.ecosystem_player_id == player.id,
        )
        .first()
    )
    if exists:
        return False
    now = _utcnow()
    live_codes = {"MERCADOLIVRE", "MAGALU", "AMAZON_BR", "INPOST", "DHL", "CORREIOS"}
    db.add(
        PartnerEcosystemLink(
            id=new_id(),
            partner_id=partner_id,
            partner_type=partner_type,
            ecosystem_player_id=player.id,
            link_role=_link_role_for(player),
            is_primary=True,
            integration_status="LIVE" if player.code in live_codes else "PLANNED",
            notes=f"Cadastro OPS — espelho catálogo {player.code}",
            created_at=now,
            updated_at=now,
        )
    )
    return True


def seed_priority_partner_records(db: Session) -> dict[str, int]:
    """Cria um registro em ecommerce_partners ou logistics_partners por player prioritário + vínculo catálogo."""
    sync_catalog(db)
    counts = {"ecommerce": 0, "logistics": 0, "ecosystem_links": 0}
    players = (
        db.query(PartnerEcosystemPlayer)
        .filter(PartnerEcosystemPlayer.code.in_(PRIORITY_ECOSYSTEM_CODES))
        .order_by(PartnerEcosystemPlayer.sort_order)
        .all()
    )
    now = _utcnow()
    for player in players:
        partner_type = _infer_partner_type(player)
        code = _partner_code(player)
        pid = _partner_id_for(player, partner_type)
        integration = _integration_type_for(player.integration_mode)

        if partner_type == "ECOMMERCE":
            row = db.get(EcommercePartner, pid) or db.query(EcommercePartner).filter(EcommercePartner.code == code).first()
            if not row:
                db.add(
                    EcommercePartner(
                        id=pid,
                        name=player.name,
                        code=code,
                        integration_type=integration,
                        api_base_url=player.api_docs_url,
                        sla_pickup_hours=72,
                        active=True,
                        country=player.country,
                        status="ACTIVE",
                        tier="PRIORITY",
                        support_email=f"ops+{code.lower().replace('-', '')}@ellanlab.example",
                        created_at=now,
                        updated_at=now,
                    )
                )
                counts["ecommerce"] += 1
                partner_id = pid
            else:
                partner_id = row.id
        else:
            row = db.get(LogisticsPartner, pid) or db.query(LogisticsPartner).filter(LogisticsPartner.code == code).first()
            if not row:
                tracking = None
                if player.locker_operator_ref:
                    tracking = f"https://track.example/{player.code.lower()}/{{code}}"
                db.add(
                    LogisticsPartner(
                        id=pid,
                        name=player.name,
                        code=code,
                        integration_type=integration,
                        api_base_url=player.api_docs_url,
                        tracking_url_template=tracking,
                        default_sla_hours=72,
                        active=True,
                        country=player.country,
                        created_at=now,
                        updated_at=now,
                    )
                )
                counts["logistics"] += 1
                partner_id = pid
            else:
                partner_id = row.id

        if _ensure_self_ecosystem_link(db, partner_id=partner_id, partner_type=partner_type, player=player):
            counts["ecosystem_links"] += 1

    db.commit()
    return counts


def seed_demo_links(db: Session, partner_id: str = "partner_demo_001") -> int:
    """Vincula demo a players prioritários (InPost, DHL, ML, Magalu, Amazon, DPD, Correios, CTT, Worten, El Corte)."""
    sync_catalog(db)
    priority_ids = [
        "mcp-inpost",
        "mcp-dhl",
        "mcp-dpd",
        "mcp-ctt",
        "mcp-correios",
        "mcp-magalu",
        "mcp-meli",
        "mcp-amazon-br",
        "mcp-worten",
        "mcp-elcorte",
    ]
    created = 0
    for idx, pid in enumerate(priority_ids):
        player = db.get(PartnerEcosystemPlayer, pid)
        if not player:
            continue
        exists = (
            db.query(PartnerEcosystemLink)
            .filter(
                PartnerEcosystemLink.partner_id == partner_id,
                PartnerEcosystemLink.ecosystem_player_id == pid,
            )
            .first()
        )
        if exists:
            continue
        link_role = "LOCKER_NETWORK" if player.parent_group == "LOCKER_NETWORK" else "CHANNEL"
        if player.parent_group == "CARRIER_LAST_MILE":
            link_role = "CARRIER"
        now = _utcnow()
        db.add(
            PartnerEcosystemLink(
                id=new_id(),
                partner_id=partner_id,
                partner_type="ECOMMERCE",
                ecosystem_player_id=pid,
                link_role=link_role,
                is_primary=idx == 0,
                integration_status="LIVE" if player.code in ("MERCADOLIVRE", "MAGALU") else "PLANNED",
                notes=f"Seed OPS — {player.name}",
                created_at=now,
                updated_at=now,
            )
        )
        created += 1
    db.commit()
    return created
