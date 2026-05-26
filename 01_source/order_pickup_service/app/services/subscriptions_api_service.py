"""Lógica compartilhada: API pública B2C e integrações de parceiros."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.subscriptions_api import (
    PublicBenefitFlagsOut,
    PublicBenefitUsageOut,
    PublicEntitlementItemOut,
    PublicInvoiceItemOut,
    PublicLoyaltyOut,
    PublicPlanSummaryOut,
    PublicPromoRedemptionOut,
    PublicSubscriptionOut,
    PublicUsageMonthOut,
)
from app.services import subscription_promo_service as promo_svc


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def parse_json(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def benefit_flags_from_row(row: dict[str, Any]) -> PublicBenefitFlagsOut:
    return PublicBenefitFlagsOut(
        free_shipping=bool(row.get("free_shipping")),
        priority_shelf=bool(row.get("priority_shelf")),
        exclusive_deals=bool(row.get("exclusive_deals")),
    )


def fetch_active_subscription(db: Session, user_id: str) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT id, user_id, plan_type, status, monthly_fee_cents,
                   free_shipping, priority_shelf, exclusive_deals,
                   billing_cycle, cancel_at_period_end,
                   trial_start, trial_end, current_period_start, current_period_end,
                   next_billing_at, partner_code, created_at, updated_at
            FROM customer_subscriptions
            WHERE user_id = :uid AND status IN ('ACTIVE', 'TRIALING', 'PAST_DUE')
            ORDER BY created_at DESC LIMIT 1
            """
        ),
        {"uid": user_id},
    ).mappings().first()
    return dict(row) if row else None


def subscription_to_public(row: dict[str, Any]) -> PublicSubscriptionOut:
    return PublicSubscriptionOut(
        id=str(row["id"]),
        plan_type=str(row["plan_type"]),
        status=str(row["status"]),
        monthly_fee_cents=int(row["monthly_fee_cents"]),
        billing_cycle=str(row.get("billing_cycle") or "MONTHLY"),
        benefits=benefit_flags_from_row(row),
        cancel_at_period_end=bool(row.get("cancel_at_period_end")),
        trial_start=to_iso(row.get("trial_start")),
        trial_end=to_iso(row.get("trial_end")),
        current_period_start=to_iso(row.get("current_period_start")),
        current_period_end=to_iso(row.get("current_period_end")),
        next_billing_at=to_iso(row.get("next_billing_at")),
        partner_code=(str(row["partner_code"]) if row.get("partner_code") else None),
    )


def fetch_plan_summary(db: Session, plan_code: str) -> PublicPlanSummaryOut | None:
    row = db.execute(
        text(
            """
            SELECT code, name, monthly_fee_cents, yearly_fee_cents,
                   free_shipping, priority_shelf, exclusive_deals,
                   max_orders_per_month, max_discount_pct
            FROM subscription_plans
            WHERE code = :code AND is_active = TRUE LIMIT 1
            """
        ),
        {"code": plan_code.strip().upper()},
    ).mappings().first()
    if not row:
        return None
    return PublicPlanSummaryOut(
        code=str(row["code"]),
        name=str(row["name"]),
        monthly_fee_cents=int(row["monthly_fee_cents"]),
        yearly_fee_cents=(int(row["yearly_fee_cents"]) if row.get("yearly_fee_cents") is not None else None),
        benefits=benefit_flags_from_row(row),
        max_orders_per_month=(int(row["max_orders_per_month"]) if row.get("max_orders_per_month") is not None else None),
        max_discount_pct=(float(row["max_discount_pct"]) if row.get("max_discount_pct") is not None else None),
    )


def list_public_plans(db: Session) -> list[PublicPlanSummaryOut]:
    rows = db.execute(
        text(
            """
            SELECT code, name, monthly_fee_cents, yearly_fee_cents,
                   free_shipping, priority_shelf, exclusive_deals,
                   max_orders_per_month, max_discount_pct
            FROM subscription_plans
            WHERE is_active = TRUE
            ORDER BY monthly_fee_cents ASC
            """
        )
    ).mappings().all()
    return [
        PublicPlanSummaryOut(
            code=str(r["code"]),
            name=str(r["name"]),
            monthly_fee_cents=int(r["monthly_fee_cents"]),
            yearly_fee_cents=(int(r["yearly_fee_cents"]) if r.get("yearly_fee_cents") is not None else None),
            benefits=benefit_flags_from_row(r),
            max_orders_per_month=(int(r["max_orders_per_month"]) if r.get("max_orders_per_month") is not None else None),
            max_discount_pct=(float(r["max_discount_pct"]) if r.get("max_discount_pct") is not None else None),
        )
        for r in rows
    ]


def fetch_usage_for_subscription(db: Session, subscription_id: str) -> PublicUsageMonthOut | None:
    row = db.execute(
        text(
            """
            SELECT usage_month, orders_count, free_shipping_used, savings_cents
            FROM subscription_usage
            WHERE subscription_id = :sid
            ORDER BY usage_month DESC LIMIT 1
            """
        ),
        {"sid": subscription_id},
    ).mappings().first()
    if not row:
        return None
    return PublicUsageMonthOut(
        usage_month=str(row["usage_month"]) if row.get("usage_month") else None,
        orders_count=int(row.get("orders_count") or 0),
        free_shipping_used=int(row.get("free_shipping_used") or 0),
        savings_cents=int(row.get("savings_cents") or 0),
    )


def fetch_benefits_usage(db: Session, subscription_id: str) -> list[PublicBenefitUsageOut]:
    rows = db.execute(
        text(
            """
            SELECT benefit_type, usage_count, usage_limit
            FROM subscription_benefits_usage
            WHERE subscription_id = :sid
            ORDER BY usage_month DESC, benefit_type
            LIMIT 20
            """
        ),
        {"sid": subscription_id},
    ).mappings().all()
    seen: set[str] = set()
    items: list[PublicBenefitUsageOut] = []
    for r in rows:
        bt = str(r["benefit_type"])
        if bt in seen:
            continue
        seen.add(bt)
        items.append(
            PublicBenefitUsageOut(
                benefit_type=bt,
                usage_count=int(r.get("usage_count") or 0),
                usage_limit=(int(r["usage_limit"]) if r.get("usage_limit") is not None else None),
            )
        )
    return items


def fetch_loyalty_balance(db: Session, user_id: str) -> PublicLoyaltyOut:
    row = db.execute(
        text(
            """
            SELECT balance_after FROM subscription_loyalty_ledger
            WHERE user_id = :u ORDER BY created_at DESC LIMIT 1
            """
        ),
        {"u": user_id},
    ).mappings().first()
    return PublicLoyaltyOut(balance=int(row["balance_after"]) if row else 0)


def count_entitlements(db: Session, plan_code: str) -> int:
    return int(
        db.execute(
            text(
                "SELECT COUNT(*) FROM subscription_plan_entitlements WHERE plan_code = :c AND enabled = TRUE"
            ),
            {"c": plan_code.strip().upper()},
        ).scalar()
        or 0
    )


def list_entitlements_for_plan(db: Session, plan_code: str, limit: int = 50) -> list[PublicEntitlementItemOut]:
    rows = db.execute(
        text(
            """
            SELECT player_code, player_name, player_type, priority_level
            FROM subscription_plan_entitlements
            WHERE plan_code = :c AND enabled = TRUE
            ORDER BY priority_level DESC, player_name
            LIMIT :lim
            """
        ),
        {"c": plan_code.strip().upper(), "lim": limit},
    ).mappings().all()
    return [
        PublicEntitlementItemOut(
            player_code=str(r["player_code"]),
            player_name=str(r["player_name"]),
            player_type=(str(r["player_type"]) if r.get("player_type") else None),
            priority_level=int(r.get("priority_level") or 0),
        )
        for r in rows
    ]


def list_invoices_for_subscription(db: Session, subscription_id: str, limit: int = 12) -> list[PublicInvoiceItemOut]:
    rows = db.execute(
        text(
            """
            SELECT id, period_start, period_end, amount_cents, currency, status, paid_at
            FROM subscription_invoices
            WHERE subscription_id = :sid
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        {"sid": subscription_id, "lim": limit},
    ).mappings().all()
    return [
        PublicInvoiceItemOut(
            id=str(r["id"]),
            period_start=to_iso(r.get("period_start")),
            period_end=to_iso(r.get("period_end")),
            amount_cents=int(r["amount_cents"]),
            currency=str(r.get("currency") or "BRL"),
            status=str(r["status"]),
            paid_at=to_iso(r.get("paid_at")),
        )
        for r in rows
    ]


_BENEFIT_COLUMN = {
    "FREE_SHIPPING": "free_shipping",
    "PRIORITY_SHELF": "priority_shelf",
    "EXCLUSIVE_DEAL": "exclusive_deals",
}


def check_benefit_eligibility(
    db: Session,
    user_id: str,
    benefit_type: str,
    *,
    allow_past_due: bool = False,
) -> dict[str, Any]:
    statuses = ("ACTIVE", "TRIALING", "PAST_DUE") if allow_past_due else ("ACTIVE", "TRIALING")
    status_list = ", ".join(f"'{s}'" for s in statuses)
    col = _BENEFIT_COLUMN.get(benefit_type.upper())
    if not col:
        return {"eligible": False, "reason": "INVALID_BENEFIT_TYPE"}

    row = db.execute(
        text(
            f"""
            SELECT cs.id, cs.plan_type, cs.status, cs.{col} AS flag_ok
            FROM customer_subscriptions cs
            WHERE cs.user_id = :uid AND cs.status IN ({status_list})
            ORDER BY cs.created_at DESC LIMIT 1
            """
        ),
        {"uid": user_id},
    ).mappings().first()

    if not row:
        return {"eligible": False, "reason": "NO_ACTIVE_SUBSCRIPTION"}

    if not bool(row.get("flag_ok")):
        return {
            "eligible": False,
            "reason": "PLAN_DOES_NOT_INCLUDE_BENEFIT",
            "subscription_id": str(row["id"]),
            "plan_type": str(row["plan_type"]),
        }

    usage = db.execute(
        text(
            """
            SELECT usage_count, usage_limit FROM subscription_benefits_usage
            WHERE subscription_id = :sid AND benefit_type = :bt
            ORDER BY usage_month DESC LIMIT 1
            """
        ),
        {"sid": row["id"], "bt": benefit_type},
    ).mappings().first()

    usage_count = int(usage["usage_count"]) if usage else 0
    usage_limit = int(usage["usage_limit"]) if usage and usage.get("usage_limit") is not None else None

    if usage_limit is not None and usage_count >= usage_limit:
        return {
            "eligible": False,
            "reason": "USAGE_LIMIT_REACHED",
            "subscription_id": str(row["id"]),
            "plan_type": str(row["plan_type"]),
            "usage_count": usage_count,
            "usage_limit": usage_limit,
        }

    return {
        "eligible": True,
        "reason": None,
        "subscription_id": str(row["id"]),
        "plan_type": str(row["plan_type"]),
        "usage_count": usage_count,
        "usage_limit": usage_limit,
    }


def resolve_plan_row(db: Session, plan_code: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT code, monthly_fee_cents, free_shipping, priority_shelf, exclusive_deals
            FROM subscription_plans WHERE code = :code AND is_active = TRUE LIMIT 1
            """
        ),
        {"code": plan_code.strip().upper()},
    ).mappings().first()
    if not row:
        raise ValueError(f"PLAN_NOT_FOUND:{plan_code}")
    return dict(row)


def create_subscription_for_user(
    db: Session,
    *,
    user_id: str,
    plan_code: str,
    billing_cycle: str = "MONTHLY",
    partner_code: str | None = None,
    trial_days: int | None = None,
    promo_code: str | None = None,
) -> tuple[dict[str, Any], PublicPromoRedemptionOut | None]:
    if fetch_active_subscription(db, user_id):
        raise ValueError("ALREADY_SUBSCRIBED")

    plan = resolve_plan_row(db, plan_code)
    now = utc_now()
    bonus_months = 0
    monthly_fee = int(plan["monthly_fee_cents"])
    if promo_code and promo_code.strip():
        preview = promo_svc.validate_promo(
            db, code=promo_code.strip(), user_id=user_id, plan_code=str(plan["code"])
        )
        if not preview.get("valid"):
            raise ValueError(f"PROMO_INVALID:{preview.get('reason', 'UNKNOWN')}")
        monthly_fee = max(0, monthly_fee - int(preview["discount_cents"]))
        bonus_months = int(preview.get("bonus_months") or 0)

    period_end = now + timedelta(days=30 * (1 + bonus_months))
    status = "ACTIVE"
    trial_start = None
    trial_end = None
    if trial_days:
        trial_start = now
        trial_end = now + timedelta(days=int(trial_days))
        status = "TRIALING"

    sid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO customer_subscriptions (
                id, user_id, plan_type, status, monthly_fee_cents,
                free_shipping, priority_shelf, exclusive_deals,
                billing_cycle, cancel_at_period_end,
                trial_start, trial_end, current_period_start, current_period_end,
                next_billing_at, started_at, partner_code,
                created_at, updated_at
            ) VALUES (
                :id, :user_id, :plan_type, :status, :fee,
                :free_ship, :priority, :deals,
                :billing_cycle, FALSE,
                :trial_start, :trial_end, :period_start, :period_end,
                :next_billing, :started, :partner,
                :now, :now
            )
            """
        ),
        {
            "id": sid,
            "user_id": user_id,
            "plan_type": plan["code"],
            "status": status,
            "fee": monthly_fee,
            "free_ship": bool(plan["free_shipping"]),
            "priority": bool(plan["priority_shelf"]),
            "deals": bool(plan["exclusive_deals"]),
            "billing_cycle": billing_cycle.strip().upper(),
            "trial_start": trial_start,
            "trial_end": trial_end,
            "period_start": now,
            "period_end": period_end,
            "next_billing": period_end,
            "started": now,
            "partner": partner_code,
            "now": now,
        },
    )
    db.execute(
        text(
            """
            INSERT INTO subscription_events (id, subscription_id, event_type, actor_id, payload_json, created_at)
            VALUES (:id, :sid, 'subscription.created', :uid, :payload, :now)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "sid": sid,
            "uid": user_id,
            "payload": json.dumps(
                {
                    "source": "public_api",
                    "plan_code": plan["code"],
                    "promo_code": promo_code.strip().upper() if promo_code and promo_code.strip() else None,
                }
            ),
            "now": now,
        },
    )
    promo_applied: PublicPromoRedemptionOut | None = None
    if promo_code and promo_code.strip():
        redeemed = promo_svc.redeem_promo(
            db,
            code=promo_code.strip(),
            user_id=user_id,
            plan_code=str(plan["code"]),
            subscription_id=sid,
        )
        promo_applied = PublicPromoRedemptionOut(
            promo_code=redeemed["promo_code"],
            discount_cents=int(redeemed["discount_cents"]),
            discount_pct=float(redeemed["discount_pct"]),
            bonus_months=int(redeemed["bonus_months"]),
        )
    db.commit()
    sub = fetch_active_subscription(db, user_id)
    assert sub is not None
    return sub, promo_applied


def cancel_subscription_for_user(
    db: Session,
    user_id: str,
    *,
    immediate: bool = False,
) -> str | None:
    sub = fetch_active_subscription(db, user_id)
    if not sub:
        return None
    now = utc_now()
    sid = str(sub["id"])
    if immediate:
        db.execute(
            text(
                """
                UPDATE customer_subscriptions
                SET status = 'CANCELLED', cancelled_at = :now, cancel_at_period_end = FALSE, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": sid, "now": now},
        )
        event_type = "subscription.cancelled"
    else:
        db.execute(
            text(
                """
                UPDATE customer_subscriptions
                SET cancel_at_period_end = TRUE, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": sid, "now": now},
        )
        event_type = "subscription.cancel_scheduled"
    db.execute(
        text(
            """
            INSERT INTO subscription_events (id, subscription_id, event_type, actor_id, payload_json, created_at)
            VALUES (:id, :sid, :etype, :uid, :payload, :now)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "sid": sid,
            "etype": event_type,
            "uid": user_id,
            "payload": json.dumps({"immediate": immediate}),
            "now": now,
        },
    )
    db.commit()
    return sid
