from __future__ import annotations

import os
import tempfile
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_current_user, get_db
from app.routers import pricing_fiscal


class _OpsUser:
    id = "user-promo-excl-001"
    full_name = "Ops"
    email = "ops@example.com"
    is_active = True
    email_verified = True


def _sqlite_engine_session():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE products (
                    id VARCHAR(255) PRIMARY KEY NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotions (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    code VARCHAR(32),
                    name VARCHAR(128) NOT NULL,
                    type VARCHAR(30) NOT NULL,
                    discount_pct NUMERIC(5,2),
                    discount_cents INTEGER,
                    min_order_cents INTEGER NOT NULL DEFAULT 0,
                    max_discount_cents INTEGER,
                    max_uses INTEGER,
                    uses_count INTEGER NOT NULL DEFAULT 0,
                    per_user_limit INTEGER DEFAULT 1,
                    conditions_json TEXT NOT NULL DEFAULT '{}',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT,
                    created_by VARCHAR(36),
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_product_exclusions (
                    promotion_id VARCHAR(36) NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
                    product_id VARCHAR(255) NOT NULL REFERENCES products(id),
                    PRIMARY KEY (promotion_id, product_id)
                )
                """
            )
        )
        conn.execute(text("INSERT INTO products (id) VALUES ('sku_excl_1')"))
        conn.execute(
            text(
                """
                INSERT INTO promotions (
                    id, code, name, type, valid_from, conditions_json,
                    is_active, uses_count, min_order_cents, created_at, updated_at
                ) VALUES (
                    'promo-excl-test', 'EXCL1', 'Promo test', 'PERCENT_OFF',
                    datetime('now'), '{}', 1, 0, 0, datetime('now'), datetime('now')
                )
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


@pytest.fixture()
def exclusion_client(monkeypatch):
    engine, Session, path = _sqlite_engine_session()
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)
    monkeypatch.setattr(pricing_fiscal, "_record_pr3_audit", lambda **kwargs: None)

    app = FastAPI()
    app.include_router(pricing_fiscal.router)

    def override_db():
        db = Session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_public_user] = lambda: _OpsUser()
    app.dependency_overrides[get_current_user] = lambda: _OpsUser()

    client = TestClient(app)
    yield client, Session
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass


def test_list_promotion_product_exclusions_empty(exclusion_client):
    client, _session = exclusion_client
    r = client.get("/promotions/promo-excl-test/product-exclusions")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["total"] == 0
    assert body["items"] == []


def test_list_promotion_not_found(exclusion_client):
    client, _ = exclusion_client
    r = client.get("/promotions/does-not-exist/product-exclusions")
    assert r.status_code == 404
    assert r.json()["detail"]["type"] == "PROMOTION_NOT_FOUND"


def test_add_and_list_and_delete_exclusion(exclusion_client):
    client, _session = exclusion_client
    r = client.post("/promotions/promo-excl-test/product-exclusions", json={"product_id": "sku_excl_1"})
    assert r.status_code == 200
    assert r.json() == {"promotion_id": "promo-excl-test", "product_id": "sku_excl_1"}

    r2 = client.get("/promotions/promo-excl-test/product-exclusions")
    assert r2.status_code == 200
    body = r2.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["product_id"] == "sku_excl_1"

    r_dup = client.post("/promotions/promo-excl-test/product-exclusions", json={"product_id": "sku_excl_1"})
    assert r_dup.status_code == 409

    r_del = client.delete("/promotions/promo-excl-test/product-exclusions/sku_excl_1")
    assert r_del.status_code == 200
    assert r_del.json()["ok"] is True

    r3 = client.get("/promotions/promo-excl-test/product-exclusions")
    assert r3.json()["total"] == 0


def test_add_product_not_found(exclusion_client):
    client, _ = exclusion_client
    r = client.post("/promotions/promo-excl-test/product-exclusions", json={"product_id": "missing_sku"})
    assert r.status_code == 404
    assert r.json()["detail"]["type"] == "PRODUCT_NOT_FOUND"


def test_delete_exclusion_not_found(exclusion_client):
    client, _ = exclusion_client
    r = client.delete("/promotions/promo-excl-test/product-exclusions/ghost_sku")
    assert r.status_code == 404
    assert r.json()["detail"]["type"] == "PROMOTION_EXCLUSION_NOT_FOUND"
