from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.routers import rentals_ops as rentals_ops_router
from tests.test_rentals_ops import _sqlite_session


@pytest.fixture()
def premium_client():
    engine, SessionLocal, path = _sqlite_session()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE rental_networks (
                    id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) UNIQUE, name VARCHAR(128),
                    network_type VARCHAR(32), active INTEGER DEFAULT 1,
                    created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_network_onboarding (
                    id VARCHAR(36) PRIMARY KEY, network_id VARCHAR(36) UNIQUE,
                    status VARCHAR(24), kyb_tier VARCHAR(16), compliance_score REAL,
                    documents_json TEXT, reviewer VARCHAR(128), notes TEXT,
                    submitted_at TEXT, approved_at TEXT, live_at TEXT,
                    created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_sla_breach_incidents (
                    id VARCHAR(36) PRIMARY KEY, network_id VARCHAR(36),
                    sla_policy_id VARCHAR(36), contract_id VARCHAR(36),
                    metric_code VARCHAR(64), target_value REAL, measured_value REAL,
                    severity VARCHAR(16), status VARCHAR(20), penalty_cents INTEGER,
                    currency VARCHAR(8), detected_at TEXT, acknowledged_at TEXT,
                    resolved_at TEXT, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_settlement_batches (
                    id VARCHAR(36) PRIMARY KEY, operator_id VARCHAR(36),
                    batch_code VARCHAR(32) UNIQUE, period_start TEXT, period_end TEXT,
                    gross_cents INTEGER, commission_cents INTEGER, adjustments_cents INTEGER,
                    net_cents INTEGER, currency VARCHAR(8), status VARCHAR(20),
                    approved_by VARCHAR(128), paid_at TEXT, created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_capacity_snapshots (
                    id VARCHAR(36) PRIMARY KEY, network_id VARCHAR(36),
                    snapshot_date TEXT, total_slots INTEGER, occupied_slots INTEGER,
                    reserved_slots INTEGER, utilization_pct REAL, peak_hour_local INTEGER,
                    created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_contract_disputes (
                    id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36),
                    dispute_type VARCHAR(32), amount_cents INTEGER, currency VARCHAR(8),
                    status VARCHAR(20), reason VARCHAR(255), resolution_note TEXT,
                    opened_at TEXT, closed_at TEXT, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_renewal_offers (
                    id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36),
                    offer_amount_cents INTEGER, currency VARCHAR(8), billing_cycle VARCHAR(20),
                    valid_until TEXT, status VARCHAR(20), auto_renew INTEGER,
                    sent_at TEXT, responded_at TEXT, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO rental_networks (id, code, name, network_type, active, created_at, updated_at)
                VALUES ('net-1', 'INPOST', 'InPost', 'LOCKER_NETWORK', 1, datetime('now'), datetime('now'))
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO rental_network_onboarding (
                    id, network_id, status, kyb_tier, compliance_score, documents_json, created_at, updated_at
                ) VALUES ('ob-1', 'net-1', 'LIVE', 'PREMIUM', 90, '[]', datetime('now'), datetime('now'))
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO rental_capacity_snapshots (
                    id, network_id, snapshot_date, total_slots, occupied_slots,
                    reserved_slots, utilization_pct, created_at
                ) VALUES ('cap-1', 'net-1', date('now'), 100, 75, 5, 75.0, datetime('now'))
                """
            )
        )

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
    app.dependency_overrides[require_internal_token] = lambda: True
    client = TestClient(app)
    yield client, path
    engine.dispose()
    import os

    try:
        os.remove(path)
    except OSError:
        pass


def test_premium_summary(premium_client):
    client, _ = premium_client
    r = client.get("/internal/rentals/analytics/premium-summary", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    s = r.json()["summary"]
    assert s["onboarding_live"] >= 1


def test_network_health(premium_client):
    client, _ = premium_client
    r = client.get("/internal/rentals/analytics/network-health", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    assert r.json()["items"][0]["health_score"] > 0


def test_list_onboarding(premium_client):
    client, _ = premium_client
    r = client.get("/internal/rentals/onboarding", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    assert r.json()["total"] >= 1
