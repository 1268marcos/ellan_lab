"""OPS avançado: eventos, faturas, entitlements, parceiros, dunning, analytics."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.subscriptions_ecosystem import ecosystem_catalog_payload
from app.core.subscriptions_global_players import (
    GLOBAL_SUBSCRIPTION_PLAYERS,
    PRIORITY_PLAYER_CODES,
    priority_players_payload,
)
from app.core.subscriptions_ecosystem_relations import SUBSCRIPTION_PLAYER_RELATIONS
from app.core.subscriptions_ecosystem_sync import sync_full_ecosystem
from app.core.subscriptions_global_sync import sync_global_players_to_db
from app.routers.subscriptions_ops import _sub_out, _to_iso, _utc_now

router = APIRouter(tags=["subscriptions-extended"])


class SubscriptionEventIn(BaseModel):
    subscription_id: str
    event_type: str = Field(..., min_length=1, max_length=64)
    actor_id: str | None = None
    payload_json: dict[str, Any] | None = None


class PartnerProgramIn(BaseModel):
    partner_code: str
    partner_name: str
    partner_type: str = "MARKETPLACE"
    default_plan_code: str | None = None
    revenue_share_pct: float = 0
    countries: list[str] | None = None
    kyb_status: str = "APPROVED"
    active: bool = True


class EntitlementIn(BaseModel):
    plan_code: str
    player_code: str
    player_name: str
    player_type: str = "MARKETPLACE"
    region_codes: list[str] | None = None
    enabled: bool = True
    priority_level: int = 0


class InvoiceGenerateIn(BaseModel):
    subscription_id: str
    amount_cents: int | None = None


class DunningResolveIn(BaseModel):
    resolution_note: str | None = None


@router.get("/players/priority")
def list_priority_players():
    return {
        "ok": True,
        "codes": sorted(PRIORITY_PLAYER_CODES),
        "items": priority_players_payload(),
        "total": len(priority_players_payload()),
    }


@router.get("/players/catalog")
def list_players_catalog(
    region: Optional[str] = Query(None),
    player_type: Optional[str] = Query(None),
    priority_only: bool = Query(False),
    segment: Optional[str] = Query(None),
):
    items = list(GLOBAL_SUBSCRIPTION_PLAYERS)
    if priority_only:
        items = [p for p in items if p.get("priority") or p["code"] in PRIORITY_PLAYER_CODES]
    if region:
        reg = region.strip().upper()
        items = [p for p in items if reg in [r.upper() for r in (p.get("regions") or [])]]
    if player_type:
        pt = player_type.strip().upper()
        items = [p for p in items if str(p.get("player_type", "")).upper() == pt]
    if segment:
        seg = segment.strip().upper()
        items = [p for p in items if str(p.get("segment", "")).upper() == seg]
    return {"ok": True, "items": items, "total": len(items), "catalog_version": ecosystem_catalog_payload()["version"]}


@router.post("/sync/global-players")
def sync_global_players(db: Session = Depends(get_db)):
    stats = sync_global_players_to_db(db)
    return {"ok": True, "synced": stats}


@router.post("/sync/ecosystem-full")
def sync_ecosystem_full(db: Session = Depends(get_db)):
    stats = sync_full_ecosystem(db)
    return {"ok": True, "synced": stats}


@router.get("/ecosystem/relations")
def list_ecosystem_relations(
    relation_type: Optional[str] = Query(None),
    from_player: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["active = TRUE"]
    params: dict[str, Any] = {}
    if relation_type:
        clauses.append("relation_type = :rt")
        params["rt"] = relation_type.strip().upper()
    if from_player:
        clauses.append("from_player_code = :f")
        params["f"] = from_player.strip().lower()
    try:
        rows = db.execute(
            text(
                f"""
                SELECT id, from_player_code, to_player_code, relation_type, integration_mode,
                       min_plan_code, notes, created_at
                FROM subscription_player_relations
                WHERE {' AND '.join(clauses)}
                ORDER BY relation_type, from_player_code
                LIMIT 500
                """
            ),
            params,
        ).mappings().all()
        items = [dict(r) for r in rows]
    except Exception:
        items = list(SUBSCRIPTION_PLAYER_RELATIONS)
    return {"items": items, "total": len(items)}


@router.get("/ecosystem/integration-channels")
def list_ecosystem_integration_channels(
    player_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["active = TRUE"]
    params: dict[str, Any] = {}
    if player_code:
        clauses.append("player_code = :p")
        params["p"] = player_code.strip().lower()
    rows = db.execute(
        text(
            f"""
            SELECT id, player_code, channel_kind, direction, auth_type,
                   base_url_template, webhook_events_json, active
            FROM subscription_integration_channels
            WHERE {' AND '.join(clauses)}
            ORDER BY player_code, channel_kind
            LIMIT 500
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["webhook_events"] = json.loads(item.pop("webhook_events_json", None) or "[]")
        except json.JSONDecodeError:
            item["webhook_events"] = []
        items.append(item)
    return {"items": items, "total": len(items)}


@router.get("/ecosystem/food-handoffs")
def list_food_handoffs(
    food_platform: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["active = TRUE"]
    params: dict[str, Any] = {}
    if food_platform:
        clauses.append("food_platform_code = :f")
        params["f"] = food_platform.strip().lower()
    rows = db.execute(
        text(
            f"""
            SELECT id, food_platform_code, pickup_player_code, handoff_type,
                   sla_minutes, min_plan_code, integration_mode
            FROM subscription_food_delivery_handoffs
            WHERE {' AND '.join(clauses)}
            ORDER BY food_platform_code
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.get("/ecosystem/players-db")
def list_ecosystem_players_db(
    segment: Optional[str] = Query(None),
    supports_food: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["active = TRUE"]
    params: dict[str, Any] = {}
    if segment:
        clauses.append("segment = :seg")
        params["seg"] = segment.strip().upper()
    if supports_food is not None:
        clauses.append("supports_food = :sf")
        params["sf"] = supports_food
    rows = db.execute(
        text(
            f"""
            SELECT code, name, player_type, segment, regions_json,
                   supports_lockers, supports_pudo, supports_food, supports_marketplace,
                   default_plan_code, priority_flag
            FROM subscription_ecosystem_players
            WHERE {' AND '.join(clauses)}
            ORDER BY segment, name
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["regions"] = json.loads(item.pop("regions_json", None) or "[]")
        except json.JSONDecodeError:
            item["regions"] = []
        items.append(item)
    return {"items": items, "total": len(items)}


@router.get("/metrics/trends")
def subscription_metrics_trends(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text(
            """
            SELECT
                strftime('%Y-%m', COALESCE(created_at, started_at)) AS month_ref,
                plan_type,
                COUNT(DISTINCT user_id) AS active_subscribers,
                SUM(monthly_fee_cents) AS mrr_cents
            FROM customer_subscriptions
            WHERE status IN ('ACTIVE', 'TRIALING')
            GROUP BY 1, plan_type
            ORDER BY 1 DESC, plan_type
            LIMIT :lim
            """
            if db.bind.dialect.name == "sqlite"
            else """
            SELECT
                to_char(date_trunc('month', COALESCE(created_at, started_at)), 'YYYY-MM') AS month_ref,
                plan_type,
                COUNT(DISTINCT user_id) AS active_subscribers,
                SUM(monthly_fee_cents) AS mrr_cents
            FROM customer_subscriptions
            WHERE status IN ('ACTIVE', 'TRIALING')
            GROUP BY 1, plan_type
            ORDER BY 1 DESC, plan_type
            LIMIT :lim
            """
        ),
        {"lim": months * 8},
    ).mappings().all()
    items = []
    for r in rows:
        items.append(
            {
                "month_ref": str(r.get("month_ref") or ""),
                "plan_type": str(r.get("plan_type") or ""),
                "active_subscribers": int(r.get("active_subscribers") or 0),
                "mrr_cents": int(r.get("mrr_cents") or 0),
            }
        )
    return {"ok": True, "items": items, "total": len(items)}


@router.get("/subscriptions/{subscription_id}/360")
def subscription_360(subscription_id: str, db: Session = Depends(get_db)):
    sub_row = db.execute(
        text(
            """
            SELECT id, user_id, plan_type, status, monthly_fee_cents,
                   free_shipping, priority_shelf, exclusive_deals,
                   billing_cycle, cancel_at_period_end,
                   trial_start, trial_end, current_period_start, current_period_end,
                   next_billing_at, cancelled_at, payment_method_id, partner_code,
                   created_at, updated_at
            FROM customer_subscriptions WHERE id = :id
            """
        ),
        {"id": subscription_id},
    ).mappings().first()
    if not sub_row:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": subscription_id})

    benefits = db.execute(
        text(
            """
            SELECT id, usage_month, benefit_type, usage_count, usage_limit
            FROM subscription_benefits_usage WHERE subscription_id = :id ORDER BY usage_month DESC
            """
        ),
        {"id": subscription_id},
    ).mappings().all()
    usage = db.execute(
        text(
            """
            SELECT id, usage_month, orders_count, free_shipping_used, savings_cents
            FROM subscription_usage WHERE subscription_id = :id ORDER BY usage_month DESC
            """
        ),
        {"id": subscription_id},
    ).mappings().all()
    events = db.execute(
        text(
            """
            SELECT id, event_type, actor_id, payload_json, created_at
            FROM subscription_events WHERE subscription_id = :id ORDER BY created_at DESC LIMIT 50
            """
        ),
        {"id": subscription_id},
    ).mappings().all()
    invoices = db.execute(
        text(
            """
            SELECT id, period_start, period_end, amount_cents, currency, status, paid_at, created_at
            FROM subscription_invoices WHERE subscription_id = :id ORDER BY period_start DESC LIMIT 24
            """
        ),
        {"id": subscription_id},
    ).mappings().all()
    dunning = db.execute(
        text(
            """
            SELECT id, stage, status, amount_due_cents, opened_at, resolved_at
            FROM subscription_dunning_cases WHERE subscription_id = :id ORDER BY opened_at DESC
            """
        ),
        {"id": subscription_id},
    ).mappings().all()
    entitlements = db.execute(
        text(
            """
            SELECT player_code, player_name, player_type, region_codes_json, enabled, priority_level
            FROM subscription_plan_entitlements
            WHERE plan_code = :code AND enabled = TRUE
            ORDER BY priority_level DESC
            """
        ),
        {"code": str(sub_row["plan_type"])},
    ).mappings().all()

    def _evt(e: dict[str, Any]) -> dict[str, Any]:
        out = dict(e)
        out["created_at"] = _to_iso(out.get("created_at"))
        try:
            out["payload"] = json.loads(out.pop("payload_json", None) or "{}")
        except json.JSONDecodeError:
            out["payload"] = {}
        return out

    return {
        "ok": True,
        "subscription": _sub_out(dict(sub_row)).model_dump(),
        "benefits_usage": [dict(b) for b in benefits],
        "usage": [dict(u) for u in usage],
        "events": [_evt(dict(e)) for e in events],
        "invoices": [
            {**dict(i), "period_start": _to_iso(i.get("period_start")), "period_end": _to_iso(i.get("period_end"))}
            for i in invoices
        ],
        "dunning_cases": [dict(d) for d in dunning],
        "plan_entitlements": [
            {
                **dict(ent),
                "region_codes": json.loads(ent.get("region_codes_json") or "[]"),
            }
            for ent in entitlements
        ],
    }


@router.get("/events")
def list_subscription_events(
    subscription_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {"lim": limit}
    if subscription_id:
        clauses.append("subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    if event_type:
        clauses.append("event_type = :et")
        params["et"] = event_type.strip()
    rows = db.execute(
        text(
            f"""
            SELECT id, subscription_id, event_type, actor_id, payload_json, created_at
            FROM subscription_events
            WHERE {' AND '.join(clauses)}
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        item["created_at"] = _to_iso(item.get("created_at"))
        try:
            item["payload"] = json.loads(item.pop("payload_json", None) or "{}")
        except json.JSONDecodeError:
            item["payload"] = {}
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/events")
def create_subscription_event(body: SubscriptionEventIn, db: Session = Depends(get_db)):
    exists = db.execute(
        text("SELECT 1 FROM customer_subscriptions WHERE id = :id LIMIT 1"),
        {"id": body.subscription_id},
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": body.subscription_id})
    eid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_events (id, subscription_id, event_type, actor_id, payload_json, created_at)
            VALUES (:id, :sid, :et, :actor, :payload, :now)
            """
        ),
        {
            "id": eid,
            "sid": body.subscription_id,
            "et": body.event_type.strip(),
            "actor": body.actor_id,
            "payload": json.dumps(body.payload_json or {}),
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": eid}


@router.get("/invoices")
def list_subscription_invoices(
    subscription_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if subscription_id:
        clauses.append("subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    if status:
        clauses.append("status = :st")
        params["st"] = status.strip().upper()
    rows = db.execute(
        text(
            f"""
            SELECT id, subscription_id, period_start, period_end, amount_cents, currency,
                   status, payment_ref, paid_at, created_at
            FROM subscription_invoices
            WHERE {' AND '.join(clauses)}
            ORDER BY period_start DESC
            LIMIT 500
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        item["period_start"] = _to_iso(item.get("period_start"))
        item["period_end"] = _to_iso(item.get("period_end"))
        item["paid_at"] = _to_iso(item["paid_at"]) if item.get("paid_at") else None
        item["created_at"] = _to_iso(item.get("created_at"))
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/invoices/generate")
def generate_subscription_invoice(body: InvoiceGenerateIn, db: Session = Depends(get_db)):
    sub = db.execute(
        text(
            """
            SELECT id, monthly_fee_cents, current_period_start, current_period_end, status
            FROM customer_subscriptions WHERE id = :id
            """
        ),
        {"id": body.subscription_id},
    ).mappings().first()
    if not sub:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": body.subscription_id})
    now = _utc_now()
    iid = str(uuid.uuid4())
    amount = body.amount_cents if body.amount_cents is not None else int(sub["monthly_fee_cents"])
    period_start = sub.get("current_period_start") or now
    period_end = sub.get("current_period_end") or now
    db.execute(
        text(
            """
            INSERT INTO subscription_invoices (
                id, subscription_id, period_start, period_end, amount_cents, currency,
                status, created_at, updated_at
            ) VALUES (:id, :sid, :ps, :pe, :amt, 'BRL', 'OPEN', :now, :now)
            """
        ),
        {"id": iid, "sid": body.subscription_id, "ps": period_start, "pe": period_end, "amt": amount, "now": now},
    )
    db.execute(
        text(
            """
            INSERT INTO subscription_events (id, subscription_id, event_type, payload_json, created_at)
            VALUES (:id, :sid, 'INVOICE_GENERATED', :payload, :now)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "sid": body.subscription_id,
            "payload": json.dumps({"invoice_id": iid, "amount_cents": amount}),
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "invoice_id": iid, "amount_cents": amount}


@router.post("/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: str, payment_ref: Optional[str] = Query(None), db: Session = Depends(get_db)):
    now = _utc_now()
    res = db.execute(
        text(
            """
            UPDATE subscription_invoices
            SET status = 'PAID', paid_at = :now, payment_ref = :ref, updated_at = :now
            WHERE id = :id
            """
        ),
        {"id": invoice_id, "now": now, "ref": payment_ref},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "INVOICE_NOT_FOUND", "message": invoice_id})
    return {"ok": True, "id": invoice_id}


@router.get("/entitlements")
def list_plan_entitlements(
    plan_code: Optional[str] = Query(None),
    player_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if plan_code:
        clauses.append("plan_code = :pc")
        params["pc"] = plan_code.strip().upper()
    if player_type:
        clauses.append("player_type = :pt")
        params["pt"] = player_type.strip().upper()
    rows = db.execute(
        text(
            f"""
            SELECT id, plan_code, player_code, player_name, player_type,
                   region_codes_json, enabled, priority_level, created_at, updated_at
            FROM subscription_plan_entitlements
            WHERE {' AND '.join(clauses)}
            ORDER BY plan_code, priority_level DESC, player_code
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["region_codes"] = json.loads(item.pop("region_codes_json", None) or "[]")
        except json.JSONDecodeError:
            item["region_codes"] = []
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/entitlements")
def upsert_plan_entitlement(body: EntitlementIn, db: Session = Depends(get_db)):
    now = _utc_now()
    code = body.plan_code.strip().upper()
    player = body.player_code.strip().lower()
    existing = db.execute(
        text("SELECT id FROM subscription_plan_entitlements WHERE plan_code = :pc AND player_code = :pl LIMIT 1"),
        {"pc": code, "pl": player},
    ).mappings().first()
    regions = json.dumps(body.region_codes or [])
    if existing:
        db.execute(
            text(
                """
                UPDATE subscription_plan_entitlements
                SET player_name = :name, player_type = :ptype, region_codes_json = :regions,
                    enabled = :enabled, priority_level = :prio, updated_at = :now
                WHERE id = :id
                """
            ),
            {
                "id": existing["id"],
                "name": body.player_name,
                "ptype": body.player_type,
                "regions": regions,
                "enabled": body.enabled,
                "prio": body.priority_level,
                "now": now,
            },
        )
        eid = str(existing["id"])
    else:
        eid = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO subscription_plan_entitlements (
                    id, plan_code, player_code, player_name, player_type,
                    region_codes_json, enabled, priority_level, created_at, updated_at
                ) VALUES (:id, :pc, :pl, :name, :ptype, :regions, :enabled, :prio, :now, :now)
                """
            ),
            {
                "id": eid,
                "pc": code,
                "pl": player,
                "name": body.player_name,
                "ptype": body.player_type,
                "regions": regions,
                "enabled": body.enabled,
                "prio": body.priority_level,
                "now": now,
            },
        )
    db.commit()
    return {"ok": True, "id": eid}


@router.get("/partner-programs")
def list_partner_programs(
    partner_type: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if partner_type:
        clauses.append("partner_type = :pt")
        params["pt"] = partner_type.strip().upper()
    if active_only:
        clauses.append("active = TRUE")
    rows = db.execute(
        text(
            f"""
            SELECT id, partner_code, partner_name, partner_type, default_plan_code,
                   revenue_share_pct, countries_json, kyb_status, webhook_enabled, active,
                   created_at, updated_at
            FROM subscription_partner_programs
            WHERE {' AND '.join(clauses)}
            ORDER BY partner_name
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        try:
            item["countries"] = json.loads(item.pop("countries_json", None) or "[]")
        except json.JSONDecodeError:
            item["countries"] = []
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/partner-programs")
def create_partner_program(body: PartnerProgramIn, db: Session = Depends(get_db)):
    code = body.partner_code.strip().lower()
    exists = db.execute(
        text("SELECT 1 FROM subscription_partner_programs WHERE partner_code = :c LIMIT 1"),
        {"c": code},
    ).scalar()
    if exists:
        raise HTTPException(status_code=409, detail={"type": "PARTNER_EXISTS", "message": code})
    pid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_partner_programs (
                id, partner_code, partner_name, partner_type, default_plan_code,
                revenue_share_pct, countries_json, kyb_status, active, created_at, updated_at
            ) VALUES (
                :id, :code, :name, :ptype, :plan, :rev, :countries, :kyb, :active, :now, :now
            )
            """
        ),
        {
            "id": pid,
            "code": code,
            "name": body.partner_name,
            "ptype": body.partner_type,
            "plan": body.default_plan_code,
            "rev": body.revenue_share_pct,
            "countries": json.dumps(body.countries or []),
            "kyb": body.kyb_status,
            "active": body.active,
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": pid, "partner_code": code}


@router.get("/dunning")
def list_dunning_cases(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("status = :st")
        params["st"] = status.strip().upper()
    rows = db.execute(
        text(
            f"""
            SELECT d.id, d.subscription_id, d.stage, d.status, d.amount_due_cents,
                   d.opened_at, d.resolved_at, d.resolution_note,
                   cs.user_id, cs.plan_type, cs.partner_code
            FROM subscription_dunning_cases d
            JOIN customer_subscriptions cs ON cs.id = d.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY d.opened_at DESC
            LIMIT 200
            """
        ),
        params,
    ).mappings().all()
    items = [dict(r) for r in rows]
    return {"items": items, "total": len(items)}


@router.post("/dunning/{case_id}/resolve")
def resolve_dunning_case(case_id: str, body: DunningResolveIn, db: Session = Depends(get_db)):
    now = _utc_now()
    row = db.execute(
        text("SELECT subscription_id FROM subscription_dunning_cases WHERE id = :id"),
        {"id": case_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "DUNNING_NOT_FOUND", "message": case_id})
    db.execute(
        text(
            """
            UPDATE subscription_dunning_cases
            SET status = 'RESOLVED', resolved_at = :now, resolution_note = :note, updated_at = :now
            WHERE id = :id
            """
        ),
        {"id": case_id, "now": now, "note": body.resolution_note},
    )
    db.execute(
        text(
            """
            UPDATE customer_subscriptions SET status = 'ACTIVE', updated_at = :now WHERE id = :sid
            """
        ),
        {"sid": row["subscription_id"], "now": now},
    )
    db.commit()
    return {"ok": True, "id": case_id}


@router.get("/webhook-deliveries")
def list_webhook_deliveries(
    endpoint_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {"lim": limit}
    if endpoint_id:
        clauses.append("endpoint_id = :eid")
        params["eid"] = endpoint_id.strip()
    rows = db.execute(
        text(
            f"""
            SELECT id, endpoint_id, subscription_id, event_type, http_status,
                   attempt_no, error_message, delivered_at
            FROM subscription_webhook_deliveries
            WHERE {' AND '.join(clauses)}
            ORDER BY delivered_at DESC
            LIMIT :lim
            """
        ),
        params,
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        item["delivered_at"] = _to_iso(item.get("delivered_at"))
        items.append(item)
    return {"items": items, "total": len(items)}


@router.post("/webhook-deliveries/simulate")
def simulate_webhook_delivery(
    partner_code: str = Query(...),
    event_type: str = Query("subscription.renewed"),
    subscription_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    endpoint = db.execute(
        text(
            """
            SELECT id, url FROM subscription_webhook_endpoints
            WHERE partner_code = :p AND active = TRUE LIMIT 1
            """
        ),
        {"p": partner_code.strip()},
    ).mappings().first()
    if not endpoint:
        raise HTTPException(status_code=404, detail={"type": "WEBHOOK_NOT_FOUND", "message": partner_code})
    did = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_webhook_deliveries (
                id, endpoint_id, subscription_id, event_type, http_status,
                attempt_no, error_message, payload_json, delivered_at
            ) VALUES (:id, :eid, :sid, :et, 200, 1, NULL, :payload, :now)
            """
        ),
        {
            "id": did,
            "eid": endpoint["id"],
            "sid": subscription_id,
            "et": event_type,
            "payload": json.dumps({"simulated": True, "partner_code": partner_code}),
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "delivery_id": did, "endpoint_url": endpoint["url"], "http_status": 200}
