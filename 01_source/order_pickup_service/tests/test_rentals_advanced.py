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
def advanced_client():
    engine, SessionLocal, path = _sqlite_session()
    with engine.begin() as conn:
        for ddl in (
            """
            CREATE TABLE IF NOT EXISTS rental_access_passes (
                id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36) NOT NULL,
                pass_type VARCHAR(16), pass_code_hash VARCHAR(128), pass_hint VARCHAR(16),
                valid_from TEXT, valid_until TEXT, max_uses INTEGER, use_count INTEGER,
                status VARCHAR(20), revoked_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rental_deposit_holds (
                id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36),
                amount_cents INTEGER, currency VARCHAR(8), status VARCHAR(20),
                hold_reason VARCHAR(64), payment_ref VARCHAR(64),
                held_at TEXT, released_at TEXT, forfeited_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rental_slot_blocks (
                id VARCHAR(36) PRIMARY KEY, locker_id VARCHAR(36), slot_label VARCHAR(20),
                block_type VARCHAR(24), reason VARCHAR(255), starts_at TEXT, ends_at TEXT,
                created_by VARCHAR(128), active INTEGER DEFAULT 1, created_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rental_pricing_rules (
                id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) UNIQUE, name VARCHAR(128),
                network_id VARCHAR(36), slot_size VARCHAR(8), billing_cycle VARCHAR(20),
                base_amount_cents INTEGER, surge_multiplier REAL, valid_from TEXT, valid_until TEXT,
                priority INTEGER, active INTEGER DEFAULT 1, created_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rental_dunning_cases (
                id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36), invoice_id VARCHAR(36),
                stage VARCHAR(20), amount_due_cents INTEGER, currency VARCHAR(8),
                status VARCHAR(20), next_action_at TEXT, closed_at TEXT, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rental_transfer_requests (
                id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36),
                from_locker_id VARCHAR(36), from_slot_label VARCHAR(20),
                to_locker_id VARCHAR(36), to_slot_label VARCHAR(20),
                status VARCHAR(20), requested_by VARCHAR(128),
                approved_at TEXT, completed_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rental_billing_invoices (
                id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36), invoice_number VARCHAR(32),
                period_start TEXT, period_end TEXT, amount_cents INTEGER, currency VARCHAR(8),
                status VARCHAR(20), due_at TEXT, paid_at TEXT, created_at TEXT, updated_at TEXT
            )
            """,
        ):
            conn.execute(text(ddl))
        conn.execute(text("DELETE FROM rental_contracts WHERE id = 'c-active'"))
        conn.execute(
            text(
                """
                INSERT INTO rental_contracts (
                    id, locker_id, slot_label, amount_cents, currency, billing_cycle,
                    status, created_at, updated_at
                ) VALUES (
                    'c-active', 'locker-a', '01A', 10000, 'BRL', 'MONTHLY', 'PENDING',
                    datetime('now'), datetime('now')
                )
                """
            )
        )
        conn.execute(text("DELETE FROM locker_slots WHERE locker_id = 'locker-a' AND slot_label = '01A'"))
        conn.execute(
            text(
                """
                INSERT INTO locker_slots (
                    id, locker_id, slot_label, slot_size, status, updated_at
                ) VALUES (
                    'slot-01a', 'locker-a', '01A', 'M', 'AVAILABLE', datetime('now')
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO rental_pricing_rules (
                    id, code, name, base_amount_cents, surge_multiplier, priority, active, created_at
                ) VALUES (
                    'rule-1', 'BASE_M', 'Base M', 9900, 1.0, 10, 1, datetime('now')
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
    import os

    try:
        os.remove(path)
    except OSError:
        pass


def test_activate_contract(advanced_client):
    client, _ = advanced_client
    r = client.post("/internal/rentals/contracts/c-active/activate", headers={"X-Internal-Token": "x"})
    assert r.status_code == 200
    assert r.json()["status"] == "ACTIVE"


def test_issue_access_pass(advanced_client):
    client, _ = advanced_client
    client.post("/internal/rentals/contracts/c-active/activate", headers={"X-Internal-Token": "x"})
    r = client.post(
        "/internal/rentals/contracts/c-active/access-passes",
        headers={"X-Internal-Token": "x"},
        json={"pass_type": "PIN", "valid_hours": 24},
    )
    assert r.status_code == 201
    assert "pass_code" in r.json()


def test_pricing_quote(advanced_client):
    client, _ = advanced_client
    r = client.post(
        "/internal/rentals/pricing/quote",
        headers={"X-Internal-Token": "x"},
        json={"slot_size": "M", "billing_cycle": "MONTHLY"},
    )
    assert r.status_code == 200
    assert r.json()["quoted"] is True
    assert r.json()["amount_cents"] == 9900
