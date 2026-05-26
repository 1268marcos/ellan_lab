"""Seed de funcionalidades premium de assinaturas."""
from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session


def seed_subscriptions_premium(db: Session) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    stats = {
        "health_snapshots": 0,
        "referrals": 0,
        "gift_codes": 0,
        "loyalty": 0,
        "experiments": 0,
        "renewal_queue": 0,
        "churn_alerts": 0,
    }

    subs = db.execute(
        text("SELECT id, user_id, plan_type, status, cancel_at_period_end FROM customer_subscriptions LIMIT 20")
    ).mappings().all()

    for sub in subs:
        sid = str(sub["id"])
        uid = str(sub.get("user_id") or "")
        status = str(sub.get("status") or "")
        cancel = bool(sub.get("cancel_at_period_end"))
        if not db.execute(
            text("SELECT 1 FROM subscription_health_snapshots WHERE subscription_id = :s LIMIT 1"),
            {"s": sid},
        ).scalar():
            if status == "PAST_DUE":
                score, risk = 25, "HIGH"
            elif cancel:
                score, risk = 40, "MEDIUM"
            elif status == "TRIALING":
                score, risk = 65, "LOW"
            else:
                score, risk = 85, "LOW"
            db.execute(
                text(
                    """
                    INSERT INTO subscription_health_snapshots (
                        id, subscription_id, health_score, churn_risk, factors_json, computed_at
                    ) VALUES (:id, :sid, :score, :risk, :factors, :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "score": score,
                    "risk": risk,
                    "factors": json.dumps({"status": status, "cancel_at_period_end": cancel}),
                    "now": now,
                },
            )
            stats["health_snapshots"] += 1

        if status == "PAST_DUE" and not db.execute(
            text("SELECT 1 FROM subscription_churn_alerts WHERE subscription_id = :s AND resolved_at IS NULL LIMIT 1"),
            {"s": sid},
        ).scalar():
            db.execute(
                text(
                    """
                    INSERT INTO subscription_churn_alerts (
                        id, subscription_id, alert_type, severity, message, created_at
                    ) VALUES (:id, :sid, 'PAYMENT_PAST_DUE', 'HIGH', :msg, :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "msg": "Assinatura em PAST_DUE — acionar dunning ou oferta de retenção.",
                    "now": now,
                },
            )
            stats["churn_alerts"] += 1

        if uid and not db.execute(
            text("SELECT 1 FROM subscription_renewal_queue WHERE subscription_id = :s AND status = 'PENDING' LIMIT 1"),
            {"s": sid},
        ).scalar():
            db.execute(
                text(
                    """
                    INSERT INTO subscription_renewal_queue (
                        id, subscription_id, scheduled_at, status, created_at
                    ) VALUES (:id, :sid, :sched, 'PENDING', :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": sid,
                    "sched": now + timedelta(days=7),
                    "now": now,
                },
            )
            stats["renewal_queue"] += 1

    if not db.execute(text("SELECT 1 FROM subscription_referrals LIMIT 1")).scalar():
        db.execute(
            text(
                """
                INSERT INTO subscription_referrals (
                    id, referrer_user_id, referral_code, reward_cents, status, created_at
                ) VALUES (:id, :uid, :code, 1000, 'ACTIVE', :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "uid": "demo-user-magalu",
                "code": "ELLAN-MAGALU",
                "now": now,
            },
        )
        stats["referrals"] += 1

    if not db.execute(text("SELECT 1 FROM subscription_gift_codes LIMIT 1")).scalar():
        db.execute(
            text(
                """
                INSERT INTO subscription_gift_codes (
                    id, gift_code, purchaser_user_id, recipient_email, plan_code, months,
                    status, expires_at, created_at
                ) VALUES (:id, :code, :uid, :email, 'PREMIUM', 3, 'ISSUED', :exp, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "code": f"GIFT-{secrets.token_hex(4).upper()}",
                "uid": "demo-user-enterprise",
                "email": "presente@example.com",
                "exp": now + timedelta(days=90),
                "now": now,
            },
        )
        stats["gift_codes"] += 1

    experiments = [
        ("PREMIUM_PRICE_TEST", "PREMIUM", "A", 1990, 50),
        ("PREMIUM_PRICE_TEST", "PREMIUM", "B", 2490, 50),
        ("PRO_ANNUAL_PUSH", "PRO", "CONTROL", 4990, 80),
        ("PRO_ANNUAL_PUSH", "PRO", "DISCOUNT_10", 4490, 20),
    ]
    for exp_code, plan, variant, fee, traffic in experiments:
        if db.execute(
            text("SELECT 1 FROM subscription_price_experiments WHERE experiment_code = :e AND variant = :v LIMIT 1"),
            {"e": exp_code, "v": variant},
        ).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_price_experiments (
                    id, experiment_code, plan_code, variant, monthly_fee_cents, traffic_pct,
                    impressions, active, created_at, updated_at
                ) VALUES (:id, :e, :plan, :v, :fee, :traffic, 100, TRUE, :now, :now)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "e": exp_code,
                "plan": plan,
                "v": variant,
                "fee": fee,
                "traffic": traffic,
                "now": now,
            },
        )
        stats["experiments"] += 1

    for uid, pts, reason in (
        ("demo-user-magalu", 120, "RENEWAL_BONUS"),
        ("demo-user-inpost", 80, "REFERRAL_PENDING"),
    ):
        if db.execute(text("SELECT 1 FROM subscription_loyalty_ledger WHERE user_id = :u LIMIT 1"), {"u": uid}).scalar():
            continue
        db.execute(
            text(
                """
                INSERT INTO subscription_loyalty_ledger (
                    id, user_id, points_delta, reason, balance_after, created_at
                ) VALUES (:id, :u, :pts, :reason, :bal, :now)
                """
            ),
            {"id": str(uuid.uuid4()), "u": uid, "pts": pts, "reason": reason, "bal": pts, "now": now},
        )
        stats["loyalty"] += 1

    db.commit()
    return stats
