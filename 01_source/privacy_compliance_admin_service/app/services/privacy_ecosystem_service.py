from __future__ import annotations

import hashlib
import json

from sqlalchemy.orm import Session

from app.data.privacy_ecosystem_catalog import ECOSYSTEM_PLAYERS, ECOSYSTEM_RELATIONS, REGULATION_PLAYER_SUMMARY
from app.models.privacy_ecosystem import (
    PrivacyEcosystemPlayer,
    PrivacyEcosystemRelation,
    PrivacyPlayerRegulationLink,
)


def seed_privacy_ecosystem(db: Session) -> dict[str, int]:
    counts = {"players": 0, "regulation_links": 0, "relations": 0}
    code_to_id: dict[str, str] = {}

    for spec in ECOSYSTEM_PLAYERS:
        existing = db.query(PrivacyEcosystemPlayer).filter(PrivacyEcosystemPlayer.code == spec["code"]).first()
        if not existing:
            row = PrivacyEcosystemPlayer(
                id=spec["id"],
                code=spec["code"],
                name=spec["name"],
                player_segment=spec["player_segment"],
                network_type=spec["network_type"],
                region_group=spec["region_group"],
                countries_json=json.dumps(spec.get("countries") or []),
                hardware_vendor=spec.get("hardware_vendor"),
                global_player_code=spec.get("global_player_code"),
                website_url=spec.get("website_url"),
                privacy_contact_email=spec.get("privacy_contact_email"),
                rental_network_id=spec.get("rental_network_id"),
                active=True,
            )
            db.add(row)
            counts["players"] += 1
            code_to_id[spec["code"]] = spec["id"]
        else:
            code_to_id[spec["code"]] = existing.id
            existing.name = spec["name"]
            existing.player_segment = spec["player_segment"]
            existing.countries_json = json.dumps(spec.get("countries") or [])

        player_id = code_to_id[spec["code"]]
        for reg in spec.get("regulation_codes") or []:
            link_id = f"plr-{spec['code']}-{reg}".lower().replace("_", "")[:36]
            if len(link_id) < 8:
                link_id = "plr-" + hashlib.sha256(f"{spec['code']}:{reg}".encode()).hexdigest()[:32]
            if not db.get(PrivacyPlayerRegulationLink, link_id):
                db.add(
                    PrivacyPlayerRegulationLink(
                        id=link_id,
                        player_id=player_id,
                        regulation_code=reg,
                        privacy_role=spec.get("privacy_role", "PROCESSOR"),
                        data_shared_json=json.dumps(spec.get("data_shared") or []),
                        dpa_required=True,
                    )
                )
                counts["regulation_links"] += 1

    db.flush()
    for code, pid in code_to_id.items():
        if not db.get(PrivacyEcosystemPlayer, pid):
            row = db.query(PrivacyEcosystemPlayer).filter(PrivacyEcosystemPlayer.code == code).first()
            if row:
                code_to_id[code] = row.id

    for from_code, to_code, rel_type, mode, desc in ECOSYSTEM_RELATIONS:
        from_id = code_to_id.get(from_code)
        to_id = code_to_id.get(to_code)
        if not from_id or not to_id:
            continue
        rel_id = "rel-" + hashlib.sha256(f"{from_code}:{to_code}:{rel_type}".encode()).hexdigest()[:32]
        if not db.get(PrivacyEcosystemRelation, rel_id):
            db.add(
                PrivacyEcosystemRelation(
                    id=rel_id,
                    from_player_id=from_id,
                    to_player_id=to_id,
                    relation_type=rel_type,
                    integration_mode=mode,
                    description=desc,
                    active=True,
                )
            )
            counts["relations"] += 1

    db.commit()
    return counts


def list_players(
    db: Session,
    *,
    regulation_code: str | None = None,
    player_segment: str | None = None,
    region_group: str | None = None,
    limit: int = 200,
) -> list[PrivacyEcosystemPlayer]:
    q = db.query(PrivacyEcosystemPlayer).filter(PrivacyEcosystemPlayer.active.is_(True))
    if player_segment:
        q = q.filter(PrivacyEcosystemPlayer.player_segment == player_segment.upper())
    if region_group:
        q = q.filter(PrivacyEcosystemPlayer.region_group == region_group.upper())
    if regulation_code:
        q = q.join(PrivacyPlayerRegulationLink).filter(
            PrivacyPlayerRegulationLink.regulation_code == regulation_code.upper()
        )
    return q.order_by(PrivacyEcosystemPlayer.player_segment, PrivacyEcosystemPlayer.name).limit(limit).all()


def list_relations(db: Session, *, player_code: str | None = None, limit: int = 200) -> list[PrivacyEcosystemRelation]:
    q = db.query(PrivacyEcosystemRelation).filter(PrivacyEcosystemRelation.active.is_(True))
    if player_code:
        player = db.query(PrivacyEcosystemPlayer).filter(PrivacyEcosystemPlayer.code == player_code.upper()).first()
        if player:
            q = q.filter(
                (PrivacyEcosystemRelation.from_player_id == player.id)
                | (PrivacyEcosystemRelation.to_player_id == player.id)
            )
    return q.limit(limit).all()


def player_to_dict(player: PrivacyEcosystemPlayer, links: list[PrivacyPlayerRegulationLink] | None = None) -> dict:
    countries = json.loads(player.countries_json or "[]")
    regs = [lk.regulation_code for lk in (links or [])]
    return {
        "id": player.id,
        "code": player.code,
        "name": player.name,
        "player_segment": player.player_segment,
        "network_type": player.network_type,
        "region_group": player.region_group,
        "countries": countries,
        "regulation_codes": regs,
        "hardware_vendor": player.hardware_vendor,
        "global_player_code": player.global_player_code,
        "website_url": player.website_url,
        "privacy_contact_email": player.privacy_contact_email,
        "rental_network_id": player.rental_network_id,
    }
