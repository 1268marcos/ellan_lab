from __future__ import annotations

import json
from datetime import date

from sqlalchemy.orm import Session

from app.data.integration_capability_catalog import INTEGRATION_CAPABILITY_CATALOG
from app.data.locker_network_players_catalog import (
    PRIORITY_LOCKER_CODES,
    global_tier_for_code,
    integration_status_for_entry,
)
from app.data.player_relations_seed import PLAYER_RELATIONS_SEED
from app.models.ml_ecosystem import (
    MlIntegrationCapabilityCatalog,
    MlMarketPresence,
    MlPlayerCapability,
    MlPlayerRelation,
)
from app.models.ml_network import MlLockerNetworkPlayer
from app.services.crypto_util import new_id

DENSITY_BY_TIER = {"TIER1": "HIGH", "TIER2": "MEDIUM", "REGIONAL": "LOW", "NICHE": "LOW"}


def seed_capability_catalog(db: Session) -> int:
    n = 0
    for cap in INTEGRATION_CAPABILITY_CATALOG:
        if not db.get(MlIntegrationCapabilityCatalog, cap["code"]):
            db.add(MlIntegrationCapabilityCatalog(**cap))
            n += 1
    db.flush()
    return n


def seed_player_ecosystem(db: Session, catalog_entries: list[dict]) -> dict[str, int]:
    caps_catalog = seed_capability_catalog(db)
    capabilities = 0
    relations = 0
    presence = 0
    players_by_code = {p.code: p for p in db.query(MlLockerNetworkPlayer).all()}

    for entry in catalog_entries:
        code = entry["code"]
        row = players_by_code.get(code)
        if not row:
            continue
        row.global_tier = global_tier_for_code(code)
        row.integration_status = integration_status_for_entry(entry)
        row.data_source = "MARKETPLACE_CATALOG" if entry.get("marketplace_channel_id") else "CATALOG"
        if entry.get("api_docs_url"):
            row.api_docs_url = entry.get("api_docs_url")

        for cap in entry.get("capabilities") or []:
            if isinstance(cap, (list, tuple)) and len(cap) >= 3:
                cap_code, protocol, direction = cap[0], cap[1], cap[2]
            else:
                continue
            if not db.get(MlIntegrationCapabilityCatalog, cap_code):
                continue
            exists = (
                db.query(MlPlayerCapability)
                .filter(
                    MlPlayerCapability.network_player_id == row.id,
                    MlPlayerCapability.capability_code == cap_code,
                )
                .first()
            )
            if not exists:
                db.add(
                    MlPlayerCapability(
                        id=new_id(),
                        network_player_id=row.id,
                        capability_code=cap_code,
                        protocol=protocol,
                        direction=direction,
                        enabled=True,
                        sandbox_ready=code in PRIORITY_LOCKER_CODES,
                        production_ready=code in PRIORITY_LOCKER_CODES and bool(entry.get("api_docs_url")),
                    )
                )
                capabilities += 1

        try:
            regions = json.loads(entry.get("regions_json") or "[]")
        except json.JSONDecodeError:
            regions = [entry.get("country", "XX")]
        if not regions:
            regions = [entry.get("country", "XX")]
        density = DENSITY_BY_TIER.get(row.global_tier or "REGIONAL", "MEDIUM")
        for country in regions:
            c = str(country).upper()[:2]
            if len(c) != 2:
                continue
            exists_p = (
                db.query(MlMarketPresence)
                .filter(
                    MlMarketPresence.network_player_id == row.id,
                    MlMarketPresence.country == c,
                    MlMarketPresence.region_code.is_(None),
                )
                .first()
            )
            if not exists_p:
                db.add(
                    MlMarketPresence(
                        id=new_id(),
                        network_player_id=row.id,
                        country=c,
                        region_code=None,
                        service_level="FULL" if c == entry.get("country") else "PARTIAL",
                        locker_density=density,
                        launched_at=date.today(),
                    )
                )
                presence += 1

    for from_code, to_code, rel_type, strength in PLAYER_RELATIONS_SEED:
        fr = players_by_code.get(from_code)
        to = players_by_code.get(to_code)
        if not fr or not to:
            continue
        exists_r = (
            db.query(MlPlayerRelation)
            .filter(
                MlPlayerRelation.from_player_id == fr.id,
                MlPlayerRelation.to_player_id == to.id,
                MlPlayerRelation.relation_type == rel_type,
            )
            .first()
        )
        if not exists_r:
            db.add(
                MlPlayerRelation(
                    id=new_id(),
                    from_player_id=fr.id,
                    to_player_id=to.id,
                    relation_type=rel_type,
                    strength=strength,
                    active=True,
                )
            )
            relations += 1

    db.flush()
    return {
        "capability_catalog": caps_catalog,
        "player_capabilities": capabilities,
        "player_relations": relations,
        "market_presence": presence,
    }


def list_player_capabilities(db: Session, network_player_id: str | None = None) -> list[dict]:
    q = db.query(MlPlayerCapability, MlLockerNetworkPlayer, MlIntegrationCapabilityCatalog).join(
        MlLockerNetworkPlayer, MlPlayerCapability.network_player_id == MlLockerNetworkPlayer.id
    ).join(
        MlIntegrationCapabilityCatalog,
        MlPlayerCapability.capability_code == MlIntegrationCapabilityCatalog.code,
    )
    if network_player_id:
        q = q.filter(MlPlayerCapability.network_player_id == network_player_id)
    rows = q.order_by(MlLockerNetworkPlayer.code, MlIntegrationCapabilityCatalog.sort_order).all()
    return [
        {
            "id": cap.id,
            "network_player_id": cap.network_player_id,
            "network_player_code": net.code,
            "capability_code": cap.capability_code,
            "capability_name": cat.name,
            "protocol": cap.protocol,
            "direction": cap.direction,
            "enabled": cap.enabled,
            "sandbox_ready": cap.sandbox_ready,
            "production_ready": cap.production_ready,
        }
        for cap, net, cat in rows
    ]


def list_player_relations(db: Session, player_code: str | None = None) -> list[dict]:
    q = db.query(MlPlayerRelation)
    rows = q.all()
    code_by_id = {p.id: p.code for p in db.query(MlLockerNetworkPlayer).all()}
    out = []
    for rel in rows:
        from_code = code_by_id.get(rel.from_player_id)
        to_code = code_by_id.get(rel.to_player_id)
        if player_code and player_code not in (from_code, to_code):
            continue
        out.append(
            {
                "id": rel.id,
                "from_player_code": from_code,
                "to_player_code": to_code,
                "relation_type": rel.relation_type,
                "strength": rel.strength,
                "active": rel.active,
            }
        )
    return sorted(out, key=lambda x: (x["from_player_code"] or "", x["to_player_code"] or ""))


def list_market_presence(db: Session, country: str | None = None) -> list[dict]:
    q = db.query(MlMarketPresence, MlLockerNetworkPlayer).join(
        MlLockerNetworkPlayer, MlMarketPresence.network_player_id == MlLockerNetworkPlayer.id
    )
    if country:
        q = q.filter(MlMarketPresence.country == country.upper())
    rows = q.order_by(MlMarketPresence.country, MlLockerNetworkPlayer.code).all()
    return [
        {
            "id": mp.id,
            "network_player_code": net.code,
            "country": mp.country,
            "region_code": mp.region_code,
            "service_level": mp.service_level,
            "locker_density": mp.locker_density,
            "active": mp.active,
        }
        for mp, net in rows
    ]


def ecosystem_counts(db: Session) -> dict:
    return {
        "integration_capabilities": db.query(MlIntegrationCapabilityCatalog).count(),
        "player_capabilities": db.query(MlPlayerCapability).filter(MlPlayerCapability.enabled.is_(True)).count(),
        "player_relations": db.query(MlPlayerRelation).filter(MlPlayerRelation.active.is_(True)).count(),
        "market_presence_rows": db.query(MlMarketPresence).filter(MlMarketPresence.active.is_(True)).count(),
        "tier1_players": db.query(MlLockerNetworkPlayer)
        .filter(MlLockerNetworkPlayer.global_tier == "TIER1", MlLockerNetworkPlayer.active.is_(True))
        .count(),
    }
