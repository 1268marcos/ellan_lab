from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.core.db import get_db
from app.core.internal_auth import require_internal_token
from app.routers import rentals_ops as rentals_ops_router
from tests.test_rentals_ops import _sqlite_session


def _billing_tables(conn) -> None:
    for ddl in (
        """
        CREATE TABLE IF NOT EXISTS rental_pricing_rules (
            id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) UNIQUE, name VARCHAR(128),
            network_id VARCHAR(36), slot_size VARCHAR(8), billing_cycle VARCHAR(20),
            base_amount_cents INTEGER, surge_multiplier REAL, valid_from TEXT, valid_until TEXT,
            priority INTEGER, active INTEGER DEFAULT 1, created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS rental_billing_invoices (
            id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36), invoice_number VARCHAR(32),
            period_start TEXT, period_end TEXT, amount_cents INTEGER, currency VARCHAR(8),
            status VARCHAR(20), due_at TEXT, paid_at TEXT, late_fee_cents INTEGER DEFAULT 0,
            base_amount_cents INTEGER, created_at TEXT, updated_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS rental_late_fee_policies (
            id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) UNIQUE, name VARCHAR(128),
            grace_days INTEGER, fee_type VARCHAR(16), fee_value REAL,
            daily_cap_cents INTEGER, max_fee_cents INTEGER, priority INTEGER, active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS rental_late_fee_charges (
            id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36), invoice_id VARCHAR(36) UNIQUE,
            policy_code VARCHAR(32), days_overdue INTEGER, fee_cents INTEGER,
            currency VARCHAR(8), applied_at TEXT, created_at TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS rental_content_insurance (
            id VARCHAR(36) PRIMARY KEY, contract_id VARCHAR(36), policy_number VARCHAR(32) UNIQUE,
            declared_value_cents INTEGER, premium_cents INTEGER, coverage_cents INTEGER,
            currency VARCHAR(8), status VARCHAR(20), starts_at TEXT, ends_at TEXT,
            created_at TEXT, updated_at TEXT
        )
        """,
    ):
        conn.execute(text(ddl))
    for col, typedef in (
        ("pricing_rule_code", "VARCHAR(32)"),
        ("insurance_premium_cents", "INTEGER DEFAULT 0"),
    ):
        try:
            conn.execute(text(f"ALTER TABLE rental_contracts ADD COLUMN {col} {typedef}"))
        except Exception:
            pass
    conn.execute(
        text(
            """
            INSERT OR IGNORE INTO rental_late_fee_policies (
                id, code, name, grace_days, fee_type, fee_value, max_fee_cents, priority, active, created_at
            ) VALUES (
                'pol-default', 'DEFAULT_OVERDUE', 'Multa demo', 3, 'BPS', 500, 50000, 10, 1, datetime('now')
            )
            """
        )
    )
    conn.execute(
        text(
            """
            INSERT OR IGNORE INTO rental_pricing_rules (
                id, code, name, network_id, slot_size, billing_cycle,
                base_amount_cents, surge_multiplier, priority, active, created_at
            ) VALUES (
                'rule-m', 'TEST_M_MONTH', 'Test M', NULL, 'M', 'MONTHLY',
                12000, 1.0, 1, 1, datetime('now')
            )
            """
        )
    )
    conn.execute(text("DELETE FROM locker_slots WHERE locker_id = 'locker-a' AND slot_label = '02B'"))
    conn.execute(
        text(
            """
            INSERT INTO locker_slots (id, locker_id, slot_label, slot_size, status, updated_at)
            VALUES ('slot-02b', 'locker-a', '02B', 'M', 'AVAILABLE', datetime('now'))
            """
        )
    )


@pytest.fixture()
def billing_client():
    engine, SessionLocal, path = _sqlite_session()
    with engine.begin() as conn:
        _billing_tables(conn)
    app = FastAPI()
    app.include_router(rentals_ops_router.router, prefix="/internal/rentals")

    def _override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[require_internal_token] = lambda: None
    client = TestClient(app)
    yield client
    engine.dispose()


def test_preview_pricing_dynamic_quote(billing_client):
    r = billing_client.post(
        "/internal/rentals/contracts/preview-pricing",
        json={
            "locker_id": "locker-a",
            "slot_label": "02B",
            "slot_size": "M",
            "billing_cycle": "MONTHLY",
            "use_dynamic_pricing": True,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["pricing"]["amount_cents"] == 12000
    assert data["pricing"]["pricing_rule_code"] == "TEST_M_MONTH"


def test_create_contract_with_insurance(billing_client):
    r = billing_client.post(
        "/internal/rentals/contracts",
        json={
            "locker_id": "locker-a",
            "slot_label": "02B",
            "slot_size": "M",
            "billing_cycle": "MONTHLY",
            "use_dynamic_pricing": True,
            "content_insurance": True,
            "declared_value_cents": 100000,
            "renter_name": "Test Insured",
            "status": "PENDING",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["pricing"]["insurance_premium_cents"] >= 500
    assert body.get("content_insurance", {}).get("policy_number", "").startswith("RCI-")


def test_apply_late_fees_on_overdue_invoice(billing_client):
    cr = billing_client.post(
        "/internal/rentals/contracts",
        json={
            "locker_id": "locker-a",
            "slot_label": "02B",
            "amount_cents": 10000,
            "billing_cycle": "MONTHLY",
            "use_dynamic_pricing": False,
            "status": "PENDING",
        },
    )
    assert cr.status_code == 201
    cid = cr.json()["contract"]["id"]
    due = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    inv = billing_client.post(
        "/internal/rentals/billing/invoices",
        json={
            "contract_id": cid,
            "period_start": "2026-01-01T00:00:00Z",
            "period_end": "2026-01-31T00:00:00Z",
            "amount_cents": 10000,
            "currency": "BRL",
            "status": "OVERDUE",
            "due_at": due,
        },
    )
    assert inv.status_code == 201, inv.text
    lf = billing_client.post("/internal/rentals/billing/apply-late-fees")
    assert lf.status_code == 200, lf.text
    assert lf.json().get("applied", 0) >= 1
