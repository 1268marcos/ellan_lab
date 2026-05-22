from __future__ import annotations

import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_db
from app.core.global_players_seed import seed_global_players_registry
from app.data.catalog_players_registry import PLAYERS_REGISTRY
from app.routers import catalog_professional as catalog_router


class _AdminOpsUser:
    id = "user-gp-001"
    is_active = True
    email_verified = True


def _sqlite_global_players():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE product_categories (id VARCHAR(64) PRIMARY KEY, name VARCHAR(128) NOT NULL)
                """
            )
        )
        conn.execute(
            text(
                "INSERT INTO product_categories (id, name) VALUES ('LOCKER_PARCEL', 'Parcel'), ('LOCKER_FOOD_DELIVERY', 'Food')"
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
                    supports_lockers INTEGER NOT NULL DEFAULT 0,
                    supports_pudo INTEGER NOT NULL DEFAULT 0,
                    supports_food_delivery INTEGER NOT NULL DEFAULT 0,
                    supports_marketplace INTEGER NOT NULL DEFAULT 0,
                    operator_id VARCHAR(64),
                    integration_modes_json TEXT NOT NULL DEFAULT '[]',
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    active INTEGER NOT NULL DEFAULT 1,
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
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT DEFAULT (datetime('now'))
                )
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


@pytest.fixture()
def gp_client(monkeypatch):
    engine, Session, path = _sqlite_global_players()
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)
    app = FastAPI()
    app.include_router(catalog_router.router)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: _AdminOpsUser()
    client = TestClient(app)
    yield client, Session
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass


def test_registry_size():
    assert len(PLAYERS_REGISTRY) >= 70


def test_seed_global_players(gp_client):
    client, Session = gp_client
    db = Session()
    counts = seed_global_players_registry(db)
    assert counts["players"] >= 50
    assert db.execute(text("SELECT COUNT(*) FROM global_players")).scalar() >= 50
    db.close()

    r = client.get("/catalog-professional/global-players?player_type=FOOD_DELIVERY")
    assert r.status_code == 200
    body = r.json()
    codes = {i["code"] for i in body["items"]}
    assert "IFOOD" in codes
    assert "UBER_EATS" in codes


def test_ecosystem_overview(gp_client):
    client, Session = gp_client
    db = Session()
    seed_global_players_registry(db, sync_ecosystem=False)
    db.close()
    r = client.get("/catalog-professional/ecosystem-overview")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["players_total"] >= 50
    assert body["taxonomy_mappings"] >= 0


def test_players_reference_from_db(gp_client):
    client, Session = gp_client
    db = Session()
    seed_global_players_registry(db)
    db.close()
    r = client.get("/catalog-professional/players-reference")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "database"
    assert "MONDIAL_RELAY" in body["channel_codes"]
    assert len(body["player_types"]) >= 8
