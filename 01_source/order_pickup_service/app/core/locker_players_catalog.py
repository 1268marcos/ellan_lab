"""Catálogo de players para promoções — delega a global_players / PLAYERS_REGISTRY."""

from __future__ import annotations

from app.core.promotions_players_integration import (
    PLAYER_ALIASES_SEED,
    load_players_catalog,
    resolve_player_code_db,
)
from app.data.catalog_players_registry import PLAYERS_REGISTRY

# Compat: reexport para código legado
LOCKER_PLAYERS_CATALOG = tuple(
    type("Ref", (), {"code": p["code"], "display_name": p["name"], "segment": p.get("type"), "countries": tuple(p.get("regions") or []), "aliases": (), "notes": ""})()
    for p in PLAYERS_REGISTRY
)


def _norm(value: str | None) -> str:
    return str(value or "").strip().upper().replace("-", "_").replace(" ", "_")


def resolve_player_code(raw: str | None, db=None) -> str | None:
    if db is not None:
        return resolve_player_code_db(db, raw)
    n = _norm(raw)
    if not n:
        return None
    for alias, canonical in PLAYER_ALIASES_SEED:
        if n == alias:
            return canonical
    for p in PLAYERS_REGISTRY:
        if _norm(p["code"]) == n:
            return str(p["code"])
    return n


def catalog_as_dicts(db=None) -> list[dict]:
    if db is not None:
        return load_players_catalog(db)
    from app.core.promotions_players_integration import PLAYER_TYPE_SEGMENT_MAP, _registry_catalog

    return _registry_catalog()


def get_locker_players_catalog(db=None) -> list[dict]:
    return catalog_as_dicts(db)
