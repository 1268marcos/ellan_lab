from __future__ import annotations

from sqlalchemy.orm import Session

from app.data.locker_world_players_catalog import (
    LOCKER_PLAYER_ALIASES,
    LOCKER_WORLD_INTEGRATIONS,
    LOCKER_WORLD_PRESENCE,
    LOCKER_WORLD_RELATIONS,
)
from app.models.ecosystem import CapabilityEcosystemPlayer
from app.models.ecosystem_global import (
    CapabilityPlayerIntegration,
    CapabilityPlayerLockerPresence,
    CapabilityPlayerRelation,
)


def seed_locker_world(db: Session, player_map: dict[str, CapabilityEcosystemPlayer]) -> dict[str, int]:
    counts = {
        "players": 0,
        "locker_presences": 0,
        "player_integrations": 0,
        "player_relations": 0,
    }

    for alias_code, alias_name, canonical in LOCKER_PLAYER_ALIASES:
        if alias_code in player_map:
            continue
        base = player_map.get(canonical)
        if not base:
            continue
        row = CapabilityEcosystemPlayer(
            code=alias_code,
            name=alias_name,
            segment_id=base.segment_id,
            country_codes=base.country_codes,
            headquarters_country=base.headquarters_country,
            integration_protocol=base.integration_protocol,
            is_active=True,
            metadata_json={"alias_of": canonical, "locker_hub": True},
        )
        db.add(row)
        db.flush()
        player_map[alias_code] = row
        counts["players"] += 1

    for pcode, role, prog_code, prog_name, region, inb, outb, ret, meta in LOCKER_WORLD_PRESENCE:
        player = player_map.get(pcode)
        if not player:
            continue
        exists = (
            db.query(CapabilityPlayerLockerPresence)
            .filter(
                CapabilityPlayerLockerPresence.player_id == player.id,
                CapabilityPlayerLockerPresence.program_code == prog_code,
            )
            .first()
        )
        if exists:
            continue
        db.add(
            CapabilityPlayerLockerPresence(
                player_id=player.id,
                player_code=pcode,
                locker_role=role,
                program_code=prog_code,
                program_name=prog_name,
                region_scope=region,
                supports_inbound=inb,
                supports_outbound=outb,
                supports_returns=ret,
                metadata_json=meta,
                is_active=True,
            )
        )
        counts["locker_presences"] += 1
        merged = dict(player.metadata_json or {})
        merged["locker_world"] = True
        player.metadata_json = merged

    for pcode, mode, direction, auth, wh, sandbox, prod in LOCKER_WORLD_INTEGRATIONS:
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

    for from_c, to_c, rel_type, notes in LOCKER_WORLD_RELATIONS:
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

    db.flush()
    return counts
