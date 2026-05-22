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
from app.routers import pricing_fiscal


class _OpsUser:
    id = "user-promo-001"
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
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


@pytest.fixture()
def promo_client(monkeypatch):
    engine, Session, path = _sqlite_engine_session()
    monkeypatch.setattr("app.core.auth_dep.user_has_any_role", lambda *args, **kwargs: True)
    monkeypatch.setattr(pricing_fiscal, "_record_pr3_audit", lambda **kwargs: None)
    monkeypatch.setattr(
        pricing_fiscal,
        "seed_promotions_world",
        lambda db, **kwargs: {
            "campaigns_inserted": 2,
            "campaigns_skipped": 0,
            "promotions_inserted": 2,
            "promotions_skipped": 0,
            "scopes_inserted": 5,
        },
    )

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


def test_list_promotions_empty(promo_client):
    client, _ = promo_client
    r = client.get("/promotions")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["total"] == 0
    assert body["items"] == []


def test_create_get_and_patch_status(promo_client):
    client, _ = promo_client
    payload = {
        "code": "TEST-PROMO",
        "name": "Test promo",
        "type": "PERCENT_OFF",
        "discount_pct": 12.5,
        "min_order_cents": 500,
        "conditions_json": {"channel": "TEST"},
        "valid_from": "2026-05-22T10:00:00Z",
    }
    created = client.post("/promotions", json=payload)
    assert created.status_code == 200
    promo = created.json()
    assert promo["code"] == "TEST-PROMO"
    assert promo["is_active"] is True

    got = client.get(f"/promotions/{promo['id']}")
    assert got.status_code == 200
    assert got.json()["name"] == "Test promo"

    patched = client.patch(
        f"/promotions/{promo['id']}/status",
        json={"is_active": False, "reason": "test"},
    )
    assert patched.status_code == 200
    assert patched.json()["is_active"] is False


def test_clone_promotion_by_id_and_code(promo_client):
    client, _ = promo_client
    payload = {
        "code": "MARCOS10",
        "name": "Marcos Professor",
        "type": "PERCENT_OFF",
        "discount_pct": 10,
        "min_order_cents": 0,
        "conditions_json": {},
        "valid_from": "2026-05-22T10:00:00Z",
    }
    created = client.post("/promotions", json=payload)
    assert created.status_code == 200
    promo = created.json()

    cloned = client.post(
        f"/promotions/{promo['id']}/clone",
        json={"new_code": "MARCOS10-COPY", "new_name": "Marcos Professor (cópia)"},
    )
    assert cloned.status_code == 200
    body = cloned.json()
    assert body["ok"] is True
    assert body["promotion_code"] == "MARCOS10-COPY"
    assert body["source_id"] == promo["id"]

    cloned_by_code = client.post(
        "/promotions/MARCOS10/clone",
        json={"new_code": "MARCOS10-COPY2"},
    )
    assert cloned_by_code.status_code == 200
    assert cloned_by_code.json()["promotion_code"] == "MARCOS10-COPY2"


def test_seed_promotions_endpoint(promo_client):
    client, _ = promo_client
    r = client.post("/promotions/seed")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["inserted"] == 2  # mapped from promotions_inserted in endpoint


def test_get_promotion_not_found(promo_client):
    client, _ = promo_client
    r = client.get("/promotions/missing-id")
    assert r.status_code == 404
    assert r.json()["detail"]["type"] == "PROMOTION_NOT_FOUND"
