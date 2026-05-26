"""Testes da API pública B2C e parceiros de assinaturas."""
from __future__ import annotations

import hashlib
import os
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_verified_public_user
from app.core.db import get_db
from app.routers.subscriptions_partner_api import router as partner_router
from app.routers.subscriptions_public import router as public_router


class FakeUser:
    id = "user-b2c-1"
    is_active = True
    email_verified = True


PARTNER_CODE = "magalu_test"
RAW_API_KEY = "sub_testkey_for_magalu_partner"
KEY_HASH = hashlib.sha256(RAW_API_KEY.encode("utf-8")).hexdigest()


def _sqlite_session():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(f"sqlite:///{path}", future=True, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        for ddl in (
            """
            CREATE TABLE subscription_plans (
                id VARCHAR(36) PRIMARY KEY, name VARCHAR(50), code VARCHAR(20) UNIQUE,
                monthly_fee_cents INTEGER, yearly_fee_cents INTEGER,
                free_shipping INTEGER DEFAULT 0, priority_shelf INTEGER DEFAULT 0,
                exclusive_deals INTEGER DEFAULT 0, priority_support INTEGER DEFAULT 0,
                max_orders_per_month INTEGER, max_discount_pct REAL,
                is_active INTEGER DEFAULT 1
            )
            """,
            """
            CREATE TABLE customer_subscriptions (
                id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), plan_type VARCHAR(30),
                status VARCHAR(20) DEFAULT 'ACTIVE', monthly_fee_cents INTEGER,
                free_shipping INTEGER DEFAULT 0, priority_shelf INTEGER DEFAULT 0,
                exclusive_deals INTEGER DEFAULT 0, billing_cycle VARCHAR(20) DEFAULT 'MONTHLY',
                cancel_at_period_end INTEGER DEFAULT 0,
                trial_start TEXT, trial_end TEXT, current_period_start TEXT, current_period_end TEXT,
                next_billing_at TEXT, cancelled_at TEXT, partner_code VARCHAR(64),
                started_at TEXT, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_benefits_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT, subscription_id VARCHAR(36),
                usage_month TEXT, benefit_type VARCHAR(30),
                usage_count INTEGER DEFAULT 0, usage_limit INTEGER,
                created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT, subscription_id VARCHAR(36),
                usage_month TEXT, orders_count INTEGER DEFAULT 0,
                free_shipping_used INTEGER DEFAULT 0, savings_cents INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE subscription_invoices (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36),
                period_start TEXT, period_end TEXT, amount_cents INTEGER,
                currency VARCHAR(8) DEFAULT 'BRL', status VARCHAR(20), paid_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_plan_entitlements (
                id VARCHAR(36) PRIMARY KEY, plan_code VARCHAR(20), player_code VARCHAR(64),
                player_name VARCHAR(128), player_type VARCHAR(32), enabled INTEGER DEFAULT 1,
                priority_level INTEGER DEFAULT 0
            )
            """,
            """
            CREATE TABLE subscription_loyalty_ledger (
                id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36), points_delta INTEGER,
                reason VARCHAR(64), balance_after INTEGER, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_referrals (
                id VARCHAR(36) PRIMARY KEY, referrer_user_id VARCHAR(36),
                referral_code VARCHAR(32) UNIQUE, reward_cents INTEGER, status VARCHAR(20), created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_events (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36), event_type VARCHAR(64),
                actor_id VARCHAR(64), payload_json TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_api_keys (
                id VARCHAR(36) PRIMARY KEY, partner_code VARCHAR(64), key_prefix VARCHAR(16),
                key_hash VARCHAR(128), label VARCHAR(64), scopes_json TEXT NOT NULL,
                expires_at TEXT, last_used_at TEXT, revoked_at TEXT, created_at TEXT
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
        ):
            conn.execute(text(ddl))
        conn.execute(
            text(
                """
                INSERT INTO subscription_plans (
                    id, name, code, monthly_fee_cents, free_shipping, priority_shelf, exclusive_deals, is_active
                ) VALUES
                ('p-basic', 'Basic', 'BASIC', 990, 0, 0, 0, 1),
                ('p-prem', 'Premium', 'PREMIUM', 2490, 1, 1, 0, 1),
                ('p-pro', 'Pro', 'PRO', 4990, 1, 1, 1, 1)
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO subscription_promo_codes (
                    id, code, description, discount_pct, discount_cents, bonus_months,
                    eligible_plans_json, max_redemptions, redemption_count, active, created_at, updated_at
                ) VALUES (
                    'promo-1', 'WELCOME20', 'Boas-vindas', 20, 0, 0,
                    '["BASIC","PREMIUM"]', 100, 0, 1, datetime('now'), datetime('now')
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO subscription_api_keys (
                    id, partner_code, key_prefix, key_hash, label, scopes_json, created_at
                ) VALUES ('k1', :p, 'sub_magalu', :h, 'test', :scopes, datetime('now'))
                """
            ),
            {
                "p": PARTNER_CODE,
                "h": KEY_HASH,
                "scopes": '["subscriptions:read","subscriptions:webhook"]',
            },
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
def public_client():
    get_db_override = _sqlite_session()
    app = FastAPI()
    app.dependency_overrides[get_db] = get_db_override
    app.dependency_overrides[get_current_verified_public_user] = lambda: FakeUser()
    app.include_router(public_router)
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def partner_client():
    get_db_override = _sqlite_session()
    app = FastAPI()
    app.dependency_overrides[get_db] = get_db_override
    app.include_router(partner_router)
    with TestClient(app) as c:
        yield c


def test_public_my_without_subscription(public_client: TestClient):
    r = public_client.get("/public/subscriptions/my")
    assert r.status_code == 200
    assert r.json()["has_subscription"] is False


def test_public_subscribe_and_my(public_client: TestClient):
    sub = public_client.post(
        "/public/subscriptions/my/subscribe",
        json={"plan_code": "PREMIUM", "trial_days": 7},
    )
    assert sub.status_code == 200
    body = sub.json()
    assert body["has_subscription"] is True
    assert body["subscription"]["plan_type"] == "PREMIUM"
    assert body["subscription"]["status"] == "TRIALING"

    dup = public_client.post(
        "/public/subscriptions/my/subscribe",
        json={"plan_code": "PREMIUM"},
    )
    assert dup.status_code == 409

    plans = public_client.get("/public/subscriptions/my/plans")
    assert plans.status_code == 200
    assert plans.json()["total"] >= 1


def test_public_benefit_check_and_cancel(public_client: TestClient):
    public_client.post("/public/subscriptions/my/subscribe", json={"plan_code": "PREMIUM"})
    chk = public_client.post(
        "/public/subscriptions/my/benefit-check",
        json={"benefit_type": "FREE_SHIPPING"},
    )
    assert chk.status_code == 200
    assert chk.json()["eligible"] is True

    ref = public_client.get("/public/subscriptions/my/referral")
    assert ref.status_code == 200
    assert ref.json()["referral_code"].startswith("ELLAN-")

    cancel = public_client.post("/public/subscriptions/my/cancel", json={"immediate": False})
    assert cancel.status_code == 200
    my = public_client.get("/public/subscriptions/my")
    assert my.json()["subscription"]["cancel_at_period_end"] is True


def test_partner_lookup_and_benefit_check(partner_client: TestClient):
    headers = {"X-Partner-Code": PARTNER_CODE, "X-API-Key": RAW_API_KEY}
    health = partner_client.get("/api/subscriptions/partner/v1/health", headers=headers)
    assert health.status_code == 200

    lookup = partner_client.get(
        "/api/subscriptions/partner/v1/subscribers/user-unknown",
        headers=headers,
    )
    assert lookup.status_code == 200
    assert lookup.json()["found"] is False

    bad = partner_client.get(
        "/api/subscriptions/partner/v1/subscribers/user-unknown",
        headers={"X-Partner-Code": PARTNER_CODE, "X-API-Key": "wrong"},
    )
    assert bad.status_code == 401


def test_public_promo_validate_and_change_plan(public_client: TestClient):
    public_client.post("/public/subscriptions/my/subscribe", json={"plan_code": "BASIC"})

    promo = public_client.post(
        "/public/subscriptions/promo/validate",
        params={"code": "WELCOME20", "plan_code": "BASIC"},
    )
    assert promo.status_code == 200
    assert promo.json()["valid"] is True

    change = public_client.post(
        "/public/subscriptions/my/change-plan",
        json={"plan_code": "PREMIUM"},
    )
    assert change.status_code == 200
    assert change.json()["to_plan"] == "PREMIUM"

    suggestions = public_client.get("/public/subscriptions/my/upgrade-suggestions")
    assert suggestions.status_code == 200
    assert suggestions.json()["ok"] is True


def test_public_subscribe_with_promo_redemption(public_client: TestClient):
    sub = public_client.post(
        "/public/subscriptions/my/subscribe",
        json={"plan_code": "BASIC", "promo_code": "WELCOME20"},
    )
    assert sub.status_code == 200
    body = sub.json()
    assert body["promo_applied"]["promo_code"] == "WELCOME20"
    assert body["promo_applied"]["discount_cents"] > 0
    assert body["subscription"]["monthly_fee_cents"] < 990

    dup_promo = public_client.post(
        "/public/subscriptions/my/subscribe",
        json={"plan_code": "PREMIUM", "promo_code": "WELCOME20"},
    )
    assert dup_promo.status_code == 409
