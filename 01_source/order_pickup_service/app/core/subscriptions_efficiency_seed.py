"""Seed: promo codes, automações, medidores, family seats, histórico de mudança de plano."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def seed_subscriptions_efficiency(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    stats = {
        "promo_codes": 0,
        "automation_rules": 0,
        "usage_meters": 0,
        "family_members": 0,
        "plan_changes": 0,
    }

    promos = [
        {
            "code": "WELCOME20",
            "desc": "Boas-vindas −20%",
            "pct": 20,
            "cents": 0,
            "bonus": 0,
            "plans": ["BASIC", "PREMIUM"],
            "partner": None,
        },
        {
            "code": "MAGALU15",
            "desc": "Parceiro Magalu −15%",
            "pct": 15,
            "cents": 0,
            "bonus": 0,
            "plans": ["PREMIUM", "PRO"],
            "partner": "magalu",
        },
        {
            "code": "UPGRADE50",
            "desc": "R$5 off upgrade PRO/ENTERPRISE",
            "pct": 0,
            "cents": 500,
            "bonus": 1,
            "plans": ["PRO", "ENTERPRISE"],
            "partner": None,
        },
    ]
    for p in promos:
        if db.execute(
            text("SELECT 1 FROM subscription_promo_codes WHERE code = :c LIMIT 1"), {"c": p["code"]}
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_promo_codes (
                    id, code, description, discount_pct, discount_cents, bonus_months,
                    eligible_plans_json, max_redemptions, valid_from, valid_until, partner_code,
                    active, created_at, updated_at
                ) VALUES (
                    :id, :code, :desc, :pct, :cents, :bonus, :plans, 1000,
                    :vfrom, :vuntil, :partner, TRUE, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": p["code"],
                "desc": p["desc"],
                "pct": p["pct"],
                "cents": p["cents"],
                "bonus": p["bonus"],
                "plans": json.dumps(p["plans"]),
                "vfrom": now - timedelta(days=30),
                "vuntil": now + timedelta(days=365),
                "partner": p["partner"],
                "now": now,
            },
        )
        stats["promo_codes"] += 1

    rules = [
        ("PAST_DUE_RETENTION", "Oferta ao ficar PAST_DUE", "subscription.past_due", "ISSUE_RETENTION_OFFER", {"discount_pct": 15}),
        ("CHURN_ALERT_NOTIFY", "Alerta churn HIGH", "subscription.churn_high", "WEBHOOK_NOTIFY", {"template": "churn_high"}),
        ("RENEWAL_REMINDER", "Lembrete renovação", "subscription.renewal_due", "SEND_EVENT", {"event": "renewal.reminder"}),
    ]
    for code, name, trigger, action, cfg in rules:
        if db.execute(
            text("SELECT 1 FROM subscription_automation_rules WHERE rule_code = :c LIMIT 1"), {"c": code}
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_automation_rules (
                    id, rule_code, name, trigger_event, action_type, config_json,
                    priority, active, created_at, updated_at
                ) VALUES (:id, :code, :name, :trig, :act, :cfg, 100, TRUE, :now, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": code,
                "name": name,
                "trig": trigger,
                "act": action,
                "cfg": json.dumps(cfg),
                "now": now,
            },
        )
        stats["automation_rules"] += 1

    subs = db.execute(
        text("SELECT id, user_id, plan_type FROM customer_subscriptions WHERE status IN ('ACTIVE','TRIALING') LIMIT 5")
    ).mappings().all()
    period = now.strftime("%Y-%m")
    for sub in subs:
        sid = str(sub["id"])
        if not db.execute(
            text(
                """
                SELECT 1 FROM subscription_usage_meters
                WHERE subscription_id = :s AND meter_code = 'ORDERS' AND period_month = :pm LIMIT 1
                """
            ),
            {"s": sid, "pm": period},
        ).scalar():
            qty = 8 if str(sub["plan_type"]) == "BASIC" else 22
            included = 10 if str(sub["plan_type"]) == "BASIC" else 50
            overage = max(0, qty - included) * 99
            db.execute(
                text(
                    """
                    INSERT INTO subscription_usage_meters (
                        id, subscription_id, meter_code, period_month, quantity,
                        included_quantity, overage_cents, recorded_at
                    ) VALUES (:id, :sid, 'ORDERS', :pm, :qty, :inc, :ov, :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "pm": period,
                    "qty": qty,
                    "inc": included,
                    "ov": overage,
                    "now": now,
                },
            )
            stats["usage_meters"] += 1

        if str(sub["plan_type"]) in ("PREMIUM", "PRO", "ENTERPRISE"):
            uid = str(sub.get("user_id") or "")
            member_id = f"{uid}-family-1" if uid else str(uuid.uuid4())
            if not db.execute(
                text(
                    "SELECT 1 FROM subscription_family_members WHERE subscription_id = :s LIMIT 1"
                ),
                {"s": sid},
            ).scalar():
                db.execute(
                    text(
                        """
                        INSERT INTO subscription_family_members (
                            id, subscription_id, member_user_id, role, status, invited_at, joined_at
                        ) VALUES (:id, :sid, :mid, 'MEMBER', 'ACTIVE', :now, :now)
                        """
                    ),
                    {"id": str(uuid.uuid4()), "sid": sid, "mid": member_id, "now": now},
                )
                stats["family_members"] += 1

        if not db.execute(
            text("SELECT 1 FROM subscription_plan_changes WHERE subscription_id = :s LIMIT 1"), {"s": sid}
        ).scalar():
            from_plan = "BASIC" if str(sub["plan_type"]) != "BASIC" else "PREMIUM"
            to_plan = str(sub["plan_type"])
            if from_plan != to_plan:
                db.execute(
                    text(
                        """
                        INSERT INTO subscription_plan_changes (
                            id, subscription_id, from_plan_code, to_plan_code, change_type,
                            proration_cents, effective_at, actor_id, notes, created_at
                        ) VALUES (:id, :sid, :fp, :tp, 'UPGRADE', 0, :now, 'seed', 'Demo histórico', :now)
                        """
                    ),
                    {
                        "id": str(uuid.uuid4()),
                        "sid": sid,
                        "fp": from_plan,
                        "tp": to_plan,
                        "now": now,
                    },
                )
                stats["plan_changes"] += 1

    db.commit()
    return stats
