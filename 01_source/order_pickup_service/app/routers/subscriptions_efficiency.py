"""Eficiência: promo codes, mudança de plano, medidores, automações, family seats, inbox OPS."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.subscriptions_efficiency_seed import seed_subscriptions_efficiency
from app.routers.subscriptions_ops import _to_iso, _utc_now

router = APIRouter(tags=["subscriptions-efficiency"])


class PromoCodeIn(BaseModel):
    code: str = Field(..., min_length=3, max_length=32)
    description: str | None = None
    discount_pct: float = Field(default=0, ge=0, le=100)
    discount_cents: int = Field(default=0, ge=0)
    bonus_months: int = Field(default=0, ge=0, le=12)
    eligible_plans: list[str] = Field(default_factory=list)
    max_redemptions: int | None = Field(default=None, ge=1)
    partner_code: str | None = None


class PromoValidateIn(BaseModel):
    code: str
    user_id: str
    plan_code: str


class PlanChangeIn(BaseModel):
    subscription_id: str
    to_plan_code: str
    actor_id: str | None = None
    notes: str | None = None


class MeterRecordIn(BaseModel):
    subscription_id: str
    meter_code: str = Field(..., pattern="^(ORDERS|LOCKER_PICKUPS|FOOD_ORDERS)$")
    quantity: int = Field(..., ge=0)
    period_month: str | None = None


class AutomationRuleIn(BaseModel):
    rule_code: str
    name: str
    trigger_event: str
    action_type: str
    config_json: dict[str, Any] = Field(default_factory=dict)
    priority: int = 100


class FamilyMemberIn(BaseModel):
    subscription_id: str
    member_user_id: str
    role: str = "MEMBER"


class InboxActionIn(BaseModel):
    kind: str = Field(..., pattern="^(DUNNING|CHURN|RENEWAL|RETENTION|UPGRADE)$")
    id: str = Field(..., min_length=1)
    action: str = Field(default="primary", max_length=32)
    actor_id: str | None = None
    notes: str | None = None


class InboxBulkIn(BaseModel):
    operation: str = Field(..., pattern="^(renewals_run_due|churn_resolve_high|churn_resolve_all)$")


_INBOX_ACTIONS: dict[str, list[dict[str, str]]] = {
    "DUNNING": [{"action": "resolve", "label": "Resolver"}],
    "CHURN": [{"action": "resolve", "label": "Marcar resolvido"}],
    "RENEWAL": [{"action": "process", "label": "Processar"}],
    "RETENTION": [
        {"action": "accept", "label": "Aceitar"},
        {"action": "decline", "label": "Recusar"},
    ],
    "UPGRADE": [{"action": "apply_upgrade", "label": "Aplicar upgrade"}],
}


def _format_brl(cents: int) -> str:
    return f"R$ {cents / 100:.2f}"


def _coerce_utc(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _parse_plans_json(raw: Any) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return [str(p).upper() for p in data] if isinstance(data, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


@router.post("/efficiency/seed")
def efficiency_seed(db: Session = Depends(get_db)):
    return {"ok": True, "seeded": seed_subscriptions_efficiency(db)}


@router.get("/efficiency/summary")
def efficiency_summary(db: Session = Depends(get_db)):
    def c(table: str, where: str = "1=1") -> int:
        return int(db.execute(text(f"SELECT COUNT(*) FROM {table} WHERE {where}")).scalar() or 0)

    return {
        "ok": True,
        "counts": {
            "promo_codes": c("subscription_promo_codes", "active = TRUE"),
            "automation_rules": c("subscription_automation_rules", "active = TRUE"),
            "usage_meters": c("subscription_usage_meters"),
            "family_members": c("subscription_family_members", "status = 'ACTIVE'"),
            "plan_changes": c("subscription_plan_changes"),
        },
    }


def _inbox_item(kind: str, **fields: Any) -> dict[str, Any]:
    item = {"kind": kind, "actions": _INBOX_ACTIONS.get(kind, []), **fields}
    return item


def _collect_upgrade_suggestions(db: Session) -> list[dict[str, Any]]:
    period = _utc_now().strftime("%Y-%m")
    rows = db.execute(
        text(
            """
            SELECT cs.id, cs.user_id, cs.plan_type, cs.monthly_fee_cents,
                   m.quantity, m.included_quantity, m.overage_cents,
                   sp.max_orders_per_month
            FROM customer_subscriptions cs
            LEFT JOIN subscription_usage_meters m ON m.subscription_id = cs.id
              AND m.meter_code = 'ORDERS' AND m.period_month = :pm
            LEFT JOIN subscription_plans sp ON sp.code = cs.plan_type
            WHERE cs.status IN ('ACTIVE', 'TRIALING')
            LIMIT 100
            """
        ),
        {"pm": period},
    ).mappings().all()
    suggestions: list[dict[str, Any]] = []
    order = ["BASIC", "PREMIUM", "PRO", "ENTERPRISE"]
    for r in rows:
        plan = str(r["plan_type"])
        qty = int(r.get("quantity") or 0)
        inc = r.get("included_quantity")
        if inc is not None and qty >= int(inc) * 0.9 and plan != "ENTERPRISE":
            idx = order.index(plan) if plan in order else 0
            target = order[min(idx + 1, len(order) - 1)]
            suggestions.append(
                {
                    "subscription_id": str(r["id"]),
                    "user_id": str(r["user_id"]),
                    "current_plan": plan,
                    "suggested_plan": target,
                    "usage_pct": round(100 * qty / max(int(inc), 1), 1),
                    "overage_cents": int(r.get("overage_cents") or 0),
                }
            )
    return suggestions


def _process_renewal_job(db: Session, queue_id: str, now: datetime | None = None) -> bool:
    now = now or _utc_now()
    job = db.execute(
        text(
            """
            SELECT id, subscription_id, status, scheduled_at
            FROM subscription_renewal_queue
            WHERE id = :id AND status = 'PENDING' LIMIT 1
            """
        ),
        {"id": queue_id},
    ).mappings().first()
    if not job:
        return False
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
        {"id": queue_id, "now": now},
    )
    db.execute(
        text(
            """
            INSERT INTO subscription_events (id, subscription_id, event_type, actor_id, payload_json, created_at)
            VALUES (:id, :sid, 'subscription.renewed', NULL, :payload, :now)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "sid": sid,
            "payload": json.dumps({"queue_id": queue_id, "source": "ops_inbox"}),
            "now": now,
        },
    )
    return True


def _run_due_renewals(db: Session, limit: int = 50) -> int:
    now = _utc_now()
    due = db.execute(
        text(
            """
            SELECT id FROM subscription_renewal_queue
            WHERE status = 'PENDING' AND scheduled_at <= :now
            ORDER BY scheduled_at
            LIMIT :lim
            """
        ),
        {"now": now, "lim": limit},
    ).mappings().all()
    processed = 0
    for row in due:
        if _process_renewal_job(db, str(row["id"]), now):
            processed += 1
    return processed


@router.get("/efficiency/ops-inbox")
def ops_inbox(db: Session = Depends(get_db)):
    """Fila unificada de ações OPS derivadas de dunning, churn, renovações e retenção."""
    items: list[dict[str, Any]] = []

    dunning = db.execute(
        text(
            """
            SELECT d.id, d.subscription_id, d.stage, d.status, d.amount_due_cents,
                   cs.user_id, cs.plan_type
            FROM subscription_dunning_cases d
            JOIN customer_subscriptions cs ON cs.id = d.subscription_id
            WHERE d.status = 'OPEN'
            ORDER BY d.opened_at DESC LIMIT 20
            """
        )
    ).mappings().all()
    for r in dunning:
        items.append(
            _inbox_item(
                "DUNNING",
                priority=1,
                id=str(r["id"]),
                subscription_id=str(r["subscription_id"]),
                user_id=str(r["user_id"]),
                title=f"Dunning {r['stage']} — {_format_brl(int(r['amount_due_cents'] or 0))}",
                status=str(r["status"]),
            )
        )

    churn = db.execute(
        text(
            """
            SELECT a.id, a.subscription_id, a.alert_type, a.severity, a.message,
                   cs.user_id, cs.plan_type
            FROM subscription_churn_alerts a
            JOIN customer_subscriptions cs ON cs.id = a.subscription_id
            WHERE a.resolved_at IS NULL
            ORDER BY a.created_at DESC LIMIT 20
            """
        )
    ).mappings().all()
    for r in churn:
        sev = str(r["severity"])
        items.append(
            _inbox_item(
                "CHURN",
                priority=0 if sev in ("HIGH", "CRITICAL") else 2,
                id=str(r["id"]),
                subscription_id=str(r["subscription_id"]),
                user_id=str(r["user_id"]),
                title=f"[{sev}] {r.get('alert_type', 'alert')}: {r['message']}",
                status="OPEN",
                severity=sev,
            )
        )

    renewals = db.execute(
        text(
            """
            SELECT q.id, q.subscription_id, q.scheduled_at, q.status, cs.user_id
            FROM subscription_renewal_queue q
            JOIN customer_subscriptions cs ON cs.id = q.subscription_id
            WHERE q.status = 'PENDING' AND q.scheduled_at <= :now
            ORDER BY q.scheduled_at LIMIT 20
            """
        ),
        {"now": _utc_now()},
    ).mappings().all()
    for r in renewals:
        items.append(
            _inbox_item(
                "RENEWAL",
                priority=3,
                id=str(r["id"]),
                subscription_id=str(r["subscription_id"]),
                user_id=str(r["user_id"]),
                title=f"Renovação vencida — {r['scheduled_at']}",
                status=str(r["status"]),
            )
        )

    retention = db.execute(
        text(
            """
            SELECT r.id, r.subscription_id, r.offer_code, r.discount_pct, r.valid_until,
                   cs.user_id
            FROM subscription_retention_offers r
            JOIN customer_subscriptions cs ON cs.id = r.subscription_id
            WHERE r.status = 'OFFERED' AND r.valid_until >= :now
            ORDER BY r.valid_until LIMIT 15
            """
        ),
        {"now": _utc_now()},
    ).mappings().all()
    for r in retention:
        items.append(
            _inbox_item(
                "RETENTION",
                priority=4,
                id=str(r["id"]),
                subscription_id=str(r["subscription_id"]),
                user_id=str(r["user_id"]),
                title=f"Oferta {r['offer_code']} −{r['discount_pct']}%",
                status="OFFERED",
            )
        )

    for s in _collect_upgrade_suggestions(db)[:15]:
        items.append(
            _inbox_item(
                "UPGRADE",
                priority=5,
                id=str(s["subscription_id"]),
                subscription_id=str(s["subscription_id"]),
                user_id=str(s["user_id"]),
                title=f"Upgrade {s['current_plan']} → {s['suggested_plan']} (uso {s['usage_pct']}%)",
                status="SUGGESTED",
                suggested_plan=str(s["suggested_plan"]),
                current_plan=str(s["current_plan"]),
                usage_pct=float(s["usage_pct"]),
            )
        )

    items.sort(key=lambda x: (x["priority"], x["kind"]))
    return {
        "ok": True,
        "items": items,
        "total": len(items),
        "bulk_operations": [
            {"operation": "renewals_run_due", "label": "Processar todas renovações vencidas"},
            {"operation": "churn_resolve_high", "label": "Resolver alertas HIGH/CRITICAL"},
            {"operation": "churn_resolve_all", "label": "Resolver todos alertas churn abertos"},
        ],
    }


@router.post("/efficiency/ops-inbox/act")
def ops_inbox_action(body: InboxActionIn, db: Session = Depends(get_db)):
    """Executa ação de um item da inbox (kind + id + action)."""
    now = _utc_now()
    action = body.action.strip().lower()
    kind = body.kind.upper()

    if kind == "DUNNING" and action in ("primary", "resolve"):
        row = db.execute(
            text("SELECT subscription_id FROM subscription_dunning_cases WHERE id = :id"),
            {"id": body.id.strip()},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail={"type": "DUNNING_NOT_FOUND", "message": body.id})
        note = body.notes or "Resolvido via OPS inbox"
        db.execute(
            text(
                """
                UPDATE subscription_dunning_cases
                SET status = 'RESOLVED', resolved_at = :now, resolution_note = :note, updated_at = :now
                WHERE id = :id
                """
            ),
            {"id": body.id.strip(), "now": now, "note": note},
        )
        db.execute(
            text(
                "UPDATE customer_subscriptions SET status = 'ACTIVE', updated_at = :now WHERE id = :sid"
            ),
            {"sid": row["subscription_id"], "now": now},
        )
        db.commit()
        return {"ok": True, "kind": kind, "id": body.id, "action": "resolve"}

    if kind == "CHURN" and action in ("primary", "resolve"):
        res = db.execute(
            text(
                "UPDATE subscription_churn_alerts SET resolved_at = :now WHERE id = :id AND resolved_at IS NULL"
            ),
            {"id": body.id.strip(), "now": now},
        )
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail={"type": "ALERT_NOT_FOUND", "message": body.id})
        db.commit()
        return {"ok": True, "kind": kind, "id": body.id, "action": "resolve"}

    if kind == "RENEWAL" and action in ("primary", "process"):
        if not _process_renewal_job(db, body.id.strip(), now):
            raise HTTPException(
                status_code=404,
                detail={"type": "RENEWAL_NOT_FOUND", "message": "Fila inexistente ou já processada."},
            )
        db.commit()
        return {"ok": True, "kind": kind, "id": body.id, "action": "process"}

    if kind == "RETENTION" and action in ("primary", "accept"):
        row = db.execute(
            text(
                """
                SELECT subscription_id, discount_pct, bonus_months FROM subscription_retention_offers
                WHERE id = :id AND status = 'OFFERED' AND valid_until >= :now LIMIT 1
                """
            ),
            {"id": body.id.strip(), "now": now},
        ).mappings().first()
        if not row:
            raise HTTPException(status_code=404, detail={"type": "OFFER_NOT_FOUND", "message": body.id})
        db.execute(
            text(
                "UPDATE subscription_retention_offers SET status = 'ACCEPTED', accepted_at = :now WHERE id = :id"
            ),
            {"id": body.id.strip(), "now": now},
        )
        period_end = now + timedelta(days=30 * (1 + int(row["bonus_months"] or 0)))
        db.execute(
            text(
                """
                UPDATE customer_subscriptions
                SET cancel_at_period_end = FALSE, current_period_end = :end, next_billing_at = :end, updated_at = :now
                WHERE id = :sid
                """
            ),
            {"sid": row["subscription_id"], "end": period_end, "now": now},
        )
        db.commit()
        return {"ok": True, "kind": kind, "id": body.id, "action": "accept"}

    if kind == "RETENTION" and action == "decline":
        res = db.execute(
            text(
                """
                UPDATE subscription_retention_offers
                SET status = 'DECLINED', accepted_at = :now
                WHERE id = :id AND status = 'OFFERED'
                """
            ),
            {"id": body.id.strip(), "now": now},
        )
        if res.rowcount == 0:
            raise HTTPException(status_code=404, detail={"type": "OFFER_NOT_FOUND", "message": body.id})
        db.commit()
        return {"ok": True, "kind": kind, "id": body.id, "action": "decline"}

    if kind == "UPGRADE" and action in ("primary", "apply_upgrade"):
        sub_id = body.id.strip()
        sug = db.execute(
            text(
                """
                SELECT cs.plan_type, sp.max_orders_per_month, m.quantity, m.included_quantity
                FROM customer_subscriptions cs
                LEFT JOIN subscription_usage_meters m ON m.subscription_id = cs.id
                  AND m.meter_code = 'ORDERS' AND m.period_month = :pm
                LEFT JOIN subscription_plans sp ON sp.code = cs.plan_type
                WHERE cs.id = :sid LIMIT 1
                """
            ),
            {"sid": sub_id, "pm": now.strftime("%Y-%m")},
        ).mappings().first()
        if not sug:
            raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": sub_id})
        order = ["BASIC", "PREMIUM", "PRO", "ENTERPRISE"]
        plan = str(sug["plan_type"])
        idx = order.index(plan) if plan in order else 0
        to_plan = order[min(idx + 1, len(order) - 1)]
        if body.notes and body.notes.strip().upper() in order:
            to_plan = body.notes.strip().upper()
        return change_subscription_plan(
            PlanChangeIn(
                subscription_id=sub_id,
                to_plan_code=to_plan,
                actor_id=body.actor_id,
                notes="ops_inbox_upgrade",
            ),
            db,
        )

    raise HTTPException(
        status_code=422,
        detail={"type": "INVALID_INBOX_ACTION", "message": f"{kind}/{action} não suportado"},
    )


@router.post("/efficiency/ops-inbox/bulk")
def ops_inbox_bulk(body: InboxBulkIn, db: Session = Depends(get_db)):
    now = _utc_now()
    op = body.operation

    if op == "renewals_run_due":
        processed = _run_due_renewals(db)
        db.commit()
        return {"ok": True, "operation": op, "processed": processed}

    if op == "churn_resolve_high":
        res = db.execute(
            text(
                """
                UPDATE subscription_churn_alerts
                SET resolved_at = :now
                WHERE resolved_at IS NULL AND severity IN ('HIGH', 'CRITICAL')
                """
            ),
            {"now": now},
        )
        db.commit()
        return {"ok": True, "operation": op, "processed": int(res.rowcount or 0)}

    if op == "churn_resolve_all":
        res = db.execute(
            text(
                "UPDATE subscription_churn_alerts SET resolved_at = :now WHERE resolved_at IS NULL"
            ),
            {"now": now},
        )
        db.commit()
        return {"ok": True, "operation": op, "processed": int(res.rowcount or 0)}

    raise HTTPException(status_code=422, detail={"type": "INVALID_BULK_OP", "message": op})


@router.get("/efficiency/promo-codes")
def list_promo_codes(active_only: bool = Query(True), db: Session = Depends(get_db)):
    clause = "active = TRUE" if active_only else "1=1"
    rows = db.execute(
        text(f"SELECT * FROM subscription_promo_codes WHERE {clause} ORDER BY code")
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        item["eligible_plans"] = _parse_plans_json(item.pop("eligible_plans_json", "[]"))
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/efficiency/promo-codes")
def create_promo_code(body: PromoCodeIn, db: Session = Depends(get_db)):
    code = body.code.strip().upper()
    if db.execute(text("SELECT 1 FROM subscription_promo_codes WHERE code = :c"), {"c": code}).scalar():
        raise HTTPException(status_code=409, detail={"type": "PROMO_EXISTS", "message": code})
    pid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_promo_codes (
                id, code, description, discount_pct, discount_cents, bonus_months,
                eligible_plans_json, max_redemptions, partner_code, active, created_at, updated_at
            ) VALUES (
                :id, :code, :desc, :pct, :cents, :bonus, :plans, :maxr, :partner, TRUE, :now, :now
            )
            """
        ),
        {
            "id": pid,
            "code": code,
            "desc": body.description,
            "pct": body.discount_pct,
            "cents": body.discount_cents,
            "bonus": body.bonus_months,
            "plans": json.dumps([p.upper() for p in body.eligible_plans]),
            "maxr": body.max_redemptions,
            "partner": body.partner_code,
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": pid, "code": code}


@router.post("/efficiency/promo-codes/validate")
def validate_promo_code(body: PromoValidateIn, db: Session = Depends(get_db)):
    from app.services import subscription_promo_service as promo_svc

    return promo_svc.validate_promo(
        db, code=body.code, user_id=body.user_id, plan_code=body.plan_code
    )


@router.get("/efficiency/plan-changes")
def list_plan_changes(
    subscription_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if subscription_id:
        clauses.append("pc.subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    rows = db.execute(
        text(
            f"""
            SELECT pc.*, cs.user_id
            FROM subscription_plan_changes pc
            JOIN customer_subscriptions cs ON cs.id = pc.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY pc.created_at DESC LIMIT 100
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/efficiency/plan-changes")
def change_subscription_plan(body: PlanChangeIn, db: Session = Depends(get_db)):
    sub = db.execute(
        text(
            """
            SELECT id, plan_type, monthly_fee_cents, status FROM customer_subscriptions
            WHERE id = :id LIMIT 1
            """
        ),
        {"id": body.subscription_id.strip()},
    ).mappings().first()
    if not sub:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": body.subscription_id})

    new_plan = db.execute(
        text(
            """
            SELECT code, monthly_fee_cents, free_shipping, priority_shelf, exclusive_deals
            FROM subscription_plans WHERE code = :c AND is_active = TRUE LIMIT 1
            """
        ),
        {"c": body.to_plan_code.strip().upper()},
    ).mappings().first()
    if not new_plan:
        raise HTTPException(status_code=422, detail={"type": "PLAN_NOT_FOUND", "message": body.to_plan_code})

    from_plan = str(sub["plan_type"])
    to_plan = str(new_plan["code"])
    old_fee = int(sub["monthly_fee_cents"])
    new_fee = int(new_plan["monthly_fee_cents"])
    change_type = "UPGRADE" if new_fee >= old_fee else "DOWNGRADE"
    proration = max(0, new_fee - old_fee) if change_type == "UPGRADE" else 0
    now = _utc_now()

    db.execute(
        text(
            """
            UPDATE customer_subscriptions
            SET plan_type = :plan, monthly_fee_cents = :fee,
                free_shipping = :fs, priority_shelf = :ps, exclusive_deals = :ed,
                updated_at = :now
            WHERE id = :id
            """
        ),
        {
            "id": sub["id"],
            "plan": to_plan,
            "fee": new_fee,
            "fs": bool(new_plan["free_shipping"]),
            "ps": bool(new_plan["priority_shelf"]),
            "ed": bool(new_plan["exclusive_deals"]),
            "now": now,
        },
    )
    chg_id = str(uuid.uuid4())
    db.execute(
        text(
            """
            INSERT INTO subscription_plan_changes (
                id, subscription_id, from_plan_code, to_plan_code, change_type,
                proration_cents, effective_at, actor_id, notes, created_at
            ) VALUES (:id, :sid, :fp, :tp, :ct, :pr, :now, :actor, :notes, :now)
            """
        ),
        {
            "id": chg_id,
            "sid": sub["id"],
            "fp": from_plan,
            "tp": to_plan,
            "ct": change_type,
            "pr": proration,
            "actor": body.actor_id,
            "notes": body.notes,
            "now": now,
        },
    )
    db.execute(
        text(
            """
            INSERT INTO subscription_events (id, subscription_id, event_type, actor_id, payload_json, created_at)
            VALUES (:id, :sid, 'subscription.plan_changed', :actor, :payload, :now)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "sid": sub["id"],
            "actor": body.actor_id,
            "payload": json.dumps({"from": from_plan, "to": to_plan, "change_type": change_type}),
            "now": now,
        },
    )
    db.commit()
    return {
        "ok": True,
        "change_id": chg_id,
        "from_plan": from_plan,
        "to_plan": to_plan,
        "change_type": change_type,
        "proration_cents": proration,
        "new_monthly_fee_cents": new_fee,
    }


@router.get("/efficiency/usage-meters")
def list_usage_meters(
    subscription_id: Optional[str] = Query(None),
    period_month: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if subscription_id:
        clauses.append("m.subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    if period_month:
        clauses.append("m.period_month = :pm")
        params["pm"] = period_month.strip()
    rows = db.execute(
        text(
            f"""
            SELECT m.*, cs.user_id, cs.plan_type
            FROM subscription_usage_meters m
            JOIN customer_subscriptions cs ON cs.id = m.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY m.period_month DESC, m.meter_code
            LIMIT 200
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/efficiency/usage-meters/record")
def record_usage_meter(body: MeterRecordIn, db: Session = Depends(get_db)):
    now = _utc_now()
    period = body.period_month or now.strftime("%Y-%m")
    plan = db.execute(
        text(
            """
            SELECT cs.plan_type, sp.max_orders_per_month
            FROM customer_subscriptions cs
            LEFT JOIN subscription_plans sp ON sp.code = cs.plan_type
            WHERE cs.id = :id LIMIT 1
            """
        ),
        {"id": body.subscription_id.strip()},
    ).mappings().first()
    if not plan:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": body.subscription_id})

    included = int(plan["max_orders_per_month"]) if body.meter_code == "ORDERS" and plan.get("max_orders_per_month") else None
    overage = 0
    if included is not None and body.quantity > included:
        overage = (body.quantity - included) * 99

    mid = str(uuid.uuid4())
    existing = db.execute(
        text(
            """
            SELECT id FROM subscription_usage_meters
            WHERE subscription_id = :sid AND meter_code = :mc AND period_month = :pm LIMIT 1
            """
        ),
        {"sid": body.subscription_id.strip(), "mc": body.meter_code, "pm": period},
    ).mappings().first()
    if existing:
        db.execute(
            text(
                """
                UPDATE subscription_usage_meters
                SET quantity = :qty, included_quantity = :inc, overage_cents = :ov, recorded_at = :now
                WHERE id = :id
                """
            ),
            {
                "id": existing["id"],
                "qty": body.quantity,
                "inc": included,
                "ov": overage,
                "now": now,
            },
        )
        mid = str(existing["id"])
    else:
        db.execute(
            text(
                """
                INSERT INTO subscription_usage_meters (
                    id, subscription_id, meter_code, period_month, quantity,
                    included_quantity, overage_cents, recorded_at
                ) VALUES (:id, :sid, :mc, :pm, :qty, :inc, :ov, :now)
                """
            ),
            {
                "id": mid,
                "sid": body.subscription_id.strip(),
                "mc": body.meter_code,
                "pm": period,
                "qty": body.quantity,
                "inc": included,
                "ov": overage,
                "now": now,
            },
        )
    db.commit()
    return {"ok": True, "id": mid, "overage_cents": overage, "included_quantity": included}


@router.get("/efficiency/automation-rules")
def list_automation_rules(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM subscription_automation_rules ORDER BY priority, rule_code")
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["config"] = json.loads(item.pop("config_json", "{}") or "{}")
        except json.JSONDecodeError:
            item["config"] = {}
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/efficiency/automation-rules")
def create_automation_rule(body: AutomationRuleIn, db: Session = Depends(get_db)):
    rid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_automation_rules (
                id, rule_code, name, trigger_event, action_type, config_json,
                priority, active, created_at, updated_at
            ) VALUES (:id, :code, :name, :trig, :act, :cfg, :pri, TRUE, :now, :now)
            """
        ),
        {
            "id": rid,
            "code": body.rule_code.strip().upper(),
            "name": body.name,
            "trig": body.trigger_event,
            "act": body.action_type,
            "cfg": json.dumps(body.config_json),
            "pri": body.priority,
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": rid}


@router.post("/efficiency/automation-rules/evaluate")
def evaluate_automation_rules(
    event_type: str = Query(...),
    subscription_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Simula disparo de regras para um evento (útil em testes e webhooks internos)."""
    rules = db.execute(
        text(
            """
            SELECT id, rule_code, action_type, config_json FROM subscription_automation_rules
            WHERE active = TRUE AND trigger_event = :ev ORDER BY priority
            """
        ),
        {"ev": event_type.strip()},
    ).mappings().all()
    fired = []
    now = _utc_now()
    for rule in rules:
        db.execute(
            text(
                "UPDATE subscription_automation_rules SET run_count = run_count + 1, last_run_at = :now WHERE id = :id"
            ),
            {"id": rule["id"], "now": now},
        )
        fired.append(
            {
                "rule_code": rule["rule_code"],
                "action_type": rule["action_type"],
                "config": json.loads(rule.get("config_json") or "{}"),
            }
        )
        if rule["action_type"] == "ISSUE_RETENTION_OFFER" and subscription_id:
            cfg = json.loads(rule.get("config_json") or "{}")
            disc = float(cfg.get("discount_pct", 10))
            db.execute(
                text(
                    """
                    INSERT INTO subscription_retention_offers (
                        id, subscription_id, offer_code, discount_pct, bonus_months,
                        valid_until, status, created_at
                    ) VALUES (:id, :sid, :code, :disc, 0, :valid, 'OFFERED', :now)
                    """
                ),
                {
                    "id": str(uuid.uuid4()),
                    "sid": subscription_id,
                    "code": f"AUTO-{rule['rule_code'][:12]}",
                    "disc": disc,
                    "valid": now + timedelta(days=14),
                    "now": now,
                },
            )
    db.commit()
    return {"ok": True, "event_type": event_type, "fired": fired, "total": len(fired)}


@router.get("/efficiency/family-members")
def list_family_members(
    subscription_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if subscription_id:
        clauses.append("f.subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    rows = db.execute(
        text(
            f"""
            SELECT f.*, cs.user_id AS owner_user_id, cs.plan_type
            FROM subscription_family_members f
            JOIN customer_subscriptions cs ON cs.id = f.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY f.invited_at DESC LIMIT 100
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/efficiency/family-members")
def add_family_member(body: FamilyMemberIn, db: Session = Depends(get_db)):
    fid = str(uuid.uuid4())
    now = _utc_now()
    count = db.execute(
        text(
            "SELECT COUNT(*) FROM subscription_family_members WHERE subscription_id = :s AND status = 'ACTIVE'"
        ),
        {"s": body.subscription_id.strip()},
    ).scalar()
    if int(count or 0) >= 5:
        raise HTTPException(status_code=409, detail={"type": "FAMILY_LIMIT", "message": "Máximo 5 membros por assinatura."})
    db.execute(
        text(
            """
            INSERT INTO subscription_family_members (
                id, subscription_id, member_user_id, role, status, invited_at, joined_at
            ) VALUES (:id, :sid, :mid, :role, 'ACTIVE', :now, :now)
            """
        ),
        {
            "id": fid,
            "sid": body.subscription_id.strip(),
            "mid": body.member_user_id.strip(),
            "role": body.role.upper(),
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": fid}


@router.get("/efficiency/upgrade-matrix")
def upgrade_matrix(db: Session = Depends(get_db)):
    """Sugestões de upgrade com base em uso de pedidos no mês corrente."""
    period = _utc_now().strftime("%Y-%m")
    suggestions = _collect_upgrade_suggestions(db)
    return {"ok": True, "period_month": period, "items": suggestions, "total": len(suggestions)}
