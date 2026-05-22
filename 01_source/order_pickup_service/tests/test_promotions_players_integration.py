from __future__ import annotations

import os
import tempfile

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.promotions_players_integration import (
    load_players_catalog,
    resolve_player_code_db,
    seed_player_aliases_and_relations,
    validate_player_scope,
)
def _sqlite_global_schema():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE global_players (
                    code TEXT PRIMARY KEY, name TEXT NOT NULL, player_type TEXT NOT NULL,
                    hq_country TEXT NOT NULL, supports_lockers INTEGER DEFAULT 0,
                    supports_pudo INTEGER DEFAULT 0, supports_food_delivery INTEGER DEFAULT 0,
                    supports_marketplace INTEGER DEFAULT 0, operator_id TEXT,
                    integration_modes_json TEXT DEFAULT '[]', metadata_json TEXT DEFAULT '{}',
                    active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_regions (
                    id TEXT PRIMARY KEY, player_code TEXT NOT NULL, country_code TEXT NOT NULL,
                    region_code TEXT, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_capabilities (
                    id TEXT PRIMARY KEY, player_code TEXT NOT NULL, capability TEXT NOT NULL, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_aliases (
                    alias_code TEXT PRIMARY KEY, player_code TEXT NOT NULL, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_relations (
                    id TEXT PRIMARY KEY, from_player_code TEXT NOT NULL, to_player_code TEXT NOT NULL,
                    relation_type TEXT NOT NULL, notes TEXT, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_integration_targets (
                    id TEXT PRIMARY KEY, player_code TEXT NOT NULL, target_type TEXT NOT NULL,
                    target_key TEXT NOT NULL, metadata_json TEXT DEFAULT '{}', created_at TEXT
                )
                """
            )
        )
    return engine, path


def test_load_catalog_from_db():
    engine, path = _sqlite_global_schema()
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    for code, name, ptype in (
        ("INPOST", "InPost", "LOCKER_NETWORK"),
        ("AMAZON_HUB", "Amazon Hub", "MARKETPLACE"),
        ("MERCADO_LIVRE", "Mercado Livre", "MARKETPLACE"),
    ):
        db.execute(
            text(
                """
                INSERT INTO global_players (
                    code, name, player_type, hq_country, supports_lockers, supports_pudo,
                    supports_food_delivery, supports_marketplace, integration_modes_json,
                    metadata_json, active, created_at, updated_at
                ) VALUES (
                    :c, :n, :t, 'BR', 1, 0, 0, 1, '[]', '{}', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
            ),
            {"c": code, "n": name, "t": ptype},
        )
    db.execute(
        text("INSERT INTO global_player_aliases (alias_code, player_code) VALUES ('AMAZON', 'AMAZON_HUB')")
    )
    db.commit()
    seed_player_aliases_and_relations(db)
    catalog = load_players_catalog(db)
    assert len(catalog) == 3
    assert resolve_player_code_db(db, "AMAZON") == "AMAZON_HUB"
    ok, resolved = validate_player_scope(db, "PLAYER", "MERCADOLIVRE")
    assert ok is True
    assert resolved == "MERCADO_LIVRE"
    db.close()
    engine.dispose()
    os.remove(path)
