"""Integração promoções ↔ global_players (catálogo mundial, aliases, relações)."""

from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.data.catalog_players_registry import PLAYERS_REGISTRY

# Aliases usados em escopos/promoções → código canónico em global_players
PLAYER_ALIASES_SEED: tuple[tuple[str, str], ...] = (
    ("AMAZON", "AMAZON_HUB"),
    ("AMAZON_US_HUB", "AMAZON_HUB"),
    ("DHL", "DHL_PACKSTATION"),
    ("MERCADOLIVRE", "MERCADO_LIVRE"),
    ("ML", "MERCADO_LIVRE"),
    ("ECT", "CORREIOS"),
    ("HERMES_UK", "EVRI"),
    ("EL_CORTE_INGLES_CP", "EL_CORTE_INGLES"),
    ("CORTE_INGLES", "EL_CORTE_INGLES"),
    ("ECI", "EL_CORTE_INGLES"),
    ("INPOST_PARCEL", "INPOST"),
    ("INPOST_LOCKERS", "INPOST"),
    ("DPD_LOCKER", "DPD"),
    ("DPD_PICKUP", "DPD"),
    ("MAGAZINE_LUIZA", "MAGALU"),
    ("WORTEN_PICKUP", "WORTEN"),
    ("CTT_EXPRESSO", "CTT"),
    ("CTT_LOCKER", "CTT"),
    ("CORREIOS_LOCKER", "CORREIOS"),
    ("LOCKER_CORREIOS", "CORREIOS"),
    ("USPS_HUB", "USPS"),
    ("USPS_LOCKER", "USPS"),
    ("UPS_ACCESS_POINT", "UPS"),
    ("FEDEX_ODP", "FEDEX"),
    ("GLS_LOCKER", "GLS"),
    ("BLOQIT", "BLOQ_IT"),
)

# Relações de integração (rede / PUDO / agregador)
PLAYER_RELATIONS_SEED: tuple[tuple[str, str, str, str], ...] = (
    ("PONTO_MAGALU", "MAGALU", "OPERATES", "Rede Ponto Magalu operada pelo marketplace"),
    ("ML_PUDO", "MERCADO_LIVRE", "OPERATES", "Pontos de coleta Mercado Livre"),
    ("AMAZON_HUB", "INPOST", "PARTNER_NETWORK", "Hub Amazon em rede InPost (EU)"),
    ("CAINIAO", "CORREIOS", "AGGREGATES", "Cainiao → last mile BR"),
    ("MELHOR_ENVIO", "CORREIOS", "AGGREGATES", "Melhor Envio agrega Correios/lockers"),
    ("MELHOR_ENVIO", "JADLOG", "AGGREGATES", "Melhor Envio agrega Jadlog"),
    ("INTELIPOST", "LOGGI", "AGGREGATES", "Intelipost routing BR"),
    ("UBER_EATS", "INPOST", "PARTNER_NETWORK", "Food → locker parceiro"),
    ("IFOOD", "MAGALU", "PARTNER_NETWORK", "Food delivery + PUDO Magalu"),
    ("GLOVO", "MONDIAL_RELAY", "PARTNER_NETWORK", "Food + parcel shop ES"),
)

PLAYER_TYPE_SEGMENT_MAP = {
    "LOCKER_NETWORK": "LOCKER_OPERATOR",
    "NETWORK_OPERATOR": "LOCKER_OPERATOR",
    "CARRIER": "CARRIER",
    "POSTAL": "CARRIER",
    "MARKETPLACE": "MARKETPLACE",
    "RETAIL_PUDO": "RETAIL_PUDO",
    "AGGREGATOR": "AGGREGATOR",
    "HARDWARE": "LOCKER_HARDWARE",
    "FOOD_DELIVERY": "FOOD_DELIVERY",
    "LAST_MILE_SAAS": "AGGREGATOR",
}


def _table_exists(db: Session, name: str) -> bool:
    return name in set(inspect(db.get_bind()).get_table_names())


def _registry_catalog() -> list[dict]:
    out = []
    for p in PLAYERS_REGISTRY:
        ptype = str(p.get("type") or "GENERAL")
        out.append(
            {
                "code": p["code"],
                "display_name": p["name"],
                "segment": PLAYER_TYPE_SEGMENT_MAP.get(ptype, ptype),
                "player_type": ptype,
                "countries": list(p.get("regions") or [p.get("country")]),
                "aliases": [],
                "supports_lockers": bool(p.get("supports_lockers")),
                "supports_pudo": bool(p.get("supports_pudo")),
                "supports_food": bool(p.get("supports_food")),
                "supports_marketplace": bool(p.get("supports_marketplace")),
                "integration_modes": p.get("integration_modes") or [],
            }
        )
    return out


def load_players_catalog(db: Session, *, segment: str | None = None) -> list[dict]:
    """Catálogo para UI/API: DB global_players se disponível, senão PLAYERS_REGISTRY."""
    seg = str(segment or "").strip().upper()
    if _table_exists(db, "global_players"):
        try:
            rows = db.execute(
                text(
                    """
                    SELECT code, name, player_type, hq_country,
                           supports_lockers, supports_pudo, supports_food_delivery,
                           supports_marketplace, integration_modes_json, metadata_json
                    FROM global_players
                    WHERE active = TRUE
                    ORDER BY player_type, name
                    """
                ),
            ).mappings().all()
            if rows:
                aliases_by_player: dict[str, list[str]] = {}
                if _table_exists(db, "global_player_aliases"):
                    for ar in db.execute(
                        text("SELECT alias_code, player_code FROM global_player_aliases")
                    ).mappings().all():
                        aliases_by_player.setdefault(str(ar["player_code"]), []).append(str(ar["alias_code"]))
                catalog = []
                for r in rows:
                    code = str(r["code"])
                    ptype = str(r["player_type"] or "")
                    meta = r.get("metadata_json")
                    if isinstance(meta, str):
                        try:
                            meta = json.loads(meta)
                        except json.JSONDecodeError:
                            meta = {}
                    countries = (meta or {}).get("regions") if isinstance(meta, dict) else None
                    if not countries:
                        countries = [str(r.get("hq_country") or "")]
                    catalog.append(
                        {
                            "code": code,
                            "display_name": str(r["name"] or code),
                            "segment": PLAYER_TYPE_SEGMENT_MAP.get(ptype, ptype),
                            "player_type": ptype,
                            "countries": list(countries),
                            "aliases": aliases_by_player.get(code, []),
                            "supports_lockers": bool(r.get("supports_lockers")),
                            "supports_pudo": bool(r.get("supports_pudo")),
                            "supports_food": bool(r.get("supports_food_delivery")),
                            "supports_marketplace": bool(r.get("supports_marketplace")),
                            "integration_modes": json.loads(r["integration_modes_json"])
                            if isinstance(r.get("integration_modes_json"), str)
                            else (r.get("integration_modes_json") or []),
                        }
                    )
                if seg:
                    catalog = [c for c in catalog if str(c.get("segment") or "").upper() == seg]
                return catalog
        except Exception:
            pass
    catalog = _registry_catalog()
    if seg:
        catalog = [c for c in catalog if str(c.get("segment") or "").upper() == seg]
    return catalog


def resolve_player_code_db(db: Session, raw: str | None) -> str | None:
    n = str(raw or "").strip().upper().replace("-", "_").replace(" ", "_")
    if not n:
        return None
    if _table_exists(db, "global_players"):
        if db.execute(text("SELECT 1 FROM global_players WHERE code = :c"), {"c": n}).scalar():
            return n
        if _table_exists(db, "global_player_aliases"):
            row = db.execute(
                text("SELECT player_code FROM global_player_aliases WHERE alias_code = :a"),
                {"a": n},
            ).scalar()
            if row:
                return str(row)
    for alias, canonical in PLAYER_ALIASES_SEED:
        if n == alias:
            return canonical
    for p in PLAYERS_REGISTRY:
        if str(p["code"]).upper() == n:
            return str(p["code"])
    return n


def validate_player_scope(db: Session, scope_type: str, scope_value: str) -> tuple[bool, str | None]:
    st = str(scope_type or "").strip().upper()
    if st not in ("PLAYER", "MARKETPLACE", "LOCKER_OPERATOR"):
        return True, None
    resolved = resolve_player_code_db(db, scope_value)
    if not resolved:
        return False, f"Player desconhecido: {scope_value}. Execute sync de global_players ou use código do catálogo."
    if _table_exists(db, "global_players"):
        if not db.execute(
            text("SELECT 1 FROM global_players WHERE code = :c AND active = TRUE"),
            {"c": resolved},
        ).scalar():
            return False, f"Player {resolved} inactivo ou ausente em global_players."
    return True, resolved


def seed_player_aliases_and_relations(db: Session) -> dict[str, int]:
    counts = {"aliases": 0, "relations": 0}
    if not _table_exists(db, "global_players"):
        return counts
    for alias, canonical in PLAYER_ALIASES_SEED:
        if not db.execute(text("SELECT 1 FROM global_players WHERE code = :c"), {"c": canonical}).scalar():
            continue
        if db.execute(
            text("SELECT 1 FROM global_player_aliases WHERE alias_code = :a"),
            {"a": alias},
        ).scalar():
            continue
        db.execute(
            text(
                "INSERT INTO global_player_aliases (alias_code, player_code) VALUES (:a, :p)"
            ),
            {"a": alias, "p": canonical},
        )
        counts["aliases"] += 1
    for from_c, to_c, rel_type, notes in PLAYER_RELATIONS_SEED:
        if not db.execute(text("SELECT 1 FROM global_players WHERE code = :c"), {"c": from_c}).scalar():
            continue
        if not db.execute(text("SELECT 1 FROM global_players WHERE code = :c"), {"c": to_c}).scalar():
            continue
        exists = db.execute(
            text(
                """
                SELECT 1 FROM global_player_relations
                WHERE from_player_code = :f AND to_player_code = :t AND relation_type = :r
                """
            ),
            {"f": from_c, "t": to_c, "r": rel_type},
        ).scalar()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO global_player_relations (id, from_player_code, to_player_code, relation_type, notes)
                VALUES (:id, :f, :t, :r, :n)
                """
            ),
            {"id": str(uuid4()), "f": from_c, "t": to_c, "r": rel_type, "n": notes},
        )
        counts["relations"] += 1
    db.commit()
    return counts


def catalog_segments_summary(db: Session) -> list[dict]:
    catalog = load_players_catalog(db)
    by_seg: dict[str, int] = {}
    for row in catalog:
        seg = str(row.get("segment") or "OTHER")
        by_seg[seg] = by_seg.get(seg, 0) + 1
    return [{"segment": k, "count": v} for k, v in sorted(by_seg.items(), key=lambda x: -x[1])]
