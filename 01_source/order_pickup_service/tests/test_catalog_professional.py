from __future__ import annotations

import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_db
from app.routers import catalog_professional as catalog_router


class _AdminOpsUser:
    id = "user-catalog-pro-001"
    is_active = True
    email_verified = True


def _sqlite_catalog_session():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE product_categories (
                    id VARCHAR(64) PRIMARY KEY NOT NULL,
                    name VARCHAR(128) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO product_categories (id, name) VALUES
                    ('ELECTRONICS', 'Eletrônicos'),
                    ('FASHION', 'Moda'),
                    ('PHARMACY_OTC_MEDS', 'Farmácia OTC'),
                    ('LOCKER_PARCEL', 'Encomenda locker')
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE products (
                    id VARCHAR(255) PRIMARY KEY NOT NULL,
                    amount_cents INTEGER DEFAULT 0
                )
                """
            )
        )
        conn.execute(text("INSERT INTO products (id, amount_cents) VALUES ('SKU-1', 1999)"))
        conn.execute(
            text(
                """
                CREATE TABLE category_taxonomy_mappings (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    category_id VARCHAR(64) NOT NULL,
                    taxonomy_scheme VARCHAR(40) NOT NULL,
                    external_code VARCHAR(128) NOT NULL,
                    external_name VARCHAR(255),
                    country_code VARCHAR(3),
                    is_primary INTEGER NOT NULL DEFAULT 0,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE product_channel_listings (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    product_id VARCHAR(255) NOT NULL,
                    channel_code VARCHAR(40) NOT NULL,
                    external_sku VARCHAR(255),
                    external_category_id VARCHAR(128),
                    listing_status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',
                    price_cents INTEGER,
                    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                    partner_id VARCHAR(36),
                    sync_mode VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
                    last_synced_at TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE product_attribute_definitions (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    category_id VARCHAR(64),
                    attr_key VARCHAR(64) NOT NULL,
                    attr_label VARCHAR(128) NOT NULL,
                    data_type VARCHAR(20) NOT NULL DEFAULT 'STRING',
                    enum_values_json TEXT,
                    is_required INTEGER NOT NULL DEFAULT 0,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE product_attribute_values (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    product_id VARCHAR(255) NOT NULL,
                    definition_id VARCHAR(36) NOT NULL,
                    value_text TEXT,
                    value_number REAL,
                    value_bool INTEGER,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


@pytest.fixture()
def catalog_client(monkeypatch):
    engine, Session, path = _sqlite_catalog_session()
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
    yield client
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass


def test_create_taxonomy_and_channel_listing(catalog_client):
    r = catalog_client.post(
        "/catalog-professional/category-taxonomy",
        json={
            "category_id": "ELECTRONICS",
            "taxonomy_scheme": "MERCADO_LIVRE",
            "external_code": "MLB1000",
            "external_name": "Eletrônicos",
        },
    )
    assert r.status_code == 200
    r2 = catalog_client.post(
        "/catalog-professional/channel-listings",
        json={
            "product_id": "SKU-1",
            "channel_code": "MERCADO_LIVRE",
            "external_sku": "ML-SKU-1",
            "listing_status": "ACTIVE",
            "price_cents": 1999,
        },
    )
    assert r2.status_code == 200
    assert r2.json()["channel_code"] == "MERCADO_LIVRE"


def test_players_reference(catalog_client):
    r = catalog_client.get("/catalog-professional/players-reference")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["source"] == "registry"
    assert "INPOST" in body["taxonomy_schemes"]
    assert "MERCADO_LIVRE" in body["channel_codes"]
    assert "FOOD_DELIVERY" in body["player_types"]
    assert len(body["players"]) >= 70
    worten = next(p for p in body["players"] if p["code"] == "WORTEN")
    assert worten["operator_id"] == "OP-WORTEN"


def test_seed_catalog_professional(catalog_client):
    r = catalog_client.post("/catalog-professional/seed")
    assert r.status_code == 200
    assert r.json()["ok"] is True
    r2 = catalog_client.get("/catalog-professional/category-taxonomy")
    assert r2.status_code == 200
    schemes = {row["taxonomy_scheme"] for row in r2.json()["items"]}
    assert "INPOST" in schemes or "CORREIOS" in schemes
