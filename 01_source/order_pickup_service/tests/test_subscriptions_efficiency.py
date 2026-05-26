"""Testes do módulo de eficiência de assinaturas."""
from __future__ import annotations

import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.db import get_db
from app.routers import subscriptions_ops as subscriptions_ops_router


def _sqlite_session():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE subscription_plans (
                    id VARCHAR(36) PRIMARY KEY, name VARCHAR(50), code VARCHAR(20) UNIQUE,
                    monthly_fee_cents INTEGER, free_shipping INTEGER DEFAULT 0,
                    priority_shelf INTEGER DEFAULT 0, exclusive_deals INTEGER DEFAULT 0,
                    max_orders_per_month INTEGER, is_active INTEGER DEFAULT 1
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE customer_subscriptions (
                    id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), plan_type VARCHAR(30),
                    status VARCHAR(20) DEFAULT 'ACTIVE', monthly_fee_cents INTEGER,
                    free_shipping INTEGER DEFAULT 0, priority_shelf INTEGER DEFAULT 0,
                    exclusive_deals INTEGER DEFAULT 0, billing_cycle VARCHAR(20) DEFAULT 'MONTHLY',
                    cancel_at_period_end INTEGER DEFAULT 0,
                    trial_start TEXT, trial_end TEXT, current_period_start TEXT, current_period_end TEXT,
                    next_billing_at TEXT, partner_code VARCHAR(64), created_at TEXT, updated_at TEXT
                )
                """
            )
        )
        for ddl in (
            """
            CREATE TABLE subscription_events (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36), event_type VARCHAR(64),
                actor_id VARCHAR(64), payload_json TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_dunning_cases (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36), stage VARCHAR(32),
                status VARCHAR(20), amount_due_cents INTEGER, opened_at TEXT,
                resolved_at TEXT, resolution_note TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_churn_alerts (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36) NOT NULL,
                alert_type VARCHAR(32) NOT NULL, severity VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
                message TEXT NOT NULL, resolved_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_renewal_queue (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36) NOT NULL,
                scheduled_at TEXT NOT NULL, status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                attempt_count INTEGER NOT NULL DEFAULT 0, last_error TEXT,
                executed_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_retention_offers (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36), offer_code VARCHAR(32),
                discount_pct REAL, bonus_months INTEGER, valid_until TEXT, status VARCHAR(20),
                accepted_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_promo_codes (
                id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) UNIQUE, description TEXT,
                discount_pct REAL DEFAULT 0, discount_cents INTEGER DEFAULT 0, bonus_months INTEGER DEFAULT 0,
                eligible_plans_json TEXT, max_redemptions INTEGER, redemption_count INTEGER DEFAULT 0,
                partner_code VARCHAR(64), valid_from TEXT, valid_until TEXT,
                active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_promo_redemptions (
                id VARCHAR(36) PRIMARY KEY, promo_code_id VARCHAR(36), user_id VARCHAR(36),
                subscription_id VARCHAR(36), discount_applied_cents INTEGER DEFAULT 0,
                redeemed_at TEXT, UNIQUE (promo_code_id, user_id)
            )
            """,
            """
            CREATE TABLE subscription_plan_changes (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36),
                from_plan_code VARCHAR(20), to_plan_code VARCHAR(20), change_type VARCHAR(16),
                proration_cents INTEGER DEFAULT 0, effective_at TEXT, actor_id VARCHAR(64),
                notes TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_usage_meters (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36), meter_code VARCHAR(32),
                period_month VARCHAR(7), quantity INTEGER DEFAULT 0, included_quantity INTEGER,
                overage_cents INTEGER DEFAULT 0, recorded_at TEXT,
                UNIQUE (subscription_id, meter_code, period_month)
            )
            """,
            """
            CREATE TABLE subscription_automation_rules (
                id VARCHAR(36) PRIMARY KEY, rule_code VARCHAR(32) UNIQUE, name VARCHAR(128),
                trigger_event VARCHAR(64), action_type VARCHAR(32), config_json TEXT,
                priority INTEGER DEFAULT 100, active INTEGER DEFAULT 1,
                last_run_at TEXT, run_count INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_family_members (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36), member_user_id VARCHAR(36),
                role VARCHAR(16), status VARCHAR(20), invited_at TEXT, joined_at TEXT,
                UNIQUE (subscription_id, member_user_id)
            )
            """,
        ):
            conn.execute(text(ddl))
        conn.execute(
            text(
                """
                INSERT INTO subscription_plans (
                    id, name, code, monthly_fee_cents, free_shipping, priority_shelf,
                    exclusive_deals, max_orders_per_month, is_active
                ) VALUES
                ('p-basic', 'Basic', 'BASIC', 990, 0, 0, 0, 10, 1),
                ('p-prem', 'Premium', 'PREMIUM', 2490, 1, 1, 0, 30, 1),
                ('p-pro', 'Pro', 'PRO', 4990, 1, 1, 1, 100, 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO customer_subscriptions (
                    id, user_id, plan_type, status, monthly_fee_cents, created_at, updated_at
                ) VALUES ('sub-eff-1', 'user-eff-1', 'BASIC', 'ACTIVE', 990, datetime('now'), datetime('now'))
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO subscription_churn_alerts (
                    id, subscription_id, alert_type, severity, message, created_at
                ) VALUES ('churn-1', 'sub-eff-1', 'USAGE_DROP', 'HIGH', 'Queda de uso', datetime('now'))
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO subscription_renewal_queue (
                    id, subscription_id, scheduled_at, status, created_at
                ) VALUES ('renew-1', 'sub-eff-1', datetime('now', '-2 days'), 'PENDING', datetime('now'))
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO subscription_dunning_cases (
                    id, subscription_id, stage, status, amount_due_cents, opened_at
                ) VALUES ('dun-1', 'sub-eff-1', 'DAY_7', 'OPEN', 990, datetime('now'))
                """
            )
        )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def _get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    return _get_db


@pytest.fixture()
def client():
    get_db_override = _sqlite_session()
    app = FastAPI()
    app.dependency_overrides[get_db] = get_db_override
    app.include_router(subscriptions_ops_router.router, prefix="/v1/subscriptions-admin")
    with TestClient(app) as c:
        yield c


def test_efficiency_seed_and_summary(client: TestClient):
    seed = client.post("/v1/subscriptions-admin/efficiency/seed")
    assert seed.status_code == 200
    assert seed.json()["seeded"]["promo_codes"] >= 1

    summary = client.get("/v1/subscriptions-admin/efficiency/summary")
    assert summary.status_code == 200
    assert summary.json()["counts"]["promo_codes"] >= 1


def test_promo_validate_and_plan_change(client: TestClient):
    client.post("/v1/subscriptions-admin/efficiency/seed")

    valid = client.post(
        "/v1/subscriptions-admin/efficiency/promo-codes/validate",
        json={"code": "WELCOME20", "user_id": "user-new", "plan_code": "BASIC"},
    )
    assert valid.status_code == 200
    assert valid.json()["valid"] is True
    assert valid.json()["discount_pct"] == 20

    change = client.post(
        "/v1/subscriptions-admin/efficiency/plan-changes",
        json={"subscription_id": "sub-eff-1", "to_plan_code": "PREMIUM"},
    )
    assert change.status_code == 200
    assert change.json()["to_plan"] == "PREMIUM"
    assert change.json()["change_type"] == "UPGRADE"


def test_usage_meter_and_upgrade_matrix(client: TestClient):
    client.post(
        "/v1/subscriptions-admin/efficiency/usage-meters/record",
        json={"subscription_id": "sub-eff-1", "meter_code": "ORDERS", "quantity": 9},
    )
    matrix = client.get("/v1/subscriptions-admin/efficiency/upgrade-matrix")
    assert matrix.status_code == 200
    assert matrix.json()["ok"] is True

    inbox = client.get("/v1/subscriptions-admin/efficiency/ops-inbox")
    assert inbox.status_code == 200
    body = inbox.json()
    assert "items" in body
    assert body.get("bulk_operations")
    kinds = {i["kind"] for i in body["items"]}
    assert "UPGRADE" in kinds


def test_inbox_actions_churn_renewal_and_bulk(client: TestClient):
    churn_resolve = client.post(
        "/v1/subscriptions-admin/efficiency/ops-inbox/act",
        json={"kind": "CHURN", "id": "churn-1", "action": "resolve"},
    )
    assert churn_resolve.status_code == 200
    assert churn_resolve.json()["ok"] is True

    renewal_process = client.post(
        "/v1/subscriptions-admin/efficiency/ops-inbox/act",
        json={"kind": "RENEWAL", "id": "renew-1", "action": "process"},
    )
    assert renewal_process.status_code == 200

    dunning_resolve = client.post(
        "/v1/subscriptions-admin/efficiency/ops-inbox/act",
        json={"kind": "DUNNING", "id": "dun-1", "action": "resolve"},
    )
    assert dunning_resolve.status_code == 200

    bulk = client.post(
        "/v1/subscriptions-admin/efficiency/ops-inbox/bulk",
        json={"operation": "churn_resolve_high"},
    )
    assert bulk.status_code == 200
    assert "processed" in bulk.json()

    inbox = client.get("/v1/subscriptions-admin/efficiency/ops-inbox")
    kinds = {i["kind"] for i in inbox.json()["items"]}
    assert "CHURN" not in kinds or all(i["id"] != "churn-1" for i in inbox.json()["items"] if i["kind"] == "CHURN")
