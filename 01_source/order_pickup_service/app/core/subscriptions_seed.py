"""Seed idempotente para planos e assinaturas de demonstração."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.subscriptions_global_players import tier_player_map_from_registry
from app.core.subscriptions_ecosystem_sync import sync_full_ecosystem
from app.core.subscriptions_premium_seed import seed_subscriptions_premium
from app.core.subscriptions_world_seed import seed_subscriptions_world
from app.core.subscriptions_efficiency_seed import seed_subscriptions_efficiency

_PLANS: list[dict[str, Any]] = [
    {
        "code": "BASIC",
        "name": "Ellan Basic",
        "description": "Frete padrão em rede nacional · ideal para uso ocasional.",
        "monthly_fee_cents": 990,
        "yearly_fee_cents": 9900,
        "free_shipping": False,
        "priority_shelf": False,
        "exclusive_deals": False,
        "priority_support": False,
        "max_orders_per_month": 8,
        "max_discount_pct": 5.0,
        "features_json": {"tier": "basic", "players": tier_player_map_from_registry().get("BASIC", ["correios", "ctt"])},
    },
    {
        "code": "PREMIUM",
        "name": "Ellan Premium",
        "description": "Frete grátis mensal · prioridade de prateleira · ofertas Magalu/ML.",
        "monthly_fee_cents": 1990,
        "yearly_fee_cents": 19900,
        "free_shipping": True,
        "priority_shelf": True,
        "exclusive_deals": True,
        "priority_support": False,
        "max_orders_per_month": 20,
        "max_discount_pct": 12.0,
        "features_json": {
            "tier": "premium",
            "players": tier_player_map_from_registry().get("PREMIUM", []),
            "free_shipping_quota": 4,
        },
    },
    {
        "code": "PRO",
        "name": "Ellan Pro",
        "description": "Operadores globais · suporte prioritário · integração marketplace.",
        "monthly_fee_cents": 4990,
        "yearly_fee_cents": 49900,
        "free_shipping": True,
        "priority_shelf": True,
        "exclusive_deals": True,
        "priority_support": True,
        "max_orders_per_month": 60,
        "max_discount_pct": 18.0,
        "features_json": {
            "tier": "pro",
            "players": tier_player_map_from_registry().get("PRO", []),
            "free_shipping_quota": 12,
        },
    },
    {
        "code": "ENTERPRISE",
        "name": "Ellan Enterprise",
        "description": "B2B multi-tenant · SLA dedicado · webhooks e API keys dedicadas.",
        "monthly_fee_cents": 14990,
        "yearly_fee_cents": 149900,
        "free_shipping": True,
        "priority_shelf": True,
        "exclusive_deals": True,
        "priority_support": True,
        "max_orders_per_month": None,
        "max_discount_pct": 25.0,
        "features_json": {
            "tier": "enterprise",
            "players": tier_player_map_from_registry().get("ENTERPRISE", []),
            "dedicated_success_manager": True,
        },
    },
]

_DEMO_USERS = ("demo-user-magalu", "demo-user-inpost", "demo-user-enterprise")


def seed_subscriptions(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    created_plans = 0
    created_subs = 0
    created_wh = 0
    created_keys = 0

    for plan in _PLANS:
        exists = db.execute(
            text("SELECT 1 FROM subscription_plans WHERE code = :code LIMIT 1"),
            {"code": plan["code"]},
        ).scalar()
        if exists:
            continue
        pid = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO subscription_plans (
                    id, name, code, description, monthly_fee_cents, yearly_fee_cents,
                    free_shipping, priority_shelf, exclusive_deals, priority_support,
                    max_orders_per_month, max_discount_pct, features_json, is_active,
                    created_at, updated_at
                ) VALUES (
                    :id, :name, :code, :description, :monthly, :yearly,
                    :free_ship, :priority, :deals, :support,
                    :max_orders, :max_disc, :features, TRUE, :now, :now
                )
                """
            ),
            {
                "id": pid,
                "name": plan["name"],
                "code": plan["code"],
                "description": plan["description"],
                "monthly": plan["monthly_fee_cents"],
                "yearly": plan["yearly_fee_cents"],
                "free_ship": plan["free_shipping"],
                "priority": plan["priority_shelf"],
                "deals": plan["exclusive_deals"],
                "support": plan["priority_support"],
                "max_orders": plan["max_orders_per_month"],
                "max_disc": plan["max_discount_pct"],
                "features": json.dumps(plan["features_json"]),
                "now": now,
            },
        )
        created_plans += 1

    plan_rows = db.execute(
        text("SELECT code, monthly_fee_cents, free_shipping, priority_shelf, exclusive_deals FROM subscription_plans")
    ).mappings().all()
    plan_by_code = {str(r["code"]): dict(r) for r in plan_rows}

    assignments = [
        ("demo-user-magalu", "PREMIUM", "ACTIVE"),
        ("demo-user-inpost", "PRO", "ACTIVE"),
        ("demo-user-enterprise", "ENTERPRISE", "TRIALING"),
    ]
    for user_id, code, status in assignments:
        exists = db.execute(
            text("SELECT 1 FROM customer_subscriptions WHERE user_id = :u LIMIT 1"),
            {"u": user_id},
        ).scalar()
        if exists:
            continue
        prow = plan_by_code.get(code) or plan_by_code.get("BASIC")
        if not prow:
            continue
        sid = str(uuid.uuid4())
        period_end = now + timedelta(days=30)
        trial_end = (now + timedelta(days=14)) if status == "TRIALING" else None
        db.execute(
            text(
                """
                INSERT INTO customer_subscriptions (
                    id, user_id, plan_type, status, monthly_fee_cents,
                    free_shipping, priority_shelf, exclusive_deals,
                    billing_cycle, cancel_at_period_end,
                    trial_start, trial_end, current_period_start, current_period_end,
                    next_billing_at, started_at, created_at, updated_at, partner_code
                ) VALUES (
                    :id, :user_id, :plan_type, :status, :fee,
                    :free_ship, :priority, :deals,
                    'MONTHLY', FALSE,
                    :trial_start, :trial_end, :period_start, :period_end,
                    :next_billing, :started, :now, :now, :partner
                )
                """
            ),
            {
                "id": sid,
                "user_id": user_id,
                "plan_type": code,
                "status": status,
                "fee": int(prow["monthly_fee_cents"]),
                "free_ship": bool(prow.get("free_shipping")),
                "priority": bool(prow.get("priority_shelf")),
                "deals": bool(prow.get("exclusive_deals")),
                "trial_start": now if trial_end else None,
                "trial_end": trial_end,
                "period_start": now,
                "period_end": period_end,
                "next_billing": period_end,
                "started": now,
                "now": now,
                "partner": user_id.split("-")[-1],
            },
        )
        usage_month = now.date().replace(day=1)
        for benefit, limit in (("FREE_SHIPPING", 4), ("PRIORITY_SHELF", 10)):
            dup = db.execute(
                text(
                    """
                    SELECT 1 FROM subscription_benefits_usage
                    WHERE subscription_id = :sid AND usage_month = :um AND benefit_type = :bt LIMIT 1
                    """
                ),
                {"sid": sid, "um": usage_month, "bt": benefit},
            ).scalar()
            if dup:
                continue
            db.execute(
                text(
                    """
                    INSERT INTO subscription_benefits_usage (
                        subscription_id, usage_month, benefit_type, usage_count, usage_limit,
                        created_at, updated_at
                    ) VALUES (:sid, :um, :bt, 0, :lim, :now, :now)
                    """
                ),
                {"sid": sid, "um": usage_month, "bt": benefit, "lim": limit, "now": now},
            )
        created_subs += 1

    partners = (
        "magalu",
        "mercado_livre",
        "inpost",
        "dhl",
        "dpd",
        "amazon",
        "correios",
        "ctt",
        "worten",
        "el_corte_ingles",
    )
    for pcode in partners:
        exists = db.execute(
            text("SELECT 1 FROM subscription_webhook_endpoints WHERE partner_code = :p LIMIT 1"),
            {"p": pcode},
        ).scalar()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_webhook_endpoints (
                    id, partner_code, url, secret_hash, events_json, active, created_at, updated_at
                ) VALUES (
                    :id, :p, :url, :hash, :events, TRUE, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "p": pcode,
                "url": f"https://hooks.{pcode}.example.com/subscriptions",
                "hash": "seed-placeholder-hash",
                "events": json.dumps(
                    [
                        "subscription.created",
                        "subscription.renewed",
                        "subscription.cancelled",
                        "subscription.past_due",
                    ]
                ),
                "now": now,
            },
        )
        created_wh += 1

    for pcode in ("magalu", "enterprise"):
        exists = db.execute(
            text(
                "SELECT 1 FROM subscription_api_keys WHERE partner_code = :p AND revoked_at IS NULL LIMIT 1"
            ),
            {"p": pcode},
        ).scalar()
        if exists:
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_api_keys (
                    id, partner_code, key_prefix, key_hash, label, scopes_json, created_at
                ) VALUES (:id, :p, :prefix, :hash, :label, :scopes, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "p": pcode,
                "prefix": f"sub_{pcode[:4]}",
                "hash": "seed-placeholder-key-hash",
                "label": "seed",
                "scopes": json.dumps(["subscriptions:read", "subscriptions:write", "subscriptions:webhook"]),
                "now": now,
            },
        )
        created_keys += 1

    sync_stats = sync_full_ecosystem(db)
    created_programs = sync_stats.get("partner_programs", 0)
    created_ent = sync_stats.get("entitlements", 0)

    created_events = 0
    created_invoices = 0
    created_dunning = 0
    created_deliveries = 0
    sub_rows = db.execute(text("SELECT id, plan_type, monthly_fee_cents, user_id FROM customer_subscriptions")).mappings().all()
    for sub in sub_rows:
        sid = str(sub["id"])
        for et in ("subscription.created", "subscription.activated"):
            if db.execute(
                text("SELECT 1 FROM subscription_events WHERE subscription_id = :s AND event_type = :e LIMIT 1"),
                {"s": sid, "e": et},
            ).scalar():
                continue
            db.execute(
                text(
                    """
                    INSERT INTO subscription_events (id, subscription_id, event_type, payload_json, created_at)
                    VALUES (:id, :sid, :et, :payload, :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "et": et,
                    "payload": json.dumps({"user_id": sub.get("user_id"), "plan": sub.get("plan_type")}),
                    "now": now,
                },
            )
            created_events += 1
        if not db.execute(
            text("SELECT 1 FROM subscription_invoices WHERE subscription_id = :s LIMIT 1"),
            {"s": sid},
        ).scalar():
            iid = str(uuid.uuid4())
            db.execute(
                text(
                    """
                    INSERT INTO subscription_invoices (
                        id, subscription_id, period_start, period_end, amount_cents, status, paid_at,
                        created_at, updated_at
                    ) VALUES (:id, :sid, :ps, :pe, :amt, 'PAID', :now, :now, :now)
                    """
                ),
                {
                    "id": iid,
                    "sid": sid,
                    "ps": now - timedelta(days=30),
                    "pe": now,
                    "amt": int(sub["monthly_fee_cents"]),
                    "now": now,
                },
            )
            created_invoices += 1
        usage_month = now.date().replace(day=1)
        if not db.execute(
            text("SELECT 1 FROM subscription_usage WHERE subscription_id = :s AND usage_month = :m LIMIT 1"),
            {"s": sid, "m": usage_month},
        ).scalar():
            db.execute(
                text(
                    """
                    INSERT INTO subscription_usage (
                        subscription_id, usage_month, orders_count, free_shipping_used, savings_cents
                    ) VALUES (:sid, :m, :orders, :free, :savings)
                    """
                ),
                {"sid": sid, "m": usage_month, "orders": 3, "free": 1, "savings": 1200},
            )

    past_due_sub = db.execute(
        text("SELECT id, monthly_fee_cents FROM customer_subscriptions WHERE user_id = 'demo-user-inpost' LIMIT 1")
    ).mappings().first()
    if past_due_sub and not db.execute(
        text("SELECT 1 FROM subscription_dunning_cases WHERE subscription_id = :s LIMIT 1"),
        {"s": past_due_sub["id"]},
    ).scalar():
        db.execute(
            text("UPDATE customer_subscriptions SET status = 'PAST_DUE', updated_at = :now WHERE id = :id"),
            {"id": past_due_sub["id"], "now": now},
        )
        db.execute(
            text(
                """
                INSERT INTO subscription_dunning_cases (
                    id, subscription_id, stage, status, amount_due_cents, opened_at, created_at, updated_at
                ) VALUES (:id, :sid, 'D+7', 'OPEN', :amt, :now, :now, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "sid": past_due_sub["id"],
                "amt": int(past_due_sub["monthly_fee_cents"]),
                "now": now,
            },
        )
        created_dunning += 1

    wh = db.execute(
        text("SELECT id, partner_code FROM subscription_webhook_endpoints WHERE partner_code = 'magalu' LIMIT 1")
    ).mappings().first()
    if wh and not db.execute(
        text("SELECT 1 FROM subscription_webhook_deliveries WHERE endpoint_id = :e LIMIT 1"),
        {"e": wh["id"]},
    ).scalar():
        db.execute(
            text(
                """
                INSERT INTO subscription_webhook_deliveries (
                    id, endpoint_id, event_type, http_status, attempt_no, payload_json, delivered_at
                ) VALUES (:id, :eid, 'subscription.renewed', 200, 1, '{}', :now)
                """
            ),
            {"id": str(uuid.uuid4()), "eid": wh["id"], "now": now},
        )
        created_deliveries += 1

    premium_stats = seed_subscriptions_premium(db)
    world_stats = seed_subscriptions_world(db)
    efficiency_stats = seed_subscriptions_efficiency(db)

    db.commit()
    return {
        "plans": created_plans,
        "subscriptions": created_subs,
        "webhooks": created_wh,
        "api_keys": created_keys,
        "partner_programs": created_programs,
        "entitlements": created_ent,
        "events": created_events,
        "invoices": created_invoices,
        "dunning_cases": created_dunning,
        "webhook_deliveries": created_deliveries,
        "global_sync": sync_stats,
        "premium": premium_stats,
        "world": world_stats,
        "efficiency": efficiency_stats,
    }
