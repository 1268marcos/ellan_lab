"""Testes do módulo mundial de assinaturas."""
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
                    monthly_fee_cents INTEGER, is_active INTEGER DEFAULT 1
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE customer_subscriptions (
                    id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), plan_type VARCHAR(30),
                    status VARCHAR(20) DEFAULT 'ACTIVE', monthly_fee_cents INTEGER DEFAULT 0,
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
            CREATE TABLE subscription_regional_prices (
                id VARCHAR(36) PRIMARY KEY, plan_code VARCHAR(20), region_code VARCHAR(8),
                currency VARCHAR(8), monthly_fee_cents INTEGER, yearly_fee_cents INTEGER,
                tax_inclusive INTEGER DEFAULT 1, active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT,
                UNIQUE (plan_code, region_code)
            )
            """,
            """
            CREATE TABLE subscription_plan_addons (
                id VARCHAR(36) PRIMARY KEY, code VARCHAR(32) UNIQUE, name VARCHAR(128),
                addon_type VARCHAR(32), monthly_fee_cents INTEGER, min_plan_code VARCHAR(20),
                regions_json TEXT, active INTEGER DEFAULT 1, metadata_json TEXT,
                created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_active_addons (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36), addon_code VARCHAR(32),
                status VARCHAR(20), monthly_fee_cents INTEGER, started_at TEXT, ended_at TEXT,
                created_at TEXT, UNIQUE (subscription_id, addon_code)
            )
            """,
            """
            CREATE TABLE subscription_pause_periods (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36),
                pause_start TEXT, pause_end TEXT, reason VARCHAR(64), status VARCHAR(20), created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_sla_targets (
                id VARCHAR(36) PRIMARY KEY, plan_code VARCHAR(20), region_code VARCHAR(8),
                metric_code VARCHAR(32), target_value REAL, unit VARCHAR(16),
                description TEXT, active INTEGER DEFAULT 1, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_partner_settlements (
                id VARCHAR(36) PRIMARY KEY, partner_code VARCHAR(64), period_month VARCHAR(7),
                subscription_count INTEGER, gross_cents INTEGER, share_pct REAL, net_cents INTEGER,
                currency VARCHAR(8), status VARCHAR(20), paid_at TEXT, created_at TEXT,
                UNIQUE (partner_code, period_month)
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
            CREATE TABLE subscription_consent_records (
                id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), consent_type VARCHAR(32),
                policy_version VARCHAR(16), locale VARCHAR(8), accepted_at TEXT, metadata_json TEXT,
                UNIQUE (user_id, consent_type, policy_version)
            )
            """,
        ):
            conn.execute(text(ddl))
        conn.execute(
            text(
                "INSERT INTO subscription_plans (id, name, code, monthly_fee_cents, is_active) VALUES ('p1','Pro','PRO',4990,1)"
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO customer_subscriptions (id, user_id, plan_type, status, monthly_fee_cents, created_at, updated_at)
                VALUES ('sub-1', 'user-1', 'PRO', 'ACTIVE', 4990, datetime('now'), datetime('now'))
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


def test_world_seed_and_summary(client: TestClient):
    seed = client.post("/v1/subscriptions-admin/world/seed")
    assert seed.status_code == 200
    assert seed.json()["seeded"]["regional_prices"] >= 1

    summary = client.get("/v1/subscriptions-admin/world/summary")
    assert summary.status_code == 200
    assert summary.json()["counts"]["regional_prices"] >= 1


def test_regional_prices_and_addons(client: TestClient):
    client.post("/v1/subscriptions-admin/world/seed")
    prices = client.get("/v1/subscriptions-admin/world/regional-prices", params={"plan_code": "PRO"})
    assert prices.status_code == 200
    assert any(p["region_code"] == "BR" for p in prices.json()["items"])

    client.post(
        "/v1/subscriptions-admin/world/addons/attach",
        json={"subscription_id": "sub-1", "addon_code": "FAMILY_SEAT"},
    )
    active = client.get(
        "/v1/subscriptions-admin/world/addons/active",
        params={"subscription_id": "sub-1"},
    )
    assert active.status_code == 200
    assert active.json()["total"] >= 1


def test_retention_offer_accept(client: TestClient):
    client.post("/v1/subscriptions-admin/world/seed")
    offers = client.get("/v1/subscriptions-admin/world/retention-offers")
    assert offers.status_code == 200
    assert offers.json()["total"] >= 1
    oid = offers.json()["items"][0]["id"]
    accepted = client.post(f"/v1/subscriptions-admin/world/retention-offers/{oid}/accept")
    assert accepted.status_code == 200
    assert accepted.json()["ok"] is True
