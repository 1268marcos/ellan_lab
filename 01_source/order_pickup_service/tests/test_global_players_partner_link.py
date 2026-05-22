from __future__ import annotations

import os
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.global_players_partner_link import (
    link_global_players_to_partners,
    resolve_player_code_from_partner,
    seed_missing_locker_operators_from_registry,
    sync_global_players_ecosystem,
)
from app.core.global_players_seed import seed_global_players_registry
from app.data.catalog_global_players import locker_operator_id


def test_resolve_partner_codes():
    assert resolve_player_code_from_partner(partner_code="MERCADOLIVRE") == "MERCADO_LIVRE"
    assert resolve_player_code_from_partner(partner_id="OP-INPOST") == "INPOST"
    assert resolve_player_code_from_partner(partner_code="DHL") == "DHL_PACKSTATION"


def _sqlite_ecosystem():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True)
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE product_categories (id VARCHAR(64) PRIMARY KEY, name VARCHAR(128) NOT NULL)"
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_players (
                    code VARCHAR(40) PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    player_type VARCHAR(32) NOT NULL,
                    hq_country VARCHAR(2) NOT NULL,
                    supports_lockers INTEGER DEFAULT 0,
                    supports_pudo INTEGER DEFAULT 0,
                    supports_food_delivery INTEGER DEFAULT 0,
                    supports_marketplace INTEGER DEFAULT 0,
                    operator_id VARCHAR(64),
                    integration_modes_json TEXT DEFAULT '[]',
                    metadata_json TEXT DEFAULT '{}',
                    active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_regions (
                    id VARCHAR(36) PRIMARY KEY,
                    player_code VARCHAR(40) NOT NULL,
                    country_code VARCHAR(3) NOT NULL,
                    region_code VARCHAR(10),
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_capabilities (
                    id VARCHAR(36) PRIMARY KEY,
                    player_code VARCHAR(40) NOT NULL,
                    capability VARCHAR(40) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE category_player_eligibility (
                    id VARCHAR(36) PRIMARY KEY,
                    category_id VARCHAR(64) NOT NULL,
                    player_code VARCHAR(40) NOT NULL,
                    eligibility VARCHAR(20) NOT NULL DEFAULT 'ALLOWED',
                    notes TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE global_player_integration_targets (
                    id VARCHAR(36) PRIMARY KEY,
                    player_code VARCHAR(40) NOT NULL,
                    target_type VARCHAR(30) NOT NULL,
                    target_key VARCHAR(64) NOT NULL,
                    metadata_json TEXT DEFAULT '{}',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE locker_operators (
                    id VARCHAR(64) PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    player_code VARCHAR(40),
                    operator_type VARCHAR(32) NOT NULL DEFAULT 'LOGISTICS',
                    country VARCHAR(2) NOT NULL DEFAULT 'BR',
                    active INTEGER NOT NULL DEFAULT 1,
                    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                    document VARCHAR(32),
                    email VARCHAR(128),
                    phone VARCHAR(32),
                    commission_rate REAL,
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE ecommerce_partners (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    code VARCHAR(32) NOT NULL UNIQUE,
                    integration_type VARCHAR(30) NOT NULL,
                    revenue_share_pct REAL,
                    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                    sla_pickup_hours INTEGER NOT NULL DEFAULT 72,
                    active INTEGER NOT NULL DEFAULT 1,
                    country VARCHAR(2) NOT NULL DEFAULT 'BR',
                    status VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO ecommerce_partners (id, name, code, integration_type, country, status)
                VALUES ('legacy-meli', 'Mercado Livre Legado', 'MERCADOLIVRE', 'API', 'BR', 'ACTIVE')
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE logistics_partners (
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(128) NOT NULL,
                    code VARCHAR(32) NOT NULL UNIQUE,
                    integration_type VARCHAR(30) NOT NULL,
                    default_sla_hours INTEGER NOT NULL DEFAULT 72,
                    reminder_hours_before INTEGER NOT NULL DEFAULT 24,
                    active INTEGER NOT NULL DEFAULT 1,
                    country VARCHAR(2) NOT NULL DEFAULT 'BR',
                    created_at TEXT DEFAULT (datetime('now')),
                    updated_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO logistics_partners (id, name, code, integration_type, country)
                VALUES ('legacy-dhl', 'DHL Legado', 'DHL', 'API', 'DE')
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


def test_sync_creates_operators_and_links():
    engine, Session, path = _sqlite_ecosystem()
    db = Session()
    seed_global_players_registry(db, sync_ecosystem=False)
    eco = sync_global_players_ecosystem(db)
    assert eco["operators_created"] >= 1
    assert eco["ecommerce_links"] >= 1
    assert eco["logistics_links"] >= 1

    op_id = locker_operator_id("MONDIAL_RELAY")
    assert db.execute(
        text("SELECT 1 FROM locker_operators WHERE id = :id"),
        {"id": op_id},
    ).scalar()

    assert db.execute(
        text(
            "SELECT 1 FROM global_player_integration_targets "
            "WHERE player_code = 'MERCADO_LIVRE' AND target_type = 'ECOMMERCE_PARTNER' AND target_key = 'legacy-meli'"
        )
    ).scalar()

    assert db.execute(
        text(
            "SELECT 1 FROM global_player_integration_targets "
            "WHERE player_code = 'DHL_PACKSTATION' AND target_type = 'LOGISTICS_PARTNER'"
        )
    ).scalar()

    db.close()
    engine.dispose()
    os.remove(path)
