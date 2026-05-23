from __future__ import annotations

import os
import tempfile

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.routers import rentals_ops as rentals_ops_router
from tests.test_rentals_ops import _sqlite_session


@pytest.fixture()
def extended_client():
    engine, SessionLocal, path = _sqlite_session()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE rental_networks (
                    id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) UNIQUE, name VARCHAR(128),
                    network_type VARCHAR(32), hardware_vendor VARCHAR(64),
                    primary_countries_json TEXT, website_url VARCHAR(255),
                    active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_network_corridors (
                    id VARCHAR(36) PRIMARY KEY, network_id VARCHAR(36), origin_country CHAR(2),
                    destination_country CHAR(2), sla_hours INTEGER, currency VARCHAR(8),
                    active INTEGER DEFAULT 1, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_operators (
                    id VARCHAR(36) PRIMARY KEY, tenant_id VARCHAR(100), network_id VARCHAR(36),
                    legal_name VARCHAR(255), trade_name VARCHAR(128), operator_code VARCHAR(32),
                    commission_bps INTEGER, status VARCHAR(20), contract_ref VARCHAR(64),
                    contact_email VARCHAR(128), created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_billing_invoices (
                    id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36), invoice_number VARCHAR(32),
                    period_start TEXT, period_end TEXT, amount_cents INTEGER, currency VARCHAR(8),
                    status VARCHAR(20), due_at TEXT, paid_at TEXT, created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_sla_policies (
                    id VARCHAR(36) PRIMARY KEY, network_id VARCHAR(36), metric_code VARCHAR(64),
                    target_value REAL, unit VARCHAR(16), breach_penalty_bps INTEGER,
                    active INTEGER DEFAULT 1, created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE rental_webhook_deliveries (
                    id VARCHAR(36) PRIMARY KEY, endpoint_id VARCHAR(36), contract_id VARCHAR(36),
                    event_type VARCHAR(64), status VARCHAR(20), attempt INTEGER,
                    response_code INTEGER, error_message TEXT, next_retry_at TEXT, created_at TEXT
                )
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
    try:
        os.remove(path)
    except OSError:
        pass


def test_analytics_summary(extended_client):
    client, _ = extended_client
    r = client.get("/internal/rentals/analytics/summary", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    assert "summary" in r.json()


def test_networks_crud(extended_client):
    client, _ = extended_client
    cr = client.post(
        "/internal/rentals/networks",
        headers={"X-Internal-Token": "x"},
        json={"code": "TESTNET", "name": "Test Network", "network_type": "LOCKER_NETWORK", "primary_countries": ["BR"]},
    )
    assert cr.status_code == 201
    lst = client.get("/internal/rentals/networks", headers={"X-Internal-Token": "x"})
    assert any(x["code"] == "TESTNET" for x in lst.json()["items"])


def test_corridor_and_operator(extended_client):
    client, _ = extended_client
    net = client.post(
        "/internal/rentals/networks",
        headers={"X-Internal-Token": "x"},
        json={"code": "CORRIDORNET", "name": "Corridor Net", "primary_countries": ["DE", "FR"]},
    ).json()
    nid = net["id"]
    cor = client.post(
        "/internal/rentals/corridors",
        headers={"X-Internal-Token": "x"},
        json={"network_id": nid, "origin_country": "DE", "destination_country": "FR", "sla_hours": 24},
    )
    assert cor.status_code == 201
    op = client.post(
        "/internal/rentals/operators",
        headers={"X-Internal-Token": "x"},
        json={"network_id": nid, "legal_name": "Test Operator GmbH", "operator_code": "TEST_OP", "tenant_id": "t1"},
    )
    assert op.status_code == 201


def test_contract_events_after_create(extended_client):
    client, _ = extended_client
    cr = client.post(
        "/internal/rentals/contracts",
        headers={"X-Internal-Token": "x"},
        json={
            "locker_id": "locker-a",
            "slot_label": "02B",
            "renter_name": "Event Test",
            "amount_cents": 1000,
            "billing_cycle": "MONTHLY",
            "status": "PENDING",
        },
    )
    assert cr.status_code == 201
    cid = cr.json()["contract"]["id"]
    ev = client.get(f"/internal/rentals/contracts/{cid}/events", headers={"X-Internal-Token": "x"})
    assert ev.status_code == 200
    assert len(ev.json()["items"]) >= 1
