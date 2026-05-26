from __future__ import annotations

import os
import tempfile

import pytest
from fastapi import Depends, FastAPI
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
                    id VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    code VARCHAR(20) NOT NULL UNIQUE,
                    description TEXT,
                    monthly_fee_cents INTEGER NOT NULL,
                    yearly_fee_cents INTEGER,
                    free_shipping INTEGER DEFAULT 0,
                    priority_shelf INTEGER DEFAULT 0,
                    exclusive_deals INTEGER DEFAULT 0,
                    priority_support INTEGER DEFAULT 0,
                    max_orders_per_month INTEGER,
                    max_discount_pct REAL,
                    features_json TEXT DEFAULT '{}',
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE customer_subscriptions (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36),
                    plan_type VARCHAR(30) NOT NULL,
                    status VARCHAR(20) DEFAULT 'ACTIVE',
                    monthly_fee_cents INTEGER NOT NULL,
                    free_shipping INTEGER DEFAULT 0,
                    priority_shelf INTEGER DEFAULT 0,
                    exclusive_deals INTEGER DEFAULT 0,
                    billing_cycle VARCHAR(20) DEFAULT 'MONTHLY',
                    cancel_at_period_end INTEGER DEFAULT 0,
                    trial_start TEXT,
                    trial_end TEXT,
                    current_period_start TEXT,
                    current_period_end TEXT,
                    next_billing_at TEXT,
                    cancelled_at TEXT,
                    payment_method_id VARCHAR(36),
                    partner_code VARCHAR(64),
                    started_at TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE subscription_benefits_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id VARCHAR(36) NOT NULL,
                    usage_month TEXT NOT NULL,
                    benefit_type VARCHAR(30) NOT NULL,
                    usage_count INTEGER DEFAULT 0,
                    usage_limit INTEGER,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE subscription_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subscription_id VARCHAR(36),
                    usage_month TEXT,
                    orders_count INTEGER DEFAULT 0,
                    free_shipping_used INTEGER DEFAULT 0,
                    savings_cents INTEGER DEFAULT 0
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE subscription_webhook_endpoints (
                    id VARCHAR(36) PRIMARY KEY,
                    partner_code VARCHAR(64) NOT NULL UNIQUE,
                    url VARCHAR(500) NOT NULL,
                    secret_hash VARCHAR(128) NOT NULL,
                    secret_key VARCHAR(256),
                    events_json TEXT NOT NULL,
                    active INTEGER DEFAULT 1,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE subscription_api_keys (
                    id VARCHAR(36) PRIMARY KEY,
                    partner_code VARCHAR(64) NOT NULL,
                    key_prefix VARCHAR(16) NOT NULL,
                    key_hash VARCHAR(128) NOT NULL,
                    label VARCHAR(64),
                    scopes_json TEXT NOT NULL,
                    expires_at TEXT,
                    last_used_at TEXT,
                    revoked_at TEXT,
                    created_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO subscription_plans (
                    id, name, code, monthly_fee_cents, free_shipping, priority_shelf, exclusive_deals,
                    is_active, created_at, updated_at
                ) VALUES (
                    'plan-basic', 'Basic', 'BASIC', 990, 0, 0, 0, 1, datetime('now'), datetime('now')
                )
                """
            )
        )
        for ddl_eco in (
            """
            CREATE TABLE subscription_ecosystem_players (
                code VARCHAR(64) PRIMARY KEY, name VARCHAR(128) NOT NULL,
                player_type VARCHAR(32) NOT NULL, segment VARCHAR(32) NOT NULL,
                regions_json TEXT, default_plan_code VARCHAR(20), revenue_share_pct REAL,
                integration_modes_json TEXT, supports_lockers INTEGER DEFAULT 0,
                supports_pudo INTEGER DEFAULT 0, supports_food INTEGER DEFAULT 0,
                supports_marketplace INTEGER DEFAULT 0, priority_flag INTEGER DEFAULT 0,
                active INTEGER DEFAULT 1, metadata_json TEXT, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_player_relations (
                id VARCHAR(36) PRIMARY KEY, from_player_code VARCHAR(64) NOT NULL,
                to_player_code VARCHAR(64) NOT NULL, relation_type VARCHAR(32) NOT NULL,
                integration_mode VARCHAR(16), min_plan_code VARCHAR(20), notes TEXT,
                active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT,
                UNIQUE (from_player_code, to_player_code, relation_type)
            )
            """,
            """
            CREATE TABLE subscription_integration_channels (
                id VARCHAR(36) PRIMARY KEY, player_code VARCHAR(64) NOT NULL,
                channel_kind VARCHAR(16), direction VARCHAR(8), auth_type VARCHAR(16),
                base_url_template VARCHAR(500), webhook_events_json TEXT,
                config_json TEXT, active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_food_delivery_handoffs (
                id VARCHAR(36) PRIMARY KEY, food_platform_code VARCHAR(64) NOT NULL,
                pickup_player_code VARCHAR(64) NOT NULL, handoff_type VARCHAR(16),
                sla_minutes INTEGER, min_plan_code VARCHAR(20), integration_mode VARCHAR(16),
                active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT,
                UNIQUE (food_platform_code, pickup_player_code, handoff_type)
            )
            """,
        ):
            conn.execute(text(ddl_eco))

        for ddl in (
            """
            CREATE TABLE subscription_events (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36) NOT NULL,
                event_type VARCHAR(64) NOT NULL, actor_id VARCHAR(64),
                payload_json TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_invoices (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36) NOT NULL,
                period_start TEXT, period_end TEXT, amount_cents INTEGER NOT NULL,
                currency VARCHAR(8) DEFAULT 'BRL', status VARCHAR(20) DEFAULT 'OPEN',
                payment_ref VARCHAR(128), paid_at TEXT, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_plan_entitlements (
                id VARCHAR(36) PRIMARY KEY, plan_code VARCHAR(20) NOT NULL,
                player_code VARCHAR(64) NOT NULL, player_name VARCHAR(128) NOT NULL,
                player_type VARCHAR(32), region_codes_json TEXT, enabled INTEGER DEFAULT 1,
                priority_level INTEGER DEFAULT 0, created_at TEXT, updated_at TEXT,
                UNIQUE (plan_code, player_code)
            )
            """,
            """
            CREATE TABLE subscription_partner_programs (
                id VARCHAR(36) PRIMARY KEY, partner_code VARCHAR(64) NOT NULL UNIQUE,
                partner_name VARCHAR(128) NOT NULL, partner_type VARCHAR(32),
                default_plan_code VARCHAR(20), revenue_share_pct REAL DEFAULT 0,
                countries_json TEXT, kyb_status VARCHAR(20), webhook_enabled INTEGER DEFAULT 1,
                active INTEGER DEFAULT 1, created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_webhook_deliveries (
                id VARCHAR(36) PRIMARY KEY, endpoint_id VARCHAR(36) NOT NULL,
                subscription_id VARCHAR(36), event_type VARCHAR(64),
                http_status INTEGER, attempt_no INTEGER DEFAULT 1,
                error_message TEXT, payload_json TEXT, delivered_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_dunning_cases (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36) NOT NULL,
                stage VARCHAR(16), status VARCHAR(20), amount_due_cents INTEGER,
                opened_at TEXT, resolved_at TEXT, resolution_note TEXT,
                created_at TEXT, updated_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_health_snapshots (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36) NOT NULL,
                health_score INTEGER NOT NULL DEFAULT 50, churn_risk VARCHAR(16) NOT NULL DEFAULT 'LOW',
                factors_json TEXT NOT NULL DEFAULT '{}', computed_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_referrals (
                id VARCHAR(36) PRIMARY KEY, referrer_user_id VARCHAR(36) NOT NULL,
                referred_user_id VARCHAR(36), referral_code VARCHAR(32) NOT NULL UNIQUE,
                reward_cents INTEGER NOT NULL DEFAULT 500, status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                converted_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_gift_codes (
                id VARCHAR(36) PRIMARY KEY, gift_code VARCHAR(24) NOT NULL UNIQUE,
                purchaser_user_id VARCHAR(36) NOT NULL, recipient_email VARCHAR(128),
                plan_code VARCHAR(20) NOT NULL, months INTEGER NOT NULL DEFAULT 1,
                status VARCHAR(20) NOT NULL DEFAULT 'ISSUED', redeemed_by_user_id VARCHAR(36),
                redeemed_at TEXT, expires_at TEXT, created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_loyalty_ledger (
                id VARCHAR(36) PRIMARY KEY, user_id VARCHAR(36) NOT NULL,
                subscription_id VARCHAR(36), points_delta INTEGER NOT NULL,
                reason VARCHAR(64) NOT NULL, balance_after INTEGER NOT NULL DEFAULT 0,
                created_at TEXT
            )
            """,
            """
            CREATE TABLE subscription_price_experiments (
                id VARCHAR(36) PRIMARY KEY, experiment_code VARCHAR(32) NOT NULL,
                plan_code VARCHAR(20) NOT NULL, variant VARCHAR(16) NOT NULL,
                monthly_fee_cents INTEGER NOT NULL, traffic_pct INTEGER NOT NULL DEFAULT 50,
                conversions INTEGER NOT NULL DEFAULT 0, impressions INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL DEFAULT 1, created_at TEXT, updated_at TEXT,
                UNIQUE (experiment_code, variant)
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
            CREATE TABLE subscription_churn_alerts (
                id VARCHAR(36) PRIMARY KEY, subscription_id VARCHAR(36) NOT NULL,
                alert_type VARCHAR(32) NOT NULL, severity VARCHAR(16) NOT NULL DEFAULT 'MEDIUM',
                message TEXT NOT NULL, resolved_at TEXT, created_at TEXT
            )
            """,
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


def test_list_plans_and_metrics(client: TestClient):
    r = client.get("/v1/subscriptions-admin/plans")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    m = client.get("/v1/subscriptions-admin/metrics/summary")
    assert m.status_code == 200
    assert "mrr_cents" in m.json()["summary"]


def test_create_subscription_and_cancel(client: TestClient):
    created = client.post(
        "/v1/subscriptions-admin/subscriptions",
        json={"user_id": "user-1", "plan_type": "BASIC", "status": "ACTIVE"},
    )
    assert created.status_code == 200
    sub_id = created.json()["id"]
    cancelled = client.post(f"/v1/subscriptions-admin/subscriptions/{sub_id}/cancel?immediate=true")
    assert cancelled.status_code == 200
    got = client.get(f"/v1/subscriptions-admin/subscriptions/{sub_id}")
    assert got.json()["status"] == "CANCELLED"


def test_webhook_and_api_key_rotate(client: TestClient):
    wh = client.put(
        "/v1/subscriptions-admin/webhooks/magalu",
        json={"url": "https://hooks.magalu.test/sub", "events": ["subscription.created"]},
    )
    assert wh.status_code == 200
    assert wh.json()["secret"]
    rot = client.post("/v1/subscriptions-admin/api-keys/magalu/rotate")
    assert rot.status_code == 200
    assert rot.json()["api_key"].startswith("sub_")


def test_seed_idempotent(client: TestClient):
    s1 = client.post("/v1/subscriptions-admin/seed")
    assert s1.status_code == 200
    s2 = client.post("/v1/subscriptions-admin/seed")
    assert s2.status_code == 200


def test_partner_programs_and_360(client: TestClient):
    client.post(
        "/v1/subscriptions-admin/partner-programs",
        json={
            "partner_code": "inpost_test",
            "partner_name": "InPost Test",
            "partner_type": "LOCKER_OPERATOR",
            "default_plan_code": "PRO",
        },
    )
    programs = client.get("/v1/subscriptions-admin/partner-programs")
    assert programs.status_code == 200
    assert programs.json()["total"] >= 1

    sub = client.post(
        "/v1/subscriptions-admin/subscriptions",
        json={"user_id": "user-360", "plan_type": "BASIC"},
    )
    sid = sub.json()["id"]
    view = client.get(f"/v1/subscriptions-admin/subscriptions/{sid}/360")
    assert view.status_code == 200
    assert view.json()["subscription"]["id"] == sid


def test_ecosystem_food_delivery_and_relations(client: TestClient):
    eco = client.get("/v1/subscriptions-admin/ecosystem/catalog")
    cat = eco.json()["catalog"]
    food = cat.get("food_delivery") or []
    codes = {p["code"] for p in food}
    assert "ifood" in codes
    assert "uber_eats" in codes
    assert cat.get("relations_total", 0) >= 20
    sync = client.post("/v1/subscriptions-admin/sync/ecosystem-full")
    assert sync.status_code == 200
    rel = client.get("/v1/subscriptions-admin/ecosystem/relations", params={"relation_type": "FOOD_HANDOFF"})
    assert rel.status_code == 200
    assert rel.json()["total"] >= 3
    handoffs = client.get("/v1/subscriptions-admin/ecosystem/food-handoffs")
    assert handoffs.status_code == 200


def test_priority_global_players_catalog(client: TestClient):
    eco = client.get("/v1/subscriptions-admin/ecosystem/catalog")
    assert eco.status_code == 200
    cat = eco.json()["catalog"]
    codes = set(cat.get("priority_player_codes") or [])
    for required in ("inpost", "dhl", "magalu", "mercado_livre", "amazon", "dpd", "correios", "ctt", "worten", "el_corte_ingles"):
        assert required in codes
    pri = client.get("/v1/subscriptions-admin/players/priority")
    assert pri.status_code == 200
    assert pri.json()["total"] >= 10
    br = client.get("/v1/subscriptions-admin/players/catalog", params={"region": "BR"})
    assert br.status_code == 200
    assert any(p["code"] == "magalu" for p in br.json()["items"])


def test_invoices_and_dunning_flow(client: TestClient):
    sub = client.post(
        "/v1/subscriptions-admin/subscriptions",
        json={"user_id": "user-bill", "plan_type": "BASIC"},
    )
    sid = sub.json()["id"]
    inv = client.post("/v1/subscriptions-admin/invoices/generate", json={"subscription_id": sid})
    assert inv.status_code == 200
    iid = inv.json()["invoice_id"]
    paid = client.post(f"/v1/subscriptions-admin/invoices/{iid}/mark-paid")
    assert paid.status_code == 200


def test_premium_health_referrals_gifts(client: TestClient):
    sub = client.post(
        "/v1/subscriptions-admin/subscriptions",
        json={"user_id": "user-premium", "plan_type": "BASIC", "status": "ACTIVE"},
    )
    assert sub.status_code == 200
    uid = "user-premium"

    matrix = client.get("/v1/subscriptions-admin/plans/compare-matrix")
    assert matrix.status_code == 200
    assert len(matrix.json()["plans"]) >= 1

    benefit = client.post(
        "/v1/subscriptions-admin/benefit-check",
        json={"user_id": uid, "benefit_type": "FREE_SHIPPING"},
    )
    assert benefit.status_code == 200
    assert "eligible" in benefit.json()

    health = client.post("/v1/subscriptions-admin/health/compute-all")
    assert health.status_code == 200
    assert health.json()["computed"] >= 1

    ref = client.post(
        "/v1/subscriptions-admin/referrals",
        json={"referrer_user_id": uid, "reward_cents": 1000},
    )
    assert ref.status_code == 200
    assert ref.json()["referral_code"].startswith("ELLAN-")

    gift = client.post(
        "/v1/subscriptions-admin/gifts/issue",
        json={"purchaser_user_id": uid, "plan_code": "PREMIUM", "months": 1},
    )
    assert gift.status_code == 200
    assert gift.json()["gift_code"].startswith("GIFT-")

    prem = client.post("/v1/subscriptions-admin/premium/seed")
    assert prem.status_code == 200
