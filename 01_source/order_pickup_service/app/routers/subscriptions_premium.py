"""Funcionalidades premium: health, referrals, gifts, loyalty, experiments, renewals, churn."""
from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.subscriptions_premium_seed import seed_subscriptions_premium
from app.routers.subscriptions_ops import _to_iso, _utc_now

router = APIRouter(tags=["subscriptions-premium"])


class BenefitCheckIn(BaseModel):
    user_id: str
    benefit_type: str = Field(..., pattern="^(FREE_SHIPPING|PRIORITY_SHELF|EXCLUSIVE_DEAL)$")


class ReferralCreateIn(BaseModel):
    referrer_user_id: str
    reward_cents: int = Field(default=500, ge=0)


class GiftIssueIn(BaseModel):
    purchaser_user_id: str
    plan_code: str
    months: int = Field(default=1, ge=1, le=12)
    recipient_email: str | None = None


class GiftRedeemIn(BaseModel):
    gift_code: str
    recipient_user_id: str


class LoyaltyGrantIn(BaseModel):
    user_id: str
    points_delta: int
    reason: str = "MANUAL_GRANT"
    subscription_id: str | None = None


class ExperimentIn(BaseModel):
    experiment_code: str
    plan_code: str
    variant: str
    monthly_fee_cents: int = Field(..., ge=0)
    traffic_pct: int = Field(default=50, ge=0, le=100)


def _check_benefit_sql() -> str:
    return """
        SELECT cs.id, cs.plan_type, cs.status,
               CASE :benefit
                 WHEN 'FREE_SHIPPING' THEN cs.free_shipping
                 WHEN 'PRIORITY_SHELF' THEN cs.priority_shelf
                 WHEN 'EXCLUSIVE_DEAL' THEN cs.exclusive_deals
                 ELSE FALSE
               END AS flag_ok
        FROM customer_subscriptions cs
        WHERE cs.user_id = :uid
          AND cs.status IN ('ACTIVE', 'TRIALING')
        ORDER BY cs.created_at DESC
        LIMIT 1
    """


@router.post("/premium/seed")
def premium_seed(db: Session = Depends(get_db)):
    return {"ok": True, "seeded": seed_subscriptions_premium(db)}


@router.post("/benefit-check")
def check_subscription_benefit(body: BenefitCheckIn, db: Session = Depends(get_db)):
    row = db.execute(text(_check_benefit_sql()), {"uid": body.user_id, "benefit": body.benefit_type}).mappings().first()
    if not row:
        return {"ok": True, "eligible": False, "reason": "NO_ACTIVE_SUBSCRIPTION"}
    eligible = bool(row.get("flag_ok"))
    usage = None
    if eligible and row.get("id"):
        usage = db.execute(
            text(
                """
                SELECT usage_count, usage_limit FROM subscription_benefits_usage
                WHERE subscription_id = :sid AND benefit_type = :bt
                ORDER BY usage_month DESC LIMIT 1
                """
            ),
            {"sid": row["id"], "bt": body.benefit_type},
        ).mappings().first()
        if usage and usage.get("usage_limit") is not None:
            if int(usage.get("usage_count") or 0) >= int(usage["usage_limit"]):
                eligible = False
    return {
        "ok": True,
        "eligible": eligible,
        "subscription_id": str(row["id"]) if row else None,
        "plan_type": str(row.get("plan_type")) if row else None,
        "usage": dict(usage) if usage else None,
    }


@router.get("/plans/compare-matrix")
def plans_compare_matrix(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT code, name, monthly_fee_cents, yearly_fee_cents,
                   free_shipping, priority_shelf, exclusive_deals, priority_support,
                   max_orders_per_month, max_discount_pct, features_json
            FROM subscription_plans WHERE is_active = TRUE ORDER BY monthly_fee_cents
            """
        )
    ).mappings().all()
    matrix = []
    for r in rows:
        ent_count = db.execute(
            text("SELECT COUNT(*) FROM subscription_plan_entitlements WHERE plan_code = :c AND enabled = TRUE"),
            {"c": r["code"]},
        ).scalar()
        matrix.append(
            {
                "code": r["code"],
                "name": r["name"],
                "monthly_fee_cents": int(r["monthly_fee_cents"]),
                "yearly_fee_cents": int(r["yearly_fee_cents"]) if r.get("yearly_fee_cents") else None,
                "benefits": {
                    "free_shipping": bool(r["free_shipping"]),
                    "priority_shelf": bool(r["priority_shelf"]),
                    "exclusive_deals": bool(r["exclusive_deals"]),
                    "priority_support": bool(r["priority_support"]),
                },
                "max_orders_per_month": r.get("max_orders_per_month"),
                "max_discount_pct": float(r["max_discount_pct"]) if r.get("max_discount_pct") else None,
                "entitled_players": int(ent_count or 0),
            }
        )
    return {"ok": True, "plans": matrix}


@router.get("/health/summary")
def health_summary(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT churn_risk, COUNT(*) AS cnt, AVG(health_score) AS avg_score
            FROM subscription_health_snapshots h
            WHERE h.computed_at = (
                SELECT MAX(h2.computed_at) FROM subscription_health_snapshots h2
                WHERE h2.subscription_id = h.subscription_id
            )
            GROUP BY churn_risk
            """
        )
    ).mappings().all()
    return {"ok": True, "by_risk": [dict(r) for r in rows]}


@router.post("/health/compute-all")
def compute_all_health(db: Session = Depends(get_db)):
    subs = db.execute(text("SELECT id, user_id, status, cancel_at_period_end FROM customer_subscriptions")).mappings().all()
    now = _utc_now()
    computed = 0
    for sub in subs:
        status = str(sub.get("status") or "")
        cancel = bool(sub.get("cancel_at_period_end"))
        if status == "PAST_DUE":
            score, risk = 25, "HIGH"
        elif status == "CANCELLED":
            score, risk = 10, "CRITICAL"
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
                "sid": sub["id"],
                "score": score,
                "risk": risk,
                "factors": json.dumps({"status": status}),
                "now": now,
            },
        )
        computed += 1
    db.commit()
    return {"ok": True, "computed": computed}


@router.get("/health/at-risk")
def list_at_risk_subscriptions(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT h.subscription_id, h.health_score, h.churn_risk, h.computed_at,
                   cs.user_id, cs.plan_type, cs.status
            FROM subscription_health_snapshots h
            JOIN customer_subscriptions cs ON cs.id = h.subscription_id
            WHERE h.churn_risk IN ('MEDIUM', 'HIGH', 'CRITICAL')
            ORDER BY h.health_score ASC, h.computed_at DESC
            LIMIT :lim
            """
        ),
        {"lim": limit},
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.get("/referrals")
def list_referrals(db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            "SELECT id, referrer_user_id, referred_user_id, referral_code, reward_cents, status, created_at FROM subscription_referrals ORDER BY created_at DESC LIMIT 200"
        )
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/referrals")
def create_referral(body: ReferralCreateIn, db: Session = Depends(get_db)):
    code = f"ELLAN-{secrets.token_hex(3).upper()}"
    rid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_referrals (id, referrer_user_id, referral_code, reward_cents, status, created_at)
            VALUES (:id, :uid, :code, :reward, 'ACTIVE', :now)
            """
        ),
        {"id": rid, "uid": body.referrer_user_id, "code": code, "reward": body.reward_cents, "now": now},
    )
    db.commit()
    return {"ok": True, "id": rid, "referral_code": code}


@router.get("/gifts")
def list_gift_codes(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("status = :st")
        params["st"] = status.upper()
    rows = db.execute(
        text(f"SELECT * FROM subscription_gift_codes WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT 100"),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/gifts/issue")
def issue_gift(body: GiftIssueIn, db: Session = Depends(get_db)):
    gid = str(uuid.uuid4())
    code = f"GIFT-{secrets.token_hex(4).upper()}"
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_gift_codes (
                id, gift_code, purchaser_user_id, recipient_email, plan_code, months,
                status, expires_at, created_at
            ) VALUES (:id, :code, :uid, :email, :plan, :months, 'ISSUED', :exp, :now)
            """
        ),
        {
            "id": gid,
            "code": code,
            "uid": body.purchaser_user_id,
            "email": body.recipient_email,
            "plan": body.plan_code.upper(),
            "months": body.months,
            "exp": now + timedelta(days=365),
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "gift_code": code, "id": gid}


@router.post("/gifts/redeem")
def redeem_gift(body: GiftRedeemIn, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT * FROM subscription_gift_codes WHERE gift_code = :c AND status = 'ISSUED' LIMIT 1"),
        {"c": body.gift_code.strip().upper()},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "GIFT_NOT_FOUND", "message": body.gift_code})
    now = _utc_now()
    db.execute(
        text(
            """
            UPDATE subscription_gift_codes
            SET status = 'REDEEMED', redeemed_by_user_id = :uid, redeemed_at = :now
            WHERE id = :id
            """
        ),
        {"id": row["id"], "uid": body.recipient_user_id, "now": now},
    )
    db.commit()
    return {"ok": True, "plan_code": row["plan_code"], "months": row["months"]}


@router.get("/loyalty/{user_id}")
def loyalty_balance(user_id: str, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT balance_after FROM subscription_loyalty_ledger
            WHERE user_id = :u ORDER BY created_at DESC LIMIT 1
            """
        ),
        {"u": user_id},
    ).mappings().first()
    history = db.execute(
        text(
            "SELECT id, points_delta, reason, balance_after, created_at FROM subscription_loyalty_ledger WHERE user_id = :u ORDER BY created_at DESC LIMIT 50"
        ),
        {"u": user_id},
    ).mappings().all()
    return {
        "user_id": user_id,
        "balance": int(row["balance_after"]) if row else 0,
        "history": [dict(h) for h in history],
    }


@router.post("/loyalty/grant")
def grant_loyalty(body: LoyaltyGrantIn, db: Session = Depends(get_db)):
    prev = db.execute(
        text("SELECT balance_after FROM subscription_loyalty_ledger WHERE user_id = :u ORDER BY created_at DESC LIMIT 1"),
        {"u": body.user_id},
    ).scalar()
    balance = int(prev or 0) + body.points_delta
    lid = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO subscription_loyalty_ledger (
                id, user_id, subscription_id, points_delta, reason, balance_after, created_at
            ) VALUES (:id, :u, :sid, :pts, :reason, :bal, :now)
            """
        ),
        {
            "id": lid,
            "u": body.user_id,
            "sid": body.subscription_id,
            "pts": body.points_delta,
            "reason": body.reason,
            "bal": balance,
            "now": _utc_now(),
        },
    )
    db.commit()
    return {"ok": True, "balance_after": balance}


@router.get("/experiments")
def list_experiments(active_only: bool = Query(True), db: Session = Depends(get_db)):
    clauses = ["1=1"]
    if active_only:
        clauses.append("active = TRUE")
    rows = db.execute(
        text(f"SELECT * FROM subscription_price_experiments WHERE {' AND '.join(clauses)} ORDER BY experiment_code, variant")
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/experiments")
def create_experiment(body: ExperimentIn, db: Session = Depends(get_db)):
    eid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_price_experiments (
                id, experiment_code, plan_code, variant, monthly_fee_cents, traffic_pct,
                active, created_at, updated_at
            ) VALUES (:id, :code, :plan, :v, :fee, :traffic, TRUE, :now, :now)
            """
        ),
        {
            "id": eid,
            "code": body.experiment_code,
            "plan": body.plan_code.upper(),
            "v": body.variant,
            "fee": body.monthly_fee_cents,
            "traffic": body.traffic_pct,
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": eid}


@router.get("/renewals/queue")
def list_renewal_queue(status: Optional[str] = Query("PENDING"), db: Session = Depends(get_db)):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("status = :st")
        params["st"] = status.upper()
    rows = db.execute(
        text(
            f"""
            SELECT q.*, cs.user_id, cs.plan_type
            FROM subscription_renewal_queue q
            JOIN customer_subscriptions cs ON cs.id = q.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY q.scheduled_at
            LIMIT 200
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/renewals/run-due")
def run_due_renewals(db: Session = Depends(get_db)):
    """Processa renovações agendadas vencidas (job OPS manual)."""
    now = _utc_now()
    due = db.execute(
        text(
            """
            SELECT id, subscription_id FROM subscription_renewal_queue
            WHERE status = 'PENDING' AND scheduled_at <= :now
            LIMIT 50
            """
        ),
        {"now": now},
    ).mappings().all()
    processed = 0
    for job in due:
        sid = str(job["subscription_id"])
        period_end = now + timedelta(days=30)
        db.execute(
            text(
                """
                UPDATE customer_subscriptions
                SET status = 'ACTIVE', current_period_start = :now, current_period_end = :end,
                    next_billing_at = :end, updated_at = :now
                WHERE id = :sid
                """
            ),
            {"sid": sid, "now": now, "end": period_end},
        )
        db.execute(
            text(
                """
                UPDATE subscription_renewal_queue
                SET status = 'DONE', executed_at = :now, attempt_count = attempt_count + 1
                WHERE id = :id
                """
            ),
            {"id": job["id"], "now": now},
        )
        processed += 1
    db.commit()
    return {"ok": True, "processed": processed}


@router.get("/churn/alerts")
def list_churn_alerts(open_only: bool = Query(True), db: Session = Depends(get_db)):
    clauses = ["1=1"]
    if open_only:
        clauses.append("resolved_at IS NULL")
    rows = db.execute(
        text(
            f"""
            SELECT a.*, cs.user_id, cs.plan_type
            FROM subscription_churn_alerts a
            JOIN customer_subscriptions cs ON cs.id = a.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY a.created_at DESC
            LIMIT 100
            """
        )
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/churn/alerts/{alert_id}/resolve")
def resolve_churn_alert(alert_id: str, db: Session = Depends(get_db)):
    now = _utc_now()
    res = db.execute(
        text("UPDATE subscription_churn_alerts SET resolved_at = :now WHERE id = :id AND resolved_at IS NULL"),
        {"id": alert_id, "now": now},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "ALERT_NOT_FOUND", "message": alert_id})
    return {"ok": True}
