"""OPS: planos, assinaturas de clientes, webhooks e API keys."""
from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.subscriptions_ecosystem import ecosystem_catalog_payload
from app.core.subscriptions_seed import seed_subscriptions
from app.schemas.subscriptions_ops import (
    CustomerSubscriptionIn,
    CustomerSubscriptionOut,
    CustomerSubscriptionUpdate,
    SubscriptionPlanIn,
    SubscriptionPlanOut,
    SubscriptionPlanUpdate,
    SubscriptionWebhookIn,
    SubscriptionWebhookUpdate,
)

router = APIRouter(tags=["subscriptions-ops"])

_PLAN_SELECT = """
    SELECT id, name, code, description, monthly_fee_cents, yearly_fee_cents,
           free_shipping, priority_shelf, exclusive_deals, priority_support,
           max_orders_per_month, max_discount_pct, features_json, is_active,
           created_at, updated_at
    FROM subscription_plans
"""

_SUB_SELECT = """
    SELECT id, user_id, plan_type, status, monthly_fee_cents,
           free_shipping, priority_shelf, exclusive_deals,
           billing_cycle, cancel_at_period_end,
           trial_start, trial_end, current_period_start, current_period_end,
           next_billing_at, cancelled_at, payment_method_id, partner_code,
           created_at, updated_at
    FROM customer_subscriptions
"""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_iso(value: Any) -> str:
    if value is None:
        return _utc_now().isoformat()
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
    return str(value)


def _parse_json(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}


def _plan_out(row: dict[str, Any]) -> SubscriptionPlanOut:
    return SubscriptionPlanOut(
        id=str(row["id"]),
        name=str(row["name"]),
        code=str(row["code"]),
        description=(str(row["description"]) if row.get("description") is not None else None),
        monthly_fee_cents=int(row["monthly_fee_cents"]),
        yearly_fee_cents=(int(row["yearly_fee_cents"]) if row.get("yearly_fee_cents") is not None else None),
        free_shipping=bool(row.get("free_shipping")),
        priority_shelf=bool(row.get("priority_shelf")),
        exclusive_deals=bool(row.get("exclusive_deals")),
        priority_support=bool(row.get("priority_support")),
        max_orders_per_month=(int(row["max_orders_per_month"]) if row.get("max_orders_per_month") is not None else None),
        max_discount_pct=(float(row["max_discount_pct"]) if row.get("max_discount_pct") is not None else None),
        features_json=_parse_json(row.get("features_json")),
        is_active=bool(row.get("is_active", True)),
        created_at=_to_iso(row.get("created_at")),
        updated_at=_to_iso(row.get("updated_at")),
    )


def _sub_out(row: dict[str, Any]) -> CustomerSubscriptionOut:
    return CustomerSubscriptionOut(
        id=str(row["id"]),
        user_id=(str(row["user_id"]) if row.get("user_id") is not None else None),
        plan_type=str(row["plan_type"]),
        status=str(row.get("status") or "ACTIVE"),
        monthly_fee_cents=int(row["monthly_fee_cents"]),
        free_shipping=bool(row.get("free_shipping")),
        priority_shelf=bool(row.get("priority_shelf")),
        exclusive_deals=bool(row.get("exclusive_deals")),
        billing_cycle=str(row.get("billing_cycle") or "MONTHLY"),
        cancel_at_period_end=bool(row.get("cancel_at_period_end")),
        trial_start=_to_iso(row["trial_start"]) if row.get("trial_start") else None,
        trial_end=_to_iso(row["trial_end"]) if row.get("trial_end") else None,
        current_period_start=_to_iso(row["current_period_start"]) if row.get("current_period_start") else None,
        current_period_end=_to_iso(row["current_period_end"]) if row.get("current_period_end") else None,
        next_billing_at=_to_iso(row["next_billing_at"]) if row.get("next_billing_at") else None,
        cancelled_at=_to_iso(row["cancelled_at"]) if row.get("cancelled_at") else None,
        payment_method_id=(str(row["payment_method_id"]) if row.get("payment_method_id") else None),
        partner_code=(str(row["partner_code"]) if row.get("partner_code") else None),
        created_at=_to_iso(row.get("created_at")),
        updated_at=_to_iso(row.get("updated_at")),
    )


def _hash_secret(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _new_api_key() -> tuple[str, str, str]:
    raw = f"sub_{secrets.token_urlsafe(24)}"
    return raw, raw[:12], _hash_secret(raw)


def _resolve_plan_pricing(db: Session, plan_type: str) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT code, monthly_fee_cents, free_shipping, priority_shelf, exclusive_deals
            FROM subscription_plans WHERE code = :code AND is_active = TRUE LIMIT 1
            """
        ),
        {"code": plan_type.strip().upper()},
    ).mappings().first()
    if not row:
        raise HTTPException(
            status_code=422,
            detail={"type": "PLAN_NOT_FOUND", "message": f"Plano {plan_type} não encontrado."},
        )
    return dict(row)


@router.get("/ecosystem/catalog")
def subscriptions_ecosystem_catalog():
    return {"ok": True, "catalog": ecosystem_catalog_payload()}


@router.post("/seed")
def subscriptions_seed(db: Session = Depends(get_db)):
    seeded = seed_subscriptions(db)
    return {"ok": True, "seeded": seeded}


@router.get("/metrics/summary")
def subscriptions_metrics_summary(db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            SELECT
                COUNT(*) FILTER (WHERE status = 'ACTIVE') AS active_count,
                COUNT(*) FILTER (WHERE status = 'TRIALING') AS trialing_count,
                COUNT(*) FILTER (WHERE status = 'PAST_DUE') AS past_due_count,
                COUNT(*) FILTER (WHERE status = 'CANCELLED') AS cancelled_count,
                COALESCE(SUM(monthly_fee_cents) FILTER (WHERE status IN ('ACTIVE','TRIALING')), 0) AS mrr_cents
            FROM customer_subscriptions
            """
        )
    ).mappings().first()
    plans = db.execute(text("SELECT COUNT(*) AS c FROM subscription_plans WHERE is_active = TRUE")).mappings().first()
    data = dict(row or {})
    return {
        "ok": True,
        "summary": {
            "active_subscriptions": int(data.get("active_count") or 0),
            "trialing_subscriptions": int(data.get("trialing_count") or 0),
            "past_due_subscriptions": int(data.get("past_due_count") or 0),
            "cancelled_subscriptions": int(data.get("cancelled_count") or 0),
            "mrr_cents": int(data.get("mrr_cents") or 0),
            "active_plans": int((plans or {}).get("c") or 0),
        },
    }


@router.get("/plans")
def list_subscription_plans(
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    if active_only:
        clauses.append("is_active = TRUE")
    rows = db.execute(
        text(f"{_PLAN_SELECT} WHERE {' AND '.join(clauses)} ORDER BY monthly_fee_cents ASC")
    ).mappings().all()
    items = [_plan_out(dict(r)) for r in rows]
    return {"items": items, "total": len(items)}


@router.post("/plans", response_model=SubscriptionPlanOut)
def create_subscription_plan(payload: SubscriptionPlanIn, db: Session = Depends(get_db)):
    code = payload.code.strip().upper()
    exists = db.execute(text("SELECT 1 FROM subscription_plans WHERE code = :c LIMIT 1"), {"c": code}).scalar()
    if exists:
        raise HTTPException(status_code=409, detail={"type": "PLAN_EXISTS", "message": code})
    now = _utc_now()
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
                :max_orders, :max_disc, :features, :active, :now, :now
            )
            """
        ),
        {
            "id": pid,
            "name": payload.name.strip(),
            "code": code,
            "description": payload.description,
            "monthly": payload.monthly_fee_cents,
            "yearly": payload.yearly_fee_cents,
            "free_ship": payload.free_shipping,
            "priority": payload.priority_shelf,
            "deals": payload.exclusive_deals,
            "support": payload.priority_support,
            "max_orders": payload.max_orders_per_month,
            "max_disc": payload.max_discount_pct,
            "features": json.dumps(payload.features_json or {}),
            "active": payload.is_active,
            "now": now,
        },
    )
    db.commit()
    row = db.execute(text(f"{_PLAN_SELECT} WHERE id = :id"), {"id": pid}).mappings().first()
    return _plan_out(dict(row))


@router.patch("/plans/{plan_id}", response_model=SubscriptionPlanOut)
def update_subscription_plan(plan_id: str, payload: SubscriptionPlanUpdate, db: Session = Depends(get_db)):
    fields: dict[str, Any] = {}
    for key, col in (
        ("name", "name"),
        ("description", "description"),
        ("monthly_fee_cents", "monthly_fee_cents"),
        ("yearly_fee_cents", "yearly_fee_cents"),
        ("free_shipping", "free_shipping"),
        ("priority_shelf", "priority_shelf"),
        ("exclusive_deals", "exclusive_deals"),
        ("priority_support", "priority_support"),
        ("max_orders_per_month", "max_orders_per_month"),
        ("max_discount_pct", "max_discount_pct"),
        ("is_active", "is_active"),
    ):
        val = getattr(payload, key, None)
        if val is not None:
            fields[col] = val
    if payload.features_json is not None:
        fields["features_json"] = json.dumps(payload.features_json)
    if not fields:
        row = db.execute(text(f"{_PLAN_SELECT} WHERE id = :id"), {"id": plan_id}).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail={"type": "PLAN_NOT_FOUND", "message": plan_id})
        return _plan_out(dict(row))
    fields["updated_at"] = _utc_now()
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = plan_id
    db.execute(text(f"UPDATE subscription_plans SET {sets} WHERE id = :id"), fields)
    db.commit()
    row = db.execute(text(f"{_PLAN_SELECT} WHERE id = :id"), {"id": plan_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "PLAN_NOT_FOUND", "message": plan_id})
    return _plan_out(dict(row))


@router.delete("/plans/{plan_id}")
def deactivate_subscription_plan(plan_id: str, db: Session = Depends(get_db)):
    now = _utc_now()
    res = db.execute(
        text("UPDATE subscription_plans SET is_active = FALSE, updated_at = :now WHERE id = :id"),
        {"id": plan_id, "now": now},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "PLAN_NOT_FOUND", "message": plan_id})
    return {"ok": True, "id": plan_id}


@router.get("/subscriptions")
def list_customer_subscriptions(
    status: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    plan_type: Optional[str] = Query(None),
    partner_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("status = :status")
        params["status"] = status.strip().upper()
    if user_id:
        clauses.append("user_id = :user_id")
        params["user_id"] = user_id.strip()
    if plan_type:
        clauses.append("plan_type = :plan_type")
        params["plan_type"] = plan_type.strip().upper()
    if partner_code:
        clauses.append("partner_code = :partner_code")
        params["partner_code"] = partner_code.strip()
    rows = db.execute(
        text(f"{_SUB_SELECT} WHERE {' AND '.join(clauses)} ORDER BY created_at DESC LIMIT 500"),
        params,
    ).mappings().all()
    items = [_sub_out(dict(r)) for r in rows]
    return {"items": items, "total": len(items)}


@router.get("/subscriptions/{subscription_id}", response_model=CustomerSubscriptionOut)
def get_customer_subscription(subscription_id: str, db: Session = Depends(get_db)):
    row = db.execute(text(f"{_SUB_SELECT} WHERE id = :id"), {"id": subscription_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": subscription_id})
    return _sub_out(dict(row))


@router.post("/subscriptions", response_model=CustomerSubscriptionOut)
def create_customer_subscription(payload: CustomerSubscriptionIn, db: Session = Depends(get_db)):
    from app.services import subscription_promo_service as promo_svc

    plan = _resolve_plan_pricing(db, payload.plan_type)
    now = _utc_now()
    bonus_months = 0
    monthly_fee = int(plan["monthly_fee_cents"])
    if payload.promo_code and payload.promo_code.strip():
        preview = promo_svc.validate_promo(
            db,
            code=payload.promo_code.strip(),
            user_id=payload.user_id.strip(),
            plan_code=str(plan["code"]),
        )
        if not preview.get("valid"):
            raise HTTPException(
                status_code=422,
                detail={"type": "PROMO_INVALID", "message": preview.get("reason", "UNKNOWN")},
            )
        monthly_fee = max(0, monthly_fee - int(preview["discount_cents"]))
        bonus_months = int(preview.get("bonus_months") or 0)

    period_end = now + timedelta(days=30 * (1 + bonus_months))
    trial_end = None
    trial_start = None
    status = payload.status.strip().upper()
    if payload.trial_days:
        trial_start = now
        trial_end = now + timedelta(days=int(payload.trial_days))
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
                next_billing_at, started_at, payment_method_id, partner_code,
                created_at, updated_at
            ) VALUES (
                :id, :user_id, :plan_type, :status, :fee,
                :free_ship, :priority, :deals,
                :billing_cycle, FALSE,
                :trial_start, :trial_end, :period_start, :period_end,
                :next_billing, :started, :payment_method, :partner,
                :now, :now
            )
            """
        ),
        {
            "id": sid,
            "user_id": payload.user_id.strip(),
            "plan_type": plan["code"],
            "status": status,
            "fee": monthly_fee,
            "free_ship": bool(plan["free_shipping"]),
            "priority": bool(plan["priority_shelf"]),
            "deals": bool(plan["exclusive_deals"]),
            "billing_cycle": payload.billing_cycle.strip().upper(),
            "trial_start": trial_start,
            "trial_end": trial_end,
            "period_start": now,
            "period_end": period_end,
            "next_billing": period_end,
            "started": now,
            "payment_method": payload.payment_method_id,
            "partner": payload.partner_code,
            "now": now,
        },
    )
    if payload.promo_code and payload.promo_code.strip():
        promo_svc.redeem_promo(
            db,
            code=payload.promo_code.strip(),
            user_id=payload.user_id.strip(),
            plan_code=str(plan["code"]),
            subscription_id=sid,
        )
    db.commit()
    row = db.execute(text(f"{_SUB_SELECT} WHERE id = :id"), {"id": sid}).mappings().first()
    return _sub_out(dict(row))


@router.patch("/subscriptions/{subscription_id}", response_model=CustomerSubscriptionOut)
def update_customer_subscription(
    subscription_id: str,
    payload: CustomerSubscriptionUpdate,
    db: Session = Depends(get_db),
):
    fields: dict[str, Any] = {}
    if payload.status is not None:
        fields["status"] = payload.status.strip().upper()
    if payload.billing_cycle is not None:
        fields["billing_cycle"] = payload.billing_cycle.strip().upper()
    if payload.cancel_at_period_end is not None:
        fields["cancel_at_period_end"] = payload.cancel_at_period_end
    if payload.payment_method_id is not None:
        fields["payment_method_id"] = payload.payment_method_id
    if payload.plan_type is not None:
        plan = _resolve_plan_pricing(db, payload.plan_type)
        fields["plan_type"] = plan["code"]
        fields["monthly_fee_cents"] = int(plan["monthly_fee_cents"])
        fields["free_shipping"] = bool(plan["free_shipping"])
        fields["priority_shelf"] = bool(plan["priority_shelf"])
        fields["exclusive_deals"] = bool(plan["exclusive_deals"])
    if not fields:
        return get_customer_subscription(subscription_id, db)
    fields["updated_at"] = _utc_now()
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = subscription_id
    res = db.execute(text(f"UPDATE customer_subscriptions SET {sets} WHERE id = :id"), fields)
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": subscription_id})
    return get_customer_subscription(subscription_id, db)


@router.post("/subscriptions/{subscription_id}/cancel")
def cancel_customer_subscription(
    subscription_id: str,
    immediate: bool = Query(False),
    db: Session = Depends(get_db),
):
    now = _utc_now()
    if immediate:
        db.execute(
            text(
                """
                UPDATE customer_subscriptions
                SET status = 'CANCELLED', cancelled_at = :now, cancel_at_period_end = FALSE, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": subscription_id, "now": now},
        )
    else:
        db.execute(
            text(
                """
                UPDATE customer_subscriptions
                SET cancel_at_period_end = TRUE, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": subscription_id, "now": now},
        )
    db.commit()
    return {"ok": True, "id": subscription_id, "immediate": immediate}


@router.post("/subscriptions/{subscription_id}/renew")
def renew_customer_subscription(subscription_id: str, db: Session = Depends(get_db)):
    now = _utc_now()
    period_end = now + timedelta(days=30)
    res = db.execute(
        text(
            """
            UPDATE customer_subscriptions
            SET status = 'ACTIVE',
                current_period_start = :now,
                current_period_end = :end,
                next_billing_at = :end,
                cancelled_at = NULL,
                cancel_at_period_end = FALSE,
                updated_at = :now
            WHERE id = :id
            """
        ),
        {"id": subscription_id, "now": now, "end": period_end},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": subscription_id})
    return {"ok": True, "id": subscription_id, "current_period_end": period_end.isoformat()}


@router.get("/benefits-usage")
def list_benefits_usage(
    subscription_id: Optional[str] = Query(None),
    usage_month: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if subscription_id:
        clauses.append("subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    if usage_month:
        clauses.append("usage_month = :um")
        params["um"] = usage_month.strip()
    rows = db.execute(
        text(
            f"""
            SELECT id, subscription_id, usage_month, benefit_type, usage_count, usage_limit,
                   created_at, updated_at
            FROM subscription_benefits_usage
            WHERE {' AND '.join(clauses)}
            ORDER BY usage_month DESC, subscription_id
            LIMIT 500
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        d = dict(r)
        d["id"] = int(d["id"])
        d["usage_month"] = str(d.get("usage_month"))
        d["created_at"] = _to_iso(d.get("created_at"))
        d["updated_at"] = _to_iso(d.get("updated_at"))
        items.append(d)
    return {"items": items, "total": len(items)}


@router.get("/usage")
def list_subscription_usage(
    subscription_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if subscription_id:
        clauses.append("subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    rows = db.execute(
        text(
            f"""
            SELECT id, subscription_id, usage_month, orders_count, free_shipping_used, savings_cents
            FROM subscription_usage
            WHERE {' AND '.join(clauses)}
            ORDER BY usage_month DESC
            LIMIT 500
            """
        ),
        params,
    ).mappings().all()
    items = [dict(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.get("/webhooks")
def list_subscription_webhooks(
    partner_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if partner_code:
        clauses.append("partner_code = :p")
        params["p"] = partner_code.strip()
    rows = db.execute(
        text(
            f"""
            SELECT id, partner_code, url, events_json, active, created_at, updated_at
            FROM subscription_webhook_endpoints
            WHERE {' AND '.join(clauses)}
            ORDER BY partner_code
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["events"] = json.loads(r.get("events_json") or "[]")
        except json.JSONDecodeError:
            item["events"] = []
        item.pop("events_json", None)
        item["created_at"] = _to_iso(item.get("created_at"))
        item["updated_at"] = _to_iso(item.get("updated_at"))
        items.append(item)
    return {"items": items, "total": len(items)}


@router.put("/webhooks/{partner_code}")
def upsert_subscription_webhook(partner_code: str, body: SubscriptionWebhookIn, db: Session = Depends(get_db)):
    now = _utc_now()
    secret = body.secret or secrets.token_urlsafe(32)
    events = body.events or [
        "subscription.created",
        "subscription.renewed",
        "subscription.cancelled",
    ]
    existing = db.execute(
        text("SELECT id FROM subscription_webhook_endpoints WHERE partner_code = :p LIMIT 1"),
        {"p": partner_code.strip()},
    ).mappings().first()
    if existing:
        db.execute(
            text(
                """
                UPDATE subscription_webhook_endpoints
                SET url = :url, secret_hash = :hash, secret_key = :secret, events_json = :events,
                    active = :active, updated_at = :now
                WHERE partner_code = :p
                """
            ),
            {
                "url": body.url.strip(),
                "hash": _hash_secret(secret),
                "secret": secret,
                "events": json.dumps(events),
                "active": body.active,
                "now": now,
                "p": partner_code.strip(),
            },
        )
        endpoint_id = str(existing["id"])
    else:
        endpoint_id = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO subscription_webhook_endpoints (
                    id, partner_code, url, secret_hash, secret_key, events_json, active, created_at, updated_at
                ) VALUES (:id, :p, :url, :hash, :secret, :events, :active, :now, :now)
                """
            ),
            {
                "id": endpoint_id,
                "p": partner_code.strip(),
                "url": body.url.strip(),
                "hash": _hash_secret(secret),
                "secret": secret,
                "events": json.dumps(events),
                "active": body.active,
                "now": now,
            },
        )
    db.commit()
    return {"ok": True, "id": endpoint_id, "partner_code": partner_code.strip(), "secret": secret}


@router.patch("/webhooks/endpoint/{endpoint_id}")
def patch_subscription_webhook(endpoint_id: str, body: SubscriptionWebhookUpdate, db: Session = Depends(get_db)):
    row = db.execute(
        text("SELECT id FROM subscription_webhook_endpoints WHERE id = :id LIMIT 1"),
        {"id": endpoint_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "WEBHOOK_NOT_FOUND", "message": endpoint_id})
    fields: dict[str, Any] = {}
    if body.url is not None:
        fields["url"] = body.url.strip()
    if body.secret is not None:
        fields["secret_hash"] = _hash_secret(body.secret)
        fields["secret_key"] = body.secret
    if body.events is not None:
        fields["events_json"] = json.dumps(body.events)
    if body.active is not None:
        fields["active"] = body.active
    if not fields:
        return {"ok": True, "id": endpoint_id}
    fields["updated_at"] = _utc_now()
    sets = ", ".join(f"{k} = :{k}" for k in fields)
    fields["id"] = endpoint_id
    db.execute(text(f"UPDATE subscription_webhook_endpoints SET {sets} WHERE id = :id"), fields)
    db.commit()
    return {"ok": True, "id": endpoint_id}


@router.get("/api-keys")
def list_subscription_api_keys(
    partner_code: Optional[str] = Query(None),
    include_revoked: bool = Query(False),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if partner_code:
        clauses.append("partner_code = :p")
        params["p"] = partner_code.strip()
    if not include_revoked:
        clauses.append("revoked_at IS NULL")
    rows = db.execute(
        text(
            f"""
            SELECT id, partner_code, key_prefix, label, scopes_json, expires_at, last_used_at, revoked_at, created_at
            FROM subscription_api_keys
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["scopes"] = json.loads(r.get("scopes_json") or "[]")
        except json.JSONDecodeError:
            item["scopes"] = []
        item.pop("scopes_json", None)
        item["created_at"] = _to_iso(item.get("created_at"))
        if item.get("revoked_at"):
            item["revoked_at"] = _to_iso(item["revoked_at"])
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/api-keys/{partner_code}/rotate")
def rotate_subscription_api_key(
    partner_code: str,
    label: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    now = _utc_now()
    db.execute(
        text("UPDATE subscription_api_keys SET revoked_at = :now WHERE partner_code = :p AND revoked_at IS NULL"),
        {"p": partner_code.strip(), "now": now},
    )
    raw, prefix, key_hash = _new_api_key()
    key_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO subscription_api_keys (
                id, partner_code, key_prefix, key_hash, label, scopes_json, created_at
            ) VALUES (:id, :p, :prefix, :hash, :label, :scopes, :now)
            """
        ),
        {
            "id": key_id,
            "p": partner_code.strip(),
            "prefix": prefix,
            "hash": key_hash,
            "label": label or "rotated",
            "scopes": json.dumps(["subscriptions:read", "subscriptions:write", "subscriptions:webhook"]),
            "now": now,
        },
    )
    db.commit()
    return {"id": key_id, "partner_code": partner_code.strip(), "key_prefix": prefix, "api_key": raw}


from app.routers import subscriptions_efficiency, subscriptions_extended, subscriptions_premium, subscriptions_world  # noqa: E402

router.include_router(subscriptions_extended.router)
router.include_router(subscriptions_premium.router)
router.include_router(subscriptions_world.router)
router.include_router(subscriptions_efficiency.router)
