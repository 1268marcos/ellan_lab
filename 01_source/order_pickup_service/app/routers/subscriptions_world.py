"""Funcionalidades mundiais: preços regionais, add-ons, pausas, SLA, settlements, retenção, LGPD."""
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
from app.core.subscriptions_world_seed import seed_subscriptions_world
from app.routers.subscriptions_ops import _to_iso, _utc_now

router = APIRouter(tags=["subscriptions-world"])


class AttachAddonIn(BaseModel):
    subscription_id: str
    addon_code: str


class PauseScheduleIn(BaseModel):
    subscription_id: str
    pause_start: datetime
    pause_end: datetime
    reason: str = Field(default="USER_REQUEST", max_length=64)


class RetentionOfferIn(BaseModel):
    subscription_id: str
    offer_code: str = "STAY20"
    discount_pct: float = Field(default=20, ge=0, le=100)
    bonus_months: int = Field(default=1, ge=0, le=3)
    valid_days: int = Field(default=14, ge=1, le=90)


class ConsentRecordIn(BaseModel):
    user_id: str
    consent_type: str = Field(..., pattern="^(TERMS_OF_SERVICE|PRIVACY_POLICY|MARKETING_OPT_IN)$")
    policy_version: str = Field(..., min_length=1, max_length=16)
    locale: str = "pt-BR"


@router.post("/world/seed")
def world_seed(db: Session = Depends(get_db)):
    return {"ok": True, "seeded": seed_subscriptions_world(db)}


@router.get("/world/summary")
def world_summary(db: Session = Depends(get_db)):
    def _count(table: str) -> int:
        return int(db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0)

    return {
        "ok": True,
        "counts": {
            "regional_prices": _count("subscription_regional_prices"),
            "plan_addons": _count("subscription_plan_addons"),
            "active_addons": _count("subscription_active_addons"),
            "pause_periods": _count("subscription_pause_periods"),
            "sla_targets": _count("subscription_sla_targets"),
            "settlements_open": int(
                db.execute(
                    text("SELECT COUNT(*) FROM subscription_partner_settlements WHERE status = 'OPEN'")
                ).scalar()
                or 0
            ),
            "retention_offers": _count("subscription_retention_offers"),
            "consent_records": _count("subscription_consent_records"),
        },
        "regions": ["BR", "PT", "EU", "UK", "US"],
        "currencies": ["BRL", "EUR", "GBP", "USD"],
    }


@router.get("/world/regional-prices")
def list_regional_prices(
    plan_code: Optional[str] = Query(None),
    region_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["active = TRUE"]
    params: dict[str, Any] = {}
    if plan_code:
        clauses.append("plan_code = :plan")
        params["plan"] = plan_code.strip().upper()
    if region_code:
        clauses.append("region_code = :reg")
        params["reg"] = region_code.strip().upper()
    rows = db.execute(
        text(
            f"""
            SELECT plan_code, region_code, currency, monthly_fee_cents, yearly_fee_cents, tax_inclusive
            FROM subscription_regional_prices
            WHERE {' AND '.join(clauses)}
            ORDER BY plan_code, region_code
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.get("/world/addons/catalog")
def list_addon_catalog(active_only: bool = Query(True), db: Session = Depends(get_db)):
    clause = "active = TRUE" if active_only else "1=1"
    rows = db.execute(
        text(f"SELECT * FROM subscription_plan_addons WHERE {clause} ORDER BY addon_type, code")
    ).mappings().all()
    items = []
    for r in rows:
        item = dict(r)
        item["regions"] = json.loads(item.pop("regions_json", None) or "[]")
        items.append(item)
    return {"items": items, "total": len(items)}


@router.get("/world/addons/active")
def list_active_addons(
    subscription_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if subscription_id:
        clauses.append("a.subscription_id = :sid")
        params["sid"] = subscription_id.strip()
    rows = db.execute(
        text(
            f"""
            SELECT a.*, p.name AS addon_name, p.addon_type
            FROM subscription_active_addons a
            JOIN subscription_plan_addons p ON p.code = a.addon_code
            WHERE {' AND '.join(clauses)}
            ORDER BY a.started_at DESC
            LIMIT 200
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/world/addons/attach")
def attach_addon(body: AttachAddonIn, db: Session = Depends(get_db)):
    addon = db.execute(
        text("SELECT code, monthly_fee_cents, active FROM subscription_plan_addons WHERE code = :c LIMIT 1"),
        {"c": body.addon_code.strip().upper()},
    ).mappings().first()
    if not addon or not addon.get("active"):
        raise HTTPException(status_code=404, detail={"type": "ADDON_NOT_FOUND", "message": body.addon_code})
    sub = db.execute(
        text("SELECT id FROM customer_subscriptions WHERE id = :id LIMIT 1"),
        {"id": body.subscription_id.strip()},
    ).scalar()
    if not sub:
        raise HTTPException(status_code=404, detail={"type": "SUBSCRIPTION_NOT_FOUND", "message": body.subscription_id})
    now = _utc_now()
    sid = body.subscription_id.strip()
    code = body.addon_code.strip().upper()
    existing = db.execute(
        text(
            "SELECT id FROM subscription_active_addons WHERE subscription_id = :sid AND addon_code = :code LIMIT 1"
        ),
        {"sid": sid, "code": code},
    ).mappings().first()
    if existing:
        aid = str(existing["id"])
        db.execute(
            text(
                """
                UPDATE subscription_active_addons
                SET status = 'ACTIVE', monthly_fee_cents = :fee, started_at = :now, ended_at = NULL
                WHERE id = :id
                """
            ),
            {"id": aid, "fee": int(addon["monthly_fee_cents"]), "now": now},
        )
    else:
        aid = str(uuid.uuid4())
        db.execute(
            text(
                """
                INSERT INTO subscription_active_addons (
                    id, subscription_id, addon_code, status, monthly_fee_cents, started_at, created_at
                ) VALUES (:id, :sid, :code, 'ACTIVE', :fee, :now, :now)
                """
            ),
            {"id": aid, "sid": sid, "code": code, "fee": int(addon["monthly_fee_cents"]), "now": now},
        )
    db.commit()
    return {"ok": True, "id": aid}


@router.get("/world/pauses")
def list_pause_periods(
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
            SELECT p.*, cs.user_id, cs.plan_type
            FROM subscription_pause_periods p
            JOIN customer_subscriptions cs ON cs.id = p.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY p.pause_start DESC
            LIMIT 100
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/world/pauses")
def schedule_pause(body: PauseScheduleIn, db: Session = Depends(get_db)):
    if body.pause_end <= body.pause_start:
        raise HTTPException(status_code=422, detail={"type": "INVALID_PAUSE_RANGE", "message": "pause_end > pause_start"})
    pid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_pause_periods (
                id, subscription_id, pause_start, pause_end, reason, status, created_at
            ) VALUES (:id, :sid, :start, :end, :reason, 'SCHEDULED', :now)
            """
        ),
        {
            "id": pid,
            "sid": body.subscription_id.strip(),
            "start": body.pause_start,
            "end": body.pause_end,
            "reason": body.reason,
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": pid}


@router.get("/world/sla-targets")
def list_sla_targets(
    plan_code: Optional[str] = Query(None),
    region_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["active = TRUE"]
    params: dict[str, Any] = {}
    if plan_code:
        clauses.append("plan_code = :plan")
        params["plan"] = plan_code.strip().upper()
    if region_code:
        clauses.append("(region_code = :reg OR region_code IS NULL)")
        params["reg"] = region_code.strip().upper()
    rows = db.execute(
        text(
            f"""
            SELECT plan_code, region_code, metric_code, target_value, unit, description
            FROM subscription_sla_targets
            WHERE {' AND '.join(clauses)}
            ORDER BY plan_code, metric_code
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.get("/world/settlements")
def list_settlements(
    partner_code: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if partner_code:
        clauses.append("partner_code = :p")
        params["p"] = partner_code.strip().lower()
    if status:
        clauses.append("status = :st")
        params["st"] = status.strip().upper()
    rows = db.execute(
        text(
            f"""
            SELECT * FROM subscription_partner_settlements
            WHERE {' AND '.join(clauses)}
            ORDER BY period_month DESC, partner_code
            LIMIT 200
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/world/settlements/{settlement_id}/mark-paid")
def mark_settlement_paid(settlement_id: str, db: Session = Depends(get_db)):
    now = _utc_now()
    res = db.execute(
        text(
            """
            UPDATE subscription_partner_settlements
            SET status = 'PAID', paid_at = :now
            WHERE id = :id AND status = 'OPEN'
            """
        ),
        {"id": settlement_id, "now": now},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail={"type": "SETTLEMENT_NOT_FOUND", "message": settlement_id})
    return {"ok": True}


@router.get("/world/retention-offers")
def list_retention_offers(
    status: Optional[str] = Query("OFFERED"),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if status:
        clauses.append("r.status = :st")
        params["st"] = status.strip().upper()
    rows = db.execute(
        text(
            f"""
            SELECT r.*, cs.user_id, cs.plan_type
            FROM subscription_retention_offers r
            JOIN customer_subscriptions cs ON cs.id = r.subscription_id
            WHERE {' AND '.join(clauses)}
            ORDER BY r.valid_until
            LIMIT 100
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/world/retention-offers")
def issue_retention_offer(body: RetentionOfferIn, db: Session = Depends(get_db)):
    oid = str(uuid.uuid4())
    now = _utc_now()
    valid = now + timedelta(days=body.valid_days)
    db.execute(
        text(
            """
            INSERT INTO subscription_retention_offers (
                id, subscription_id, offer_code, discount_pct, bonus_months,
                valid_until, status, created_at
            ) VALUES (:id, :sid, :code, :disc, :bonus, :valid, 'OFFERED', :now)
            """
        ),
        {
            "id": oid,
            "sid": body.subscription_id.strip(),
            "code": body.offer_code,
            "disc": body.discount_pct,
            "bonus": body.bonus_months,
            "valid": valid,
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": oid, "valid_until": _to_iso(valid)}


@router.post("/world/retention-offers/{offer_id}/accept")
def accept_retention_offer(offer_id: str, db: Session = Depends(get_db)):
    now = _utc_now()
    row = db.execute(
        text(
            """
            SELECT subscription_id, discount_pct, bonus_months FROM subscription_retention_offers
            WHERE id = :id AND status = 'OFFERED' AND valid_until >= :now LIMIT 1
            """
        ),
        {"id": offer_id, "now": now},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail={"type": "OFFER_NOT_FOUND", "message": offer_id})
    db.execute(
        text(
            "UPDATE subscription_retention_offers SET status = 'ACCEPTED', accepted_at = :now WHERE id = :id"
        ),
        {"id": offer_id, "now": now},
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
    return {"ok": True, "subscription_id": str(row["subscription_id"]), "discount_pct": float(row["discount_pct"])}


@router.get("/world/consents")
def list_consent_records(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    clauses = ["1=1"]
    params: dict[str, Any] = {}
    if user_id:
        clauses.append("user_id = :u")
        params["u"] = user_id.strip()
    rows = db.execute(
        text(
            f"""
            SELECT user_id, consent_type, policy_version, locale, accepted_at
            FROM subscription_consent_records
            WHERE {' AND '.join(clauses)}
            ORDER BY accepted_at DESC
            LIMIT 200
            """
        ),
        params,
    ).mappings().all()
    return {"items": [dict(r) for r in rows], "total": len(rows)}


@router.post("/world/consents")
def record_consent(body: ConsentRecordIn, db: Session = Depends(get_db)):
    cid = str(uuid.uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO subscription_consent_records (
                id, user_id, consent_type, policy_version, locale, accepted_at, metadata_json
            ) VALUES (:id, :u, :ct, :ver, :loc, :now, '{}')
            ON CONFLICT (user_id, consent_type, policy_version) DO NOTHING
            """
        ),
        {
            "id": cid,
            "u": body.user_id.strip(),
            "ct": body.consent_type,
            "ver": body.policy_version,
            "loc": body.locale,
            "now": now,
        },
    )
    db.commit()
    return {"ok": True, "id": cid}
