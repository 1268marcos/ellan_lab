from __future__ import annotations

import json
import os
import tempfile
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, get_current_user, get_db
from app.routers import promotions_admin


class _OpsUser:
    id = "user-promo-admin-001"
    full_name = "Ops"
    email = "ops@example.com"
    is_active = True
    email_verified = True


def _sqlite_schema():
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
                CREATE TABLE promotion_campaigns (
                    id VARCHAR(36) PRIMARY KEY,
                    code VARCHAR(32) NOT NULL UNIQUE,
                    name VARCHAR(128) NOT NULL,
                    description TEXT,
                    channel_family VARCHAR(32) NOT NULL DEFAULT 'GENERAL',
                    primary_country VARCHAR(8),
                    priority INTEGER NOT NULL DEFAULT 100,
                    max_stack_promotions INTEGER NOT NULL DEFAULT 1,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    valid_from TEXT NOT NULL,
                    valid_until TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotions (
                    id VARCHAR(36) PRIMARY KEY,
                    code VARCHAR(32) UNIQUE,
                    name VARCHAR(128) NOT NULL,
                    type VARCHAR(30) NOT NULL,
                    discount_pct REAL,
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
                    campaign_id VARCHAR(36),
                    created_by VARCHAR(36),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_scopes (
                    id VARCHAR(36) PRIMARY KEY,
                    promotion_id VARCHAR(36) NOT NULL,
                    scope_type VARCHAR(32) NOT NULL,
                    scope_value VARCHAR(128) NOT NULL,
                    mode VARCHAR(16) NOT NULL DEFAULT 'INCLUDE',
                    notes VARCHAR(255),
                    created_at TEXT NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE promotion_redemptions (
                    id VARCHAR(36) PRIMARY KEY,
                    promotion_id VARCHAR(36) NOT NULL,
                    campaign_id VARCHAR(36),
                    order_id VARCHAR(64) NOT NULL,
                    user_id VARCHAR(36),
                    partner_id VARCHAR(36),
                    channel_code VARCHAR(32),
                    country_code VARCHAR(8),
                    player_code VARCHAR(64),
                    discount_cents INTEGER NOT NULL DEFAULT 0,
                    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                    idempotency_key VARCHAR(64),
                    redeemed_at TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
        )
        now = "2026-05-22T12:00:00Z"
        conn.execute(
            text(
                """
                INSERT INTO promotion_campaigns (
                    id, code, name, channel_family, is_active, valid_from, created_at, updated_at
                ) VALUES ('camp-1', 'TEST-CAMP', 'Camp test', 'MARKETPLACE', 1, :now, :now, :now)
                """
            ),
            {"now": now},
        )
        conn.execute(
            text(
                """
                INSERT INTO promotions (
                    id, code, name, type, valid_from, conditions_json, is_active, uses_count,
                    min_order_cents, created_at, updated_at, campaign_id
                ) VALUES (
                    'promo-1', 'PROMO1', 'Promo', 'PERCENT_OFF', :now, '{}', 1, 0, 0, :now, :now, 'camp-1'
                )
                """
            ),
            {"now": now},
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


@pytest.fixture()
def admin_client(monkeypatch):
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)
    engine, Session, path = _sqlite_schema()
    app = FastAPI()
    app.include_router(promotions_admin.router)

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
    yield client
    engine.dispose()
    os.remove(path)


def test_promotions_overview(admin_client):
    r = admin_client.get("/promotions/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["promotions_total"] == 1
    assert body["campaigns_total"] == 1


def test_add_list_delete_scope(admin_client):
    client = admin_client
    created = client.post(
        "/promotions/promo-1/scopes",
        json={"scope_type": "PLAYER", "scope_value": "INPOST", "mode": "INCLUDE"},
    )
    assert created.status_code == 200
    listed = client.get("/promotions/promo-1/scopes")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    scope_id = listed.json()["items"][0]["id"]
    deleted = client.delete(f"/promotions/promo-1/scopes/{scope_id}")
    assert deleted.status_code == 200
    assert client.get("/promotions/promo-1/scopes").json()["total"] == 0


def test_list_campaigns(admin_client):
    r = admin_client.get("/promotion-campaigns")
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["code"] == "TEST-CAMP"
