from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.routers import rentals_ops as rentals_ops_router


def _sqlite_session():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(text("CREATE TABLE lockers (id VARCHAR(36) PRIMARY KEY, active INTEGER DEFAULT 1, created_at TEXT)"))
        conn.execute(text("INSERT INTO lockers (id, active, created_at) VALUES ('locker-a', 1, datetime('now'))"))
        conn.execute(
            text(
                """
                CREATE TABLE rental_plans (
                    id VARCHAR(36) PRIMARY KEY,
                    locker_id VARCHAR(36),
                    slot_size VARCHAR(8),
                    name VARCHAR(128) NOT NULL,
                    description TEXT,
                    billing_cycle VARCHAR(20) NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                    max_duration_days INTEGER,
                    grace_period_hours INTEGER NOT NULL DEFAULT 24,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_contracts (
                    id VARCHAR(36) PRIMARY KEY,
                    locker_id VARCHAR(36) NOT NULL,
                    slot_label VARCHAR(20) NOT NULL,
                    plan_id VARCHAR(36),
                    tenant_id VARCHAR(100),
                    renter_user_id VARCHAR(36),
                    renter_name VARCHAR(255),
                    renter_document VARCHAR(32),
                    renter_phone VARCHAR(32),
                    renter_email VARCHAR(128),
                    amount_cents INTEGER NOT NULL,
                    currency VARCHAR(8) NOT NULL DEFAULT 'BRL',
                    billing_cycle VARCHAR(20) NOT NULL,
                    next_billing_at TEXT,
                    auto_renew INTEGER NOT NULL DEFAULT 0,
                    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                    started_at TEXT,
                    ends_at TEXT,
                    cancelled_at TEXT,
                    cancel_reason VARCHAR(255),
                    ended_at TEXT,
                    access_pin_hash VARCHAR(255),
                    access_token_ref VARCHAR(255),
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE locker_slots (
                    id VARCHAR(36) PRIMARY KEY,
                    locker_id VARCHAR(36) NOT NULL,
                    slot_label VARCHAR(20) NOT NULL,
                    slot_size VARCHAR(8) NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
                    current_rental_id VARCHAR(36),
                    updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_webhook_endpoints (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(100) NOT NULL,
                    url VARCHAR(500) NOT NULL,
                    secret_hash VARCHAR(128) NOT NULL,
                    secret_key VARCHAR(256),
                    events_json TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_contract_events (
                    id VARCHAR(36) PRIMARY KEY,
                    contract_id VARCHAR(36) NOT NULL,
                    event_type VARCHAR(64) NOT NULL,
                    payload_json TEXT NOT NULL DEFAULT '{}',
                    actor VARCHAR(128) NOT NULL DEFAULT 'system',
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_api_keys (
                    id VARCHAR(36) PRIMARY KEY,
                    tenant_id VARCHAR(100) NOT NULL,
                    key_prefix VARCHAR(16) NOT NULL,
                    key_hash VARCHAR(128) NOT NULL,
                    label VARCHAR(64),
                    scopes_json TEXT NOT NULL DEFAULT '[]',
                    expires_at TEXT,
                    last_used_at TEXT,
                    revoked_at TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO rental_plans (id, locker_id, slot_size, name, billing_cycle, amount_cents, active)
                VALUES
                    ('plan-1', 'locker-a', 'M', 'Plano M', 'MONTHLY', 9900, 1),
                    ('plan-2', NULL, NULL, 'Plano inativo', 'MONTHLY', 100, 0)
                """
            )
        )
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
            text(
                """
                INSERT INTO rental_contracts (
                    id, locker_id, slot_label, plan_id, renter_user_id, renter_name,
                    amount_cents, billing_cycle, next_billing_at, status
                ) VALUES
                    ('c-active', 'locker-a', '01A', 'plan-1', 'user-1', 'Maria', 9900, 'MONTHLY', :now, 'ACTIVE'),
                    ('c-pend', 'locker-a', '01B', 'plan-1', 'user-2', 'Joao', 5000, 'WEEKLY', NULL, 'PENDING')
                """
            ),
            {"now": now},
        )
        conn.execute(
            text(
                """
                INSERT INTO locker_slots (id, locker_id, slot_label, slot_size, status, current_rental_id)
                VALUES ('slot-1', 'locker-a', '01A', 'M', 'OCCUPIED', 'c-active')
                """
            )
        )
    Session = sessionmaker(bind=engine, future=True)
    return engine, Session, path


@pytest.fixture()
def rentals_client():
    engine, SessionLocal, path = _sqlite_session()

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(rentals_ops_router.router, prefix="/internal/rentals")

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[require_internal_token] = lambda: True
    client = TestClient(app)
    yield client, path
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass


def test_list_contracts_pagination(rentals_client):
    client, _ = rentals_client
    r = client.get("/internal/rentals/contracts", headers={"X-Internal-Token": "any"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_contracts_filter_status(rentals_client):
    client, _ = rentals_client
    r = client.get("/internal/rentals/contracts", params={"status": "ACTIVE"}, headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "c-active"


def test_list_contracts_filter_locker_and_user(rentals_client):
    client, _ = rentals_client
    r = client.get(
        "/internal/rentals/contracts",
        params={"locker_id": "locker-a", "renter_user_id": "user-2"},
        headers={"X-Internal-Token": "x"},
    )
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["id"] == "c-pend"


def test_contract_detail_with_plan_and_slot(rentals_client):
    client, _ = rentals_client
    r = client.get("/internal/rentals/contracts/c-active", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    body = r.json()
    assert body["contract"]["id"] == "c-active"
    assert body["plan"]["id"] == "plan-1"
    assert body["slot"]["slot_label"] == "01A"


def test_contract_detail_404(rentals_client):
    client, _ = rentals_client
    r = client.get("/internal/rentals/contracts/missing-id", headers={"X-Internal-Token": "x"})
    assert r.status_code == 404


def test_plans_lists_only_active(rentals_client):
    client, _ = rentals_client
    r = client.get("/internal/rentals/plans", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    ids = {x["id"] for x in r.json()["items"]}
    assert "plan-1" in ids
    assert "plan-2" not in ids


def test_create_plan_and_contract(rentals_client):
    client, _ = rentals_client
    pr = client.post(
        "/internal/rentals/plans",
        headers={"X-Internal-Token": "x"},
        json={
            "name": "Novo plano",
            "locker_id": "locker-a",
            "slot_size": "S",
            "billing_cycle": "WEEKLY",
            "amount_cents": 2500,
        },
    )
    assert pr.status_code == 201
    plan_id = pr.json()["id"]

    cr = client.post(
        "/internal/rentals/contracts",
        headers={"X-Internal-Token": "x"},
        json={
            "locker_id": "locker-a",
            "slot_label": "01C",
            "plan_id": plan_id,
            "renter_name": "Teste OPS",
            "status": "PENDING",
        },
    )
    assert cr.status_code == 201
    assert cr.json()["contract"]["plan_id"] == plan_id


def test_webhook_upsert_and_rotate_key(rentals_client):
    client, _ = rentals_client
    wh = client.put(
        "/internal/rentals/webhooks/tenant-x",
        headers={"X-Internal-Token": "x"},
        json={
            "tenant_id": "tenant-x",
            "url": "https://example.com/hook",
            "events": ["rental.contract.created"],
        },
    )
    assert wh.status_code == 200
    assert wh.json()["webhook_secret"]

    rot = client.post("/internal/rentals/api-keys/tenant-x/rotate", headers={"X-Internal-Token": "x"})
    assert rot.status_code == 200
    assert rot.json()["api_key"].startswith("rnt_")


def test_cancel_contract(rentals_client):
    client, _ = rentals_client
    r = client.post(
        "/internal/rentals/contracts/c-pend/cancel",
        headers={"X-Internal-Token": "x"},
        json={"cancel_reason": "ops test"},
    )
    assert r.status_code == 200
    assert r.json()["contract"]["status"] == "CANCELLED"


def test_ecosystem_catalog(rentals_client):
    client, _ = rentals_client
    r = client.get("/internal/rentals/ecosystem/catalog", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    catalog = body["catalog"]
    assert catalog["networks_total"] >= 20
    codes = {n["code"] for n in catalog["networks"]}
    for code in ("INPOST", "DPD", "DHL_PACK", "MAGALU", "MELI", "AMAZON_HUB", "CORREIOS", "CTT", "WORTEN", "ECI"):
        assert code in codes


def test_invalid_token_without_override(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "internal_token", "secret-ops", raising=False)

    engine, SessionLocal, path = _sqlite_session()

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(
        rentals_ops_router.router,
        prefix="/internal/rentals",
        dependencies=[Depends(require_internal_token)],
    )
    app.dependency_overrides[get_db] = _get_db
    client = TestClient(app)
    bad = client.get("/internal/rentals/plans", headers={"X-Internal-Token": "wrong"})
    assert bad.status_code == 401
    good = client.get("/internal/rentals/plans", headers={"X-Internal-Token": "secret-ops"})
    assert good.status_code == 200
    engine.dispose()
    try:
        os.remove(path)
    except OSError:
        pass
