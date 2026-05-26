from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.data.global_locker_players_catalog import (
    GLOBAL_LOCKER_PLAYERS,
    GLOBAL_MARKET_PRESENCE,
    GLOBAL_PLAYER_RELATIONS,
    LEGACY_CODE_ALIASES,
    TIER1_PLAYER_CODES,
)
from app.models.bi_players import BiLockerNetworkPlayer, BiPlayerRelation
from app.schemas.bi_players import BiLockerNetworkPlayerIn, BiPlayerRelationIn
from app.services.crypto_util import new_id


def list_players(db: Session, priority_only: bool = False) -> list[BiLockerNetworkPlayer]:
    q = db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.active.is_(True))
    if priority_only:
        q = q.filter(BiLockerNetworkPlayer.bi_priority_score >= 85)
    return q.order_by(BiLockerNetworkPlayer.sort_order, BiLockerNetworkPlayer.code).all()


def create_player(db: Session, body: BiLockerNetworkPlayerIn) -> BiLockerNetworkPlayer:
    if db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="player_code_exists")
    row = BiLockerNetworkPlayer(
        id=new_id(),
        code=body.code,
        name=body.name,
        player_role=body.player_role,
        parent_group=body.parent_group,
        country=body.country,
        regions_json=json.dumps(body.regions),
        supports_lockers=body.supports_lockers,
        supports_marketplace=body.supports_marketplace,
        integration_mode=body.integration_mode,
        global_tier="TIER1" if body.code in TIER1_PLAYER_CODES else "TIER2",
        bi_priority_score=body.bi_priority_score,
        sort_order=body.sort_order,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _upsert_player(
    db: Session,
    code: str,
    name: str,
    role: str,
    group: str,
    country: str,
    lockers: bool,
    marketplace: bool,
    score: float,
    regions: list[str],
) -> bool:
    """Retorna True se inseriu, False se atualizou existente."""
    row = db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.code == code).first()
    tier = "TIER1" if code in TIER1_PLAYER_CODES else ("TIER2" if score >= 80 else "REGIONAL")
    if row:
        row.name = name
        row.player_role = role
        row.parent_group = group
        row.country = country
        row.regions_json = json.dumps(regions)
        row.supports_lockers = lockers
        row.supports_marketplace = marketplace
        row.bi_priority_score = score
        row.global_tier = tier
        row.sort_order = 100 - int(score)
        row.active = True
        return False
    db.add(
        BiLockerNetworkPlayer(
            id=new_id(),
            code=code,
            name=name,
            player_role=role,
            parent_group=group,
            country=country,
            regions_json=json.dumps(regions),
            supports_lockers=lockers,
            supports_marketplace=marketplace,
            integration_mode="API",
            global_tier=tier,
            bi_priority_score=score,
            sort_order=100 - int(score),
        )
    )
    return True


def _migrate_legacy_aliases(db: Session) -> int:
    """Renomeia códigos legados para canônicos quando o canônico ainda não existe."""
    migrated = 0
    for old, new in LEGACY_CODE_ALIASES.items():
        old_row = db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.code == old).first()
        if not old_row:
            continue
        if db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.code == new).first():
            old_row.active = False
            migrated += 1
            continue
        old_row.code = new
        migrated += 1
    for rel in db.query(BiPlayerRelation).all():
        fr = LEGACY_CODE_ALIASES.get(rel.from_player_code, rel.from_player_code)
        to = LEGACY_CODE_ALIASES.get(rel.to_player_code, rel.to_player_code)
        if fr != rel.from_player_code:
            rel.from_player_code = fr
        if to != rel.to_player_code:
            rel.to_player_code = to
    return migrated


def seed_players(db: Session) -> dict[str, int]:
    inserted = 0
    updated = 0
    for code, name, role, group, country, lockers, marketplace, score, regions in GLOBAL_LOCKER_PLAYERS:
        if _upsert_player(db, code, name, role, group, country, lockers, marketplace, score, regions):
            inserted += 1
        else:
            updated += 1
    migrated = _migrate_legacy_aliases(db)
    rel_count = 0
    for fr, to, rtype in GLOBAL_PLAYER_RELATIONS:
        fr = LEGACY_CODE_ALIASES.get(fr, fr)
        to = LEGACY_CODE_ALIASES.get(to, to)
        if db.query(BiPlayerRelation).filter(
            BiPlayerRelation.from_player_code == fr, BiPlayerRelation.to_player_code == to
        ).first():
            continue
        db.add(
            BiPlayerRelation(
                id=new_id(),
                from_player_code=fr,
                to_player_code=to,
                relation_type=rtype,
            )
        )
        rel_count += 1
    db.commit()
    return {
        "players_inserted": inserted,
        "players_updated": updated,
        "legacy_migrated": migrated,
        "relations_inserted": rel_count,
        "catalog_size": len(GLOBAL_LOCKER_PLAYERS),
        "tier1_present": sum(
            1 for c in TIER1_PLAYER_CODES if db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.code == c).first()
        ),
    }


def seed_market_presence_from_catalog(db: Session) -> int:
    from app.models.bi_ops import BiPlayerMarketPresence

    inserted = 0
    for code, country, region, lockers, volume, share in GLOBAL_MARKET_PRESENCE:
        if (
            db.query(BiPlayerMarketPresence)
            .filter(
                BiPlayerMarketPresence.network_player_code == code,
                BiPlayerMarketPresence.country_code == country,
            )
            .first()
        ):
            continue
        db.add(
            BiPlayerMarketPresence(
                id=new_id(),
                network_player_code=code,
                country_code=country,
                region_code=region,
                locker_count_est=lockers,
                parcel_volume_est_monthly=volume,
                market_share_pct=share,
            )
        )
        inserted += 1
    db.commit()
    return inserted


def list_relations(db: Session) -> list[BiPlayerRelation]:
    return db.query(BiPlayerRelation).order_by(BiPlayerRelation.from_player_code).all()


def create_relation(db: Session, body: BiPlayerRelationIn) -> BiPlayerRelation:
    row = BiPlayerRelation(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def tier1_coverage_report(db: Session) -> dict:
    present = [c for c in TIER1_PLAYER_CODES if db.query(BiLockerNetworkPlayer).filter(BiLockerNetworkPlayer.code == c).first()]
    missing = sorted(TIER1_PLAYER_CODES - set(present))
    return {
        "tier1_required": len(TIER1_PLAYER_CODES),
        "tier1_present": len(present),
        "tier1_codes": sorted(present),
        "tier1_missing": missing,
        "coverage_pct": round(100 * len(present) / len(TIER1_PLAYER_CODES), 1) if TIER1_PLAYER_CODES else 100,
    }
