from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.security_ecosystem_worldwide import (
    DEFAULT_INTEGRATIONS_BY_SEGMENT,
    SECURITY_ECOSYSTEM_PLAYERS,
    SECURITY_PLAYER_SEGMENTS,
    all_player_relations,
    players_by_segment,
    priority_player_codes,
)
from app.models.partner_ecosystem import PartnerEcosystemPlayer
from app.models.security import (
    SecurityCrossDomainGrant,
    SecurityLockerPlayerRegistry,
    SecurityPlayerIntegration,
    SecurityPlayerRelation,
    SecurityPlayerSegment,
    SecurityUserPlayerAccess,
    UserDomainLink,
)
from app.models.user import User
from app.schemas.security import (
    CrossDomainGrantOut,
    DomainLinkOut,
    LockerPlayerListOut,
    LockerPlayerOut,
    LockerPlayerSecurityProfileOut,
    UserPlayerAccessCreateIn,
    UserPlayerAccessListOut,
    UserPlayerAccessOut,
)
from app.services.crypto_util import new_id
from app.services.security_service import _parse_json, _utcnow, write_audit


def _player_out(db: Session, row: SecurityLockerPlayerRegistry) -> LockerPlayerOut:
    grants = (
        db.query(SecurityCrossDomainGrant)
        .filter(
            SecurityCrossDomainGrant.entity_id == row.player_code,
            SecurityCrossDomainGrant.is_active.is_(True),
        )
        .count()
    )
    access = (
        db.query(SecurityUserPlayerAccess)
        .filter(SecurityUserPlayerAccess.player_code == row.player_code, SecurityUserPlayerAccess.is_active.is_(True))
        .count()
    )
    return LockerPlayerOut(
        player_code=row.player_code,
        name=row.name,
        segment=row.segment,
        parent_group=row.parent_group,
        primary_domain=row.primary_domain,
        integration_modes=_parse_json(row.integration_modes_json, []),
        related_domains=_parse_json(row.related_domains_json, []),
        default_permissions=_parse_json(row.default_permission_keys_json, []),
        regions=_parse_json(row.regions_json, []),
        global_tier=row.global_tier,
        ecosystem_player_id=row.ecosystem_player_id,
        locker_operator_ref=row.locker_operator_ref,
        is_active=row.is_active,
        grants_count=grants,
        user_access_count=access,
    )


def sync_locker_player_registry(db: Session) -> dict[str, int]:
    """Sincroniza catálogo mundial + partner_ecosystem_players."""
    counts = {"inserted": 0, "updated": 0}
    now = _utcnow()
    eco_by_code = {p.code: p for p in db.query(PartnerEcosystemPlayer).all()}

    for entry in SECURITY_ECOSYSTEM_PLAYERS:
        code = entry["player_code"]
        eco = eco_by_code.get(code)
        row = db.get(SecurityLockerPlayerRegistry, code)
        payload = {
            "name": entry["name"],
            "segment": entry["segment"],
            "parent_group": entry.get("parent_group") or entry["segment"],
            "primary_domain": entry["primary_domain"],
            "related_domains_json": json.dumps(entry.get("related_domains") or []),
            "default_permission_keys_json": json.dumps(entry.get("default_permissions") or []),
            "regions_json": json.dumps(entry.get("regions") or []),
            "global_tier": entry.get("global_tier") or "REGIONAL",
            "ecosystem_player_id": eco.id if eco else None,
            "locker_operator_ref": entry.get("locker_operator_ref") or (eco.locker_operator_ref if eco else None),
            "integration_modes_json": json.dumps(entry.get("integration_modes") or ["REST"]),
            "external_refs_json": json.dumps(entry.get("external_refs") or {}),
            "is_active": True,
            "metadata_json": json.dumps({"source": "security_ecosystem_worldwide"}),
            "updated_at": now,
        }
        if row:
            for k, v in payload.items():
                setattr(row, k, v)
            counts["updated"] += 1
        else:
            db.add(SecurityLockerPlayerRegistry(player_code=code, created_at=now, **payload))
            counts["inserted"] += 1

    db.commit()
    return counts


def list_locker_players(
    db: Session,
    *,
    priority_only: bool = False,
    segment: str | None = None,
) -> LockerPlayerListOut:
    q = db.query(SecurityLockerPlayerRegistry).filter(SecurityLockerPlayerRegistry.is_active.is_(True))
    if priority_only:
        codes = priority_player_codes()
        q = q.filter(SecurityLockerPlayerRegistry.player_code.in_(codes))
    if segment:
        q = q.filter(SecurityLockerPlayerRegistry.segment == segment)
    rows = q.order_by(SecurityLockerPlayerRegistry.global_tier, SecurityLockerPlayerRegistry.name).all()
    items = [_player_out(db, r) for r in rows]
    pri = sum(1 for i in items if i.global_tier == "PRIORITY")
    return LockerPlayerListOut(items=items, total=len(items), priority_count=pri)


def get_player_security_profile(db: Session, player_code: str) -> LockerPlayerSecurityProfileOut:
    row = db.get(SecurityLockerPlayerRegistry, player_code.upper())
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="locker_player_not_found")
    player = _player_out(db, row)

    grants = (
        db.query(SecurityCrossDomainGrant)
        .filter(
            SecurityCrossDomainGrant.entity_id == player_code,
            SecurityCrossDomainGrant.is_active.is_(True),
        )
        .all()
    )
    suggested = [CrossDomainGrantOut.model_validate(g) for g in grants]

    links = [
        DomainLinkOut(
            id=l.id,
            user_id=l.user_id,
            domain=l.domain,
            entity_type=l.entity_type,
            entity_id=l.entity_id,
            relation=l.relation,
            is_primary=l.is_primary,
            metadata=_parse_json(l.metadata_json, {}),
            created_at=l.created_at,
        )
        for l in db.query(UserDomainLink)
        .filter(UserDomainLink.entity_id == player_code)
        .limit(50)
        .all()
    ]

    eco: dict[str, Any] | None = None
    if row.ecosystem_player_id:
        ep = db.get(PartnerEcosystemPlayer, row.ecosystem_player_id)
        if ep:
            eco = {
                "id": ep.id,
                "code": ep.code,
                "name": ep.name,
                "integration_status": ep.integration_status,
                "finance_catalog_code": ep.finance_catalog_code,
                "locker_operator_ref": ep.locker_operator_ref,
            }

    return LockerPlayerSecurityProfileOut(
        player=player,
        suggested_grants=suggested,
        domain_links=links,
        ecosystem_match=eco,
    )


def seed_player_cross_domain_grants(db: Session) -> dict[str, int]:
    """Cria grants cross-domain para players prioritários (admin + suporte + auditoria)."""
    counts = {"grants": 0, "user_access": 0, "domain_links": 0}
    now = _utcnow()
    priority = priority_player_codes()

    user_matrix = [
        ("usr-admin-ops", "NETWORK_ADMIN", ["INPOST", "DHL", "DPD", "MAGALU", "MERCADOLIVRE", "AMAZON_BR", "CORREIOS"]),
        ("usr-suporte", "SUPPORT", ["INPOST", "CORREIOS", "CTT", "MERCADOLIVRE"]),
        ("usr-auditoria", "AUDITOR", ["DPD", "DHL", "WORTEN", "EL_CORTE_INGLES", "AMAZON_ES"]),
    ]

    for uid, access_role, codes in user_matrix:
        if not db.get(User, uid):
            continue
        for code in codes:
            if code not in priority:
                continue
            reg = db.get(SecurityLockerPlayerRegistry, code)
            if not reg:
                continue

            if not (
                db.query(SecurityUserPlayerAccess)
                .filter(
                    SecurityUserPlayerAccess.user_id == uid,
                    SecurityUserPlayerAccess.player_code == code,
                    SecurityUserPlayerAccess.access_role == access_role,
                )
                .first()
            ):
                db.add(
                    SecurityUserPlayerAccess(
                        id=new_id(),
                        user_id=uid,
                        player_code=code,
                        access_role=access_role,
                        scope_type="NETWORK",
                        granted_by="usr-admin-ops",
                        is_active=True,
                        created_at=now,
                    )
                )
                counts["user_access"] += 1

            perm = (_parse_json(reg.default_permission_keys_json, []) or ["ops.lockers.read"])[0]
            domain = reg.primary_domain
            exists = (
                db.query(SecurityCrossDomainGrant)
                .filter(
                    SecurityCrossDomainGrant.user_id == uid,
                    SecurityCrossDomainGrant.domain_code == domain,
                    SecurityCrossDomainGrant.entity_id == code,
                    SecurityCrossDomainGrant.permission_key == perm,
                )
                .first()
            )
            if not exists:
                db.add(
                    SecurityCrossDomainGrant(
                        id=new_id(),
                        user_id=uid,
                        domain_code=domain,
                        entity_type="LockerPlayer",
                        entity_id=code,
                        entity_label=reg.name,
                        permission_key=perm,
                        scope_type="NETWORK",
                        granted_by="usr-admin-ops",
                        is_active=True,
                        metadata_json=json.dumps({"player_segment": reg.segment, "global_tier": reg.global_tier}),
                        created_at=now,
                    )
                )
                counts["grants"] += 1

            link_domain = reg.primary_domain
            if not (
                db.query(UserDomainLink)
                .filter(
                    UserDomainLink.user_id == uid,
                    UserDomainLink.domain == link_domain,
                    UserDomainLink.entity_id == code,
                )
                .first()
            ):
                db.add(
                    UserDomainLink(
                        id=new_id(),
                        user_id=uid,
                        domain=link_domain,
                        entity_type="LockerPlayer",
                        entity_id=code,
                        relation=access_role,
                        is_primary=code in ("INPOST", "MAGALU", "MERCADOLIVRE"),
                        metadata_json=json.dumps({"name": reg.name, "segment": reg.segment}),
                        created_at=now,
                    )
                )
                counts["domain_links"] += 1

    db.commit()
    return counts


def list_user_player_access(db: Session, user_id: str | None = None, player_code: str | None = None) -> UserPlayerAccessListOut:
    q = db.query(SecurityUserPlayerAccess).filter(SecurityUserPlayerAccess.is_active.is_(True))
    if user_id:
        q = q.filter(SecurityUserPlayerAccess.user_id == user_id)
    if player_code:
        q = q.filter(SecurityUserPlayerAccess.player_code == player_code.upper())
    rows = q.order_by(SecurityUserPlayerAccess.created_at.desc()).all()
    return UserPlayerAccessListOut(items=[UserPlayerAccessOut.model_validate(r) for r in rows], total=len(rows))


def create_user_player_access(db: Session, body: UserPlayerAccessCreateIn) -> UserPlayerAccessOut:
    if not db.get(User, body.user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    code = body.player_code.upper()
    if not db.get(SecurityLockerPlayerRegistry, code):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="locker_player_not_found")
    row = SecurityUserPlayerAccess(
        id=new_id(),
        user_id=body.user_id,
        player_code=code,
        access_role=body.access_role,
        scope_type=body.scope_type,
        granted_by=body.granted_by,
        is_active=True,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=body.granted_by,
        action="USER_PLAYER_ACCESS_GRANTED",
        target_type="LockerPlayer",
        target_id=code,
        new_state={"user_id": body.user_id, "role": body.access_role},
    )
    return UserPlayerAccessOut.model_validate(row)


def locker_players_for_ecosystem_map(db: Session) -> list[dict[str, str]]:
    rows = (
        db.query(SecurityLockerPlayerRegistry)
        .filter(SecurityLockerPlayerRegistry.is_active.is_(True))
        .order_by(SecurityLockerPlayerRegistry.global_tier, SecurityLockerPlayerRegistry.name)
        .limit(80)
        .all()
    )
    return [
        {
            "domain": r.primary_domain,
            "entity_type": "LockerPlayer",
            "entity_id": r.player_code,
            "label": r.name,
            "source": "locker_player_registry",
            "segment": r.segment,
            "parent_group": r.parent_group,
        }
        for r in rows
    ]


def seed_ecosystem_taxonomy(db: Session) -> dict[str, int]:
    counts = {"segments": 0, "relations": 0, "integrations": 0}
    for seg in SECURITY_PLAYER_SEGMENTS:
        if not db.get(SecurityPlayerSegment, seg["code"]):
            db.add(
                SecurityPlayerSegment(
                    code=seg["code"],
                    label=seg["label"],
                    description=seg.get("description"),
                    primary_domain=seg["primary_domain"],
                    sort_order=seg.get("sort_order", 100),
                    icon_key=seg.get("icon_key"),
                    is_active=True,
                )
            )
            counts["segments"] += 1

    registered = {r.player_code for r in db.query(SecurityLockerPlayerRegistry.player_code).all()}
    domain_for_segment = {s["code"]: s["primary_domain"] for s in SECURITY_PLAYER_SEGMENTS}

    for from_c, to_c, rel_type, strength in all_player_relations():
        if from_c not in registered or to_c not in registered:
            continue
        exists = (
            db.query(SecurityPlayerRelation)
            .filter(
                SecurityPlayerRelation.from_player_code == from_c,
                SecurityPlayerRelation.to_player_code == to_c,
                SecurityPlayerRelation.relation_type == rel_type,
            )
            .first()
        )
        if not exists:
            db.add(
                SecurityPlayerRelation(
                    id=new_id(),
                    from_player_code=from_c,
                    to_player_code=to_c,
                    relation_type=rel_type,
                    strength=strength,
                    is_active=True,
                    created_at=_utcnow(),
                )
            )
            counts["relations"] += 1

    for reg in db.query(SecurityLockerPlayerRegistry).filter(SecurityLockerPlayerRegistry.is_active.is_(True)).all():
        templates = DEFAULT_INTEGRATIONS_BY_SEGMENT.get(reg.segment, [("REST", "BIDIRECTIONAL", "OPS_READ")])
        target = domain_for_segment.get(reg.segment, reg.primary_domain)
        for ch, direction, cap in templates:
            exists = (
                db.query(SecurityPlayerIntegration)
                .filter(
                    SecurityPlayerIntegration.player_code == reg.player_code,
                    SecurityPlayerIntegration.capability_key == cap,
                )
                .first()
            )
            if not exists:
                db.add(
                    SecurityPlayerIntegration(
                        id=new_id(),
                        player_code=reg.player_code,
                        channel_type=ch,
                        direction=direction,
                        target_domain=target,
                        capability_key=cap,
                        is_required=cap in ("ORDER_SYNC", "PARCEL_EVENT"),
                        is_active=True,
                        created_at=_utcnow(),
                    )
                )
                counts["integrations"] += 1

    db.commit()
    return counts


def list_player_segments(db: Session) -> "PlayerSegmentListOut":
    from app.schemas.security import PlayerSegmentListOut, PlayerSegmentOut

    rows = db.query(SecurityPlayerSegment).filter(SecurityPlayerSegment.is_active.is_(True)).order_by(SecurityPlayerSegment.sort_order).all()
    items = []
    for s in rows:
        cnt = db.query(SecurityLockerPlayerRegistry).filter(SecurityLockerPlayerRegistry.segment == s.code, SecurityLockerPlayerRegistry.is_active.is_(True)).count()
        items.append(
            PlayerSegmentOut(
                code=s.code,
                label=s.label,
                description=s.description,
                primary_domain=s.primary_domain,
                sort_order=s.sort_order,
                icon_key=s.icon_key,
                player_count=cnt,
            )
        )
    return PlayerSegmentListOut(items=items, total=len(items))


def list_player_relations(
    db: Session,
    *,
    from_code: str | None = None,
    to_code: str | None = None,
    relation_type: str | None = None,
) -> "PlayerRelationListOut":
    from app.schemas.security import PlayerRelationListOut, PlayerRelationOut

    q = db.query(SecurityPlayerRelation).filter(SecurityPlayerRelation.is_active.is_(True))
    if from_code:
        q = q.filter(SecurityPlayerRelation.from_player_code == from_code.upper())
    if to_code:
        q = q.filter(SecurityPlayerRelation.to_player_code == to_code.upper())
    if relation_type:
        q = q.filter(SecurityPlayerRelation.relation_type == relation_type)
    rows = q.limit(500).all()
    return PlayerRelationListOut(items=[PlayerRelationOut.model_validate(r) for r in rows], total=len(rows))


def list_player_integrations(db: Session, player_code: str | None = None) -> "PlayerIntegrationListOut":
    from app.schemas.security import PlayerIntegrationListOut, PlayerIntegrationOut

    q = db.query(SecurityPlayerIntegration).filter(SecurityPlayerIntegration.is_active.is_(True))
    if player_code:
        q = q.filter(SecurityPlayerIntegration.player_code == player_code.upper())
    rows = q.limit(300).all()
    return PlayerIntegrationListOut(items=[PlayerIntegrationOut.model_validate(r) for r in rows], total=len(rows))


def get_ecosystem_taxonomy_summary(db: Session) -> "EcosystemTaxonomySummaryOut":
    from app.schemas.security import EcosystemTaxonomySummaryOut

    by_segment: dict[str, int] = {}
    for seg, cnt in (
        db.query(SecurityLockerPlayerRegistry.segment, func.count())
        .filter(SecurityLockerPlayerRegistry.is_active.is_(True))
        .group_by(SecurityLockerPlayerRegistry.segment)
        .all()
    ):
        by_segment[str(seg)] = int(cnt)

    food = [r.player_code for r in db.query(SecurityLockerPlayerRegistry).filter(SecurityLockerPlayerRegistry.segment == "FOOD_DELIVERY").all()]
    pudo = [r.player_code for r in db.query(SecurityLockerPlayerRegistry).filter(SecurityLockerPlayerRegistry.segment == "COLLECTION_POINT").all()]
    agg = [
        r.player_code
        for r in db.query(SecurityLockerPlayerRegistry).filter(
            SecurityLockerPlayerRegistry.segment.in_(["AGGREGATOR", "LOGISTICS_PLATFORM"])
        ).all()
    ]

    return EcosystemTaxonomySummaryOut(
        total_players=db.query(SecurityLockerPlayerRegistry).filter(SecurityLockerPlayerRegistry.is_active.is_(True)).count(),
        by_segment=by_segment,
        total_relations=db.query(SecurityPlayerRelation).filter(SecurityPlayerRelation.is_active.is_(True)).count(),
        total_integrations=db.query(SecurityPlayerIntegration).filter(SecurityPlayerIntegration.is_active.is_(True)).count(),
        food_delivery_players=food,
        collection_point_players=pudo,
        aggregator_players=agg,
    )
