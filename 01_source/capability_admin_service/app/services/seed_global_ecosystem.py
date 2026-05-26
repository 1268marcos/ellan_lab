from __future__ import annotations

from sqlalchemy.orm import Session

from app.data.global_players_catalog import (
    GLOBAL_PLAYERS,
    INTEGRATION_MODES,
    PLAYER_INTEGRATIONS,
    PLAYER_RELATIONS,
)
from app.models.ecosystem import CapabilityEcosystemPlayer, CapabilityEcosystemSegment
from app.models.ecosystem_global import (
    CapabilityIntegrationMode,
    CapabilityPlayerIntegration,
    CapabilityPlayerRelation,
)
from app.services.seed_locker_world import seed_locker_world

EXTRA_SEGMENTS: list[tuple[str, str, int]] = [
    ("LOCKER_OPERATOR", "Operador de rede de lockers", 15),
]


def seed_global_ecosystem(db: Session) -> dict[str, int]:
    counts = {
        "segments": 0,
        "players": 0,
        "integration_modes": 0,
        "player_integrations": 0,
        "player_relations": 0,
        "locker_presences": 0,
    }

    segment_map: dict[str, CapabilityEcosystemSegment] = {
        s.code: s for s in db.query(CapabilityEcosystemSegment).all()
    }
    base_segments = [
        ("LOCKER_NETWORK", "Rede de lockers", 10),
        ("CARRIER", "Carrier global", 20),
        ("MARKETPLACE", "Marketplace", 30),
        ("COLLECTION_POINT", "Ponto de coleta", 40),
        ("AGGREGATOR", "Agregador / hub", 50),
        ("FOOD_DELIVERY", "Food delivery", 60),
    ]
    for code, name, order in base_segments + EXTRA_SEGMENTS:
        if code not in segment_map:
            row = CapabilityEcosystemSegment(code=code, name=name, sort_order=order, is_active=True)
            db.add(row)
            db.flush()
            segment_map[code] = row
            counts["segments"] += 1

    player_map: dict[str, CapabilityEcosystemPlayer] = {
        p.code: p for p in db.query(CapabilityEcosystemPlayer).all()
    }
    for code, name, seg, countries, hq, protocol, meta in GLOBAL_PLAYERS:
        if code in player_map:
            continue
        seg_row = segment_map.get(seg)
        if not seg_row:
            continue
        row = CapabilityEcosystemPlayer(
            code=code,
            name=name,
            segment_id=seg_row.id,
            country_codes=countries,
            headquarters_country=hq,
            integration_protocol=protocol,
            is_active=True,
            metadata_json=meta,
        )
        db.add(row)
        db.flush()
        player_map[code] = row
        counts["players"] += 1

    # legacy alias
    if "AMAZON_HUB" not in player_map and "AMAZON" in player_map:
        amazon = player_map["AMAZON"]
        alias = CapabilityEcosystemPlayer(
            code="AMAZON_HUB",
            name="Amazon Hub (alias)",
            segment_id=amazon.segment_id,
            country_codes=amazon.country_codes,
            headquarters_country=amazon.headquarters_country,
            integration_protocol=amazon.integration_protocol,
            is_active=True,
            metadata_json={"alias_of": "AMAZON"},
        )
        db.add(alias)
        db.flush()
        player_map["AMAZON_HUB"] = alias
        counts["players"] += 1

    for code, name, desc in INTEGRATION_MODES:
        if db.query(CapabilityIntegrationMode).filter(CapabilityIntegrationMode.code == code).first():
            continue
        db.add(CapabilityIntegrationMode(code=code, name=name, description=desc, is_active=True))
        counts["integration_modes"] += 1
    db.flush()

    for pcode, mode, direction, auth, wh, sandbox, prod in PLAYER_INTEGRATIONS:
        player = player_map.get(pcode)
        if not player:
            continue
        exists = (
            db.query(CapabilityPlayerIntegration)
            .filter(
                CapabilityPlayerIntegration.player_id == player.id,
                CapabilityPlayerIntegration.integration_mode_code == mode,
                CapabilityPlayerIntegration.direction == direction,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            CapabilityPlayerIntegration(
                player_id=player.id,
                player_code=pcode,
                integration_mode_code=mode,
                direction=direction,
                auth_type=auth,
                webhook_supported=wh,
                sandbox_available=sandbox,
                production_ready=prod,
                is_active=True,
            )
        )
        counts["player_integrations"] += 1

    for from_c, to_c, rel_type, notes in PLAYER_RELATIONS:
        fp = player_map.get(from_c)
        tp = player_map.get(to_c)
        if not fp or not tp:
            continue
        exists = (
            db.query(CapabilityPlayerRelation)
            .filter(
                CapabilityPlayerRelation.from_player_id == fp.id,
                CapabilityPlayerRelation.to_player_id == tp.id,
                CapabilityPlayerRelation.relation_type == rel_type,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            CapabilityPlayerRelation(
                from_player_id=fp.id,
                to_player_id=tp.id,
                from_player_code=from_c,
                to_player_code=to_c,
                relation_type=rel_type,
                notes=notes,
                is_active=True,
            )
        )
        counts["player_relations"] += 1

    locker_counts = seed_locker_world(db, player_map)
    for k, v in locker_counts.items():
        counts[k] = counts.get(k, 0) + v

    db.flush()
    return counts
