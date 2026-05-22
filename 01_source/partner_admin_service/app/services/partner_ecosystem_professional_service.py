from __future__ import annotations

import importlib.util
import json
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.data.integration_capability_catalog import INTEGRATION_CAPABILITY_CATALOG
from app.data.locker_ecosystem_catalog import LOCKER_ECOSYSTEM_CATALOG, PRIORITY_ECOSYSTEM_CODES
from app.data.player_relations_seed import PLAYER_RELATIONS_SEED
from app.models.partner_ecosystem import PartnerEcosystemPlayer
from app.models.partner_ecosystem_professional import (
    PartnerIntegrationCapabilityCatalog,
    PartnerMarketPresence,
    PartnerPlayerCapability,
    PartnerPlayerRelation,
)
from app.services.crypto_util import new_id

DENSITY_BY_TIER = {"PRIORITY": "HIGH", "GLOBAL": "MEDIUM", "REGIONAL": "LOW"}

_MARKETPLACE_CATALOG_FILE = (
    Path(__file__).resolve().parents[3] / "marketplace_admin_service" / "app" / "data" / "channel_players_catalog.py"
)


def _load_marketplace_raw_catalog() -> list[dict]:
    if not _MARKETPLACE_CATALOG_FILE.is_file():
        return []
    spec = importlib.util.spec_from_file_location("mkt_ch", _MARKETPLACE_CATALOG_FILE)
    if spec is None or spec.loader is None:
        return []
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.CHANNEL_PLAYERS_CATALOG)


def _capabilities_by_code() -> dict[str, list[tuple[str, str, str]]]:
    out: dict[str, list[tuple[str, str, str]]] = {}
    for raw in _load_marketplace_raw_catalog():
        out[raw["code"]] = list(raw.get("capabilities") or [])
    for entry in LOCKER_ECOSYSTEM_CATALOG:
        caps = entry.get("capabilities") or []
        if caps:
            out[entry["code"]] = list(caps)
    return out


def _integration_status_for(code: str, entry: dict) -> str:
    if code in PRIORITY_ECOSYSTEM_CODES and entry.get("api_docs_url"):
        return "SANDBOX"
    if code in PRIORITY_ECOSYSTEM_CODES:
        return "PLANNED"
    return "PLANNED"


def seed_capability_catalog(db: Session) -> int:
    n = 0
    for cap in INTEGRATION_CAPABILITY_CATALOG:
        if not db.get(PartnerIntegrationCapabilityCatalog, cap["code"]):
            db.add(PartnerIntegrationCapabilityCatalog(**cap))
            n += 1
    db.flush()
    return n


def seed_professional_ecosystem(db: Session) -> dict[str, int]:
    """Capacidades, presença por país e relações entre players."""
    from app.services.partner_ecosystem_service import sync_catalog

    sync_catalog(db)
    caps_catalog = seed_capability_catalog(db)
    capabilities = relations = presence = 0
    caps_by_code = _capabilities_by_code()
    players_by_code = {p.code: p for p in db.query(PartnerEcosystemPlayer).all()}

    for entry in LOCKER_ECOSYSTEM_CATALOG:
        code = entry["code"]
        row = players_by_code.get(code)
        if not row:
            continue
        row.integration_status = _integration_status_for(code, entry)
        row.data_source = "MARKETPLACE_CATALOG" if entry.get("marketplace_channel_id") else "PARTNER_EXTENSION"
        if entry.get("api_docs_url"):
            row.api_docs_url = entry.get("api_docs_url")

        for cap_code, protocol, direction in caps_by_code.get(code, []):
            if not db.get(PartnerIntegrationCapabilityCatalog, cap_code):
                continue
            exists = (
                db.query(PartnerPlayerCapability)
                .filter(
                    PartnerPlayerCapability.ecosystem_player_id == row.id,
                    PartnerPlayerCapability.capability_code == cap_code,
                )
                .first()
            )
            if not exists:
                db.add(
                    PartnerPlayerCapability(
                        id=new_id(),
                        ecosystem_player_id=row.id,
                        capability_code=cap_code,
                        protocol=protocol,
                        direction=direction,
                        enabled=True,
                        sandbox_ready=code in PRIORITY_ECOSYSTEM_CODES,
                        production_ready=code in PRIORITY_ECOSYSTEM_CODES and bool(entry.get("api_docs_url")),
                    )
                )
                capabilities += 1

        if row.parent_group == "FOOD_DELIVERY" and not caps_by_code.get(code):
            for cap_code, protocol, direction in [("DELIVERY_STATUS", "WEBHOOK", "INBOUND")]:
                if db.get(PartnerIntegrationCapabilityCatalog, cap_code):
                    exists = (
                        db.query(PartnerPlayerCapability)
                        .filter(
                            PartnerPlayerCapability.ecosystem_player_id == row.id,
                            PartnerPlayerCapability.capability_code == cap_code,
                        )
                        .first()
                    )
                    if not exists:
                        db.add(
                            PartnerPlayerCapability(
                                id=new_id(),
                                ecosystem_player_id=row.id,
                                capability_code=cap_code,
                                protocol=protocol,
                                direction=direction,
                                enabled=True,
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
            if len(c) != 2 or c == "GL":
                continue
            exists_p = (
                db.query(PartnerMarketPresence)
                .filter(
                    PartnerMarketPresence.ecosystem_player_id == row.id,
                    PartnerMarketPresence.country == c,
                    PartnerMarketPresence.region_code.is_(None),
                )
                .first()
            )
            if not exists_p:
                db.add(
                    PartnerMarketPresence(
                        id=new_id(),
                        ecosystem_player_id=row.id,
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
            db.query(PartnerPlayerRelation)
            .filter(
                PartnerPlayerRelation.from_player_id == fr.id,
                PartnerPlayerRelation.to_player_id == to.id,
                PartnerPlayerRelation.relation_type == rel_type,
            )
            .first()
        )
        if not exists_r:
            db.add(
                PartnerPlayerRelation(
                    id=new_id(),
                    from_player_id=fr.id,
                    to_player_id=to.id,
                    relation_type=rel_type,
                    strength=strength,
                    active=True,
                )
            )
            relations += 1

    db.commit()
    return {
        "capability_catalog": caps_catalog,
        "player_capabilities": capabilities,
        "player_relations": relations,
        "market_presence": presence,
    }


def ecosystem_summary(db: Session) -> dict:
    groups = (
        db.query(PartnerEcosystemPlayer.parent_group, PartnerEcosystemPlayer.id)
        .filter(PartnerEcosystemPlayer.active.is_(True))
        .all()
    )
    by_group: dict[str, int] = {}
    for g, _ in groups:
        by_group[g] = by_group.get(g, 0) + 1
    return {
        "total_players": db.query(PartnerEcosystemPlayer).filter(PartnerEcosystemPlayer.active.is_(True)).count(),
        "by_parent_group": by_group,
        "integration_capabilities": db.query(PartnerIntegrationCapabilityCatalog).count(),
        "player_capabilities": db.query(PartnerPlayerCapability).filter(PartnerPlayerCapability.enabled.is_(True)).count(),
        "player_relations": db.query(PartnerPlayerRelation).filter(PartnerPlayerRelation.active.is_(True)).count(),
        "market_presence_rows": db.query(PartnerMarketPresence).filter(PartnerMarketPresence.active.is_(True)).count(),
        "priority_players": db.query(PartnerEcosystemPlayer)
        .filter(PartnerEcosystemPlayer.code.in_(PRIORITY_ECOSYSTEM_CODES))
        .count(),
    }


def integration_matrix(db: Session) -> list[dict]:
    rows = (
        db.query(PartnerEcosystemPlayer)
        .filter(PartnerEcosystemPlayer.active.is_(True))
        .order_by(PartnerEcosystemPlayer.sort_order, PartnerEcosystemPlayer.code)
        .all()
    )
    by_group: dict[str, list[dict]] = {}
    for r in rows:
        cap_count = (
            db.query(PartnerPlayerCapability)
            .filter(PartnerPlayerCapability.ecosystem_player_id == r.id, PartnerPlayerCapability.enabled.is_(True))
            .count()
        )
        by_group.setdefault(r.parent_group, []).append(
            {
                "code": r.code,
                "name": r.name,
                "integration_mode": r.integration_mode,
                "integration_status": getattr(r, "integration_status", None) or "PLANNED",
                "global_tier": r.global_tier,
                "capabilities_count": cap_count,
                "supports_lockers": r.supports_lockers,
                "supports_marketplace": r.supports_marketplace,
            }
        )
    return [
        {"parent_group": g, "total": len(players), "players": players}
        for g, players in sorted(by_group.items(), key=lambda x: x[0])
    ]


def list_player_capabilities(db: Session, player_code: str | None = None) -> list[dict]:
    q = (
        db.query(PartnerPlayerCapability, PartnerEcosystemPlayer, PartnerIntegrationCapabilityCatalog)
        .join(PartnerEcosystemPlayer, PartnerPlayerCapability.ecosystem_player_id == PartnerEcosystemPlayer.id)
        .join(
            PartnerIntegrationCapabilityCatalog,
            PartnerPlayerCapability.capability_code == PartnerIntegrationCapabilityCatalog.code,
        )
    )
    if player_code:
        q = q.filter(PartnerEcosystemPlayer.code == player_code.upper())
    rows = q.order_by(PartnerEcosystemPlayer.code, PartnerIntegrationCapabilityCatalog.sort_order).all()
    return [
        {
            "id": cap.id,
            "player_code": net.code,
            "capability_code": cap.capability_code,
            "capability_name": cat.name,
            "protocol": cap.protocol,
            "direction": cap.direction,
            "sandbox_ready": cap.sandbox_ready,
            "production_ready": cap.production_ready,
        }
        for cap, net, cat in rows
    ]


def list_player_relations(db: Session, player_code: str | None = None) -> list[dict]:
    code_by_id = {p.id: p.code for p in db.query(PartnerEcosystemPlayer).all()}
    out = []
    for rel in db.query(PartnerPlayerRelation).filter(PartnerPlayerRelation.active.is_(True)).all():
        from_code = code_by_id.get(rel.from_player_id)
        to_code = code_by_id.get(rel.to_player_id)
        if player_code and player_code.upper() not in (from_code, to_code):
            continue
        out.append(
            {
                "id": rel.id,
                "from_player_code": from_code,
                "to_player_code": to_code,
                "relation_type": rel.relation_type,
                "strength": rel.strength,
            }
        )
    return sorted(out, key=lambda x: (x["from_player_code"] or "", x["to_player_code"] or ""))


def list_market_presence(db: Session, country: str | None = None) -> list[dict]:
    q = db.query(PartnerMarketPresence, PartnerEcosystemPlayer).join(
        PartnerEcosystemPlayer, PartnerMarketPresence.ecosystem_player_id == PartnerEcosystemPlayer.id
    )
    if country:
        q = q.filter(PartnerMarketPresence.country == country.upper())
    rows = q.order_by(PartnerMarketPresence.country, PartnerEcosystemPlayer.code).limit(500).all()
    return [
        {
            "player_code": net.code,
            "country": mp.country,
            "service_level": mp.service_level,
            "locker_density": mp.locker_density,
        }
        for mp, net in rows
    ]
