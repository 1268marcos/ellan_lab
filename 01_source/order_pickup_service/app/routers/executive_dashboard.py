"""Dashboard executivo (CEO): KPIs, finanças, expansão e parceiros."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import extract, func, text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.allocation import Allocation, AllocationState
from app.models.locker import Locker
from app.models.order import Order, OrderStatus
from app.models.partner_performance_metric import PartnerPerformanceMetric
from app.models.partner_settlement import PartnerSettlementBatch
from app.services.auth_service import get_user_by_session_token
from app.services.user_roles_service import user_has_any_role

router = APIRouter(
    prefix="/api/v1/executive",
    tags=["Executive Dashboard"],
)


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "", 1).strip()
    return token or None


def _resolve_partner_by_raw_api_key(db: Session, raw_key: str) -> dict[str, Any] | None:
    if not raw_key:
        return None
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    pid_row = db.execute(
        text(
            """
            SELECT partner_id
            FROM partner_api_keys
            WHERE key_hash = :key_hash
              AND revoked_at IS NULL
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"key_hash": key_hash},
    ).mappings().first()
    if not pid_row:
        return None
    partner_id = str(pid_row["partner_id"])
    prow = db.execute(
        text(
            """
            SELECT id, name, code, tier, status
            FROM ecommerce_partners
            WHERE id = :id
            LIMIT 1
            """
        ),
        {"id": partner_id},
    ).mappings().first()
    return dict(prow) if prow else None


def _partner_may_access_executive_dashboard(row: dict[str, Any]) -> bool:
    pid = str(row.get("id") or "").lower()
    code = str(row.get("code") or "").upper()
    tier = str(row.get("tier") or "").upper()
    if "ceo" in pid:
        return True
    if code in {"CEO", "ELLAN_CEO"}:
        return True
    return tier == "EXECUTIVE"


def require_ceo_access(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> None:
    """Permite usuários com role `ceo` (sessão Bearer) ou parceiro executivo (API key)."""
    bearer = _bearer_token(authorization)
    raw_key = (x_api_key or "").strip() or (bearer or "").strip()

    if bearer:
        user = get_user_by_session_token(db, raw_token=bearer)
        if user is not None and user.is_active:
            if user_has_any_role(db, user_id=user.id, allowed_roles={"ceo"}):
                return

    if raw_key:
        prow = _resolve_partner_by_raw_api_key(db, raw_key)
        if prow and _partner_may_access_executive_dashboard(prow):
            return

    raise HTTPException(
        status_code=403,
        detail={
            "type": "CEO_ACCESS_REQUIRED",
            "message": "Acesso restrito: role ceo ou parceiro executivo (tier EXECUTIVE / code CEO).",
        },
    )


def _month_start_utc(d: datetime.date) -> datetime:
    return datetime(d.year, d.month, 1, tzinfo=timezone.utc)


def _format_brl_from_cents(cents: int | float) -> str:
    v = float(cents) / 100.0
    return f"R$ {v:,.2f}"


@router.get("/kpis/globals", dependencies=[Depends(require_ceo_access)])
async def get_global_kpis(db: Session = Depends(get_db)) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    today = now.date()
    month_start = _month_start_utc(today)

    revenue_row = (
        db.query(func.coalesce(func.sum(Order.amount_cents), 0).label("cents"))
        .filter(
            Order.paid_at.isnot(None),
            Order.paid_at >= month_start,
            Order.status.notin_(
                [
                    OrderStatus.CANCELLED,
                    OrderStatus.REFUNDED,
                    OrderStatus.FAILED,
                    OrderStatus.PAYMENT_PENDING,
                ]
            ),
        )
        .one()
    )
    total_revenue_mtd_cents = int(revenue_row.cents or 0)
    total_revenue_mtd = total_revenue_mtd_cents / 100.0

    total_capacity = db.query(func.coalesce(func.sum(Locker.slots_count), 0)).scalar() or 0
    occupied_slots = (
        db.query(func.count(Allocation.id))
        .filter(
            Allocation.state.in_(
                [
                    AllocationState.RESERVED_PAID_PENDING_PICKUP,
                    AllocationState.OPENED_FOR_PICKUP,
                ]
            )
        )
        .scalar()
        or 0
    )
    occupancy_rate = (occupied_slots / total_capacity * 100) if total_capacity else 0.0

    nps = 68.5
    critical_incidents = (
        db.query(func.count(Allocation.id)).filter(Allocation.state == AllocationState.ERROR).scalar() or 0
    )
    expanding_lockers = db.query(func.count(Locker.id)).filter(Locker.active.is_(False)).scalar() or 0

    return {
        "total_revenue_mtd": total_revenue_mtd,
        "total_revenue_mtd_formatted": _format_brl_from_cents(total_revenue_mtd_cents),
        "occupancy_rate": round(occupancy_rate, 1),
        "nps": nps,
        "critical_incidents": critical_incidents,
        "expanding_lockers": expanding_lockers,
        "as_of": now.isoformat(),
    }


@router.get("/finance/mrr", dependencies=[Depends(require_ceo_access)])
async def get_mrr(db: Session = Depends(get_db)) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    month_start = _month_start_utc(now.date())

    rows = (
        db.query(Locker.region, func.coalesce(func.sum(Order.amount_cents), 0).label("cents"))
        .join(Locker, Order.totem_id == Locker.id)
        .filter(
            Order.paid_at.isnot(None),
            Order.paid_at >= month_start,
            Order.status.notin_(
                [
                    OrderStatus.CANCELLED,
                    OrderStatus.REFUNDED,
                    OrderStatus.FAILED,
                ]
            ),
        )
        .group_by(Locker.region)
        .all()
    )
    by_region_cents = [(r.region, int(r.cents or 0)) for r in rows]
    total_cents = sum(c for _, c in by_region_cents)
    total_mrr = total_cents / 100.0

    return {
        "total_mrr": total_mrr,
        "total_mrr_formatted": _format_brl_from_cents(total_cents),
        "by_region": [
            {
                "region": region,
                "mrr": cents / 100.0,
                "percentage": round((cents / total_cents * 100), 2) if total_cents > 0 else 0.0,
            }
            for region, cents in sorted(by_region_cents, key=lambda x: x[1], reverse=True)
        ],
    }


@router.get("/finance/forecast", dependencies=[Depends(require_ceo_access)])
async def get_forecast(db: Session = Depends(get_db)) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    six_months_ago = now - timedelta(days=180)

    y_lab = extract("year", Order.paid_at).label("y")
    m_lab = extract("month", Order.paid_at).label("m")
    rows = (
        db.query(
            y_lab,
            m_lab,
            func.coalesce(func.sum(Order.amount_cents), 0).label("cents"),
        )
        .filter(
            Order.paid_at.isnot(None),
            Order.paid_at >= six_months_ago,
            Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
        )
        .group_by(y_lab, m_lab)
        .order_by(y_lab, m_lab)
        .all()
    )

    historical: list[dict[str, Any]] = []
    last_revenue = 10000.0
    for row in rows:
        y, m = int(row.y), int(row.m)
        cents = int(row.cents or 0)
        rev = cents / 100.0
        historical.append({"month": f"{y:04d}-{m:02d}", "revenue": rev})
        last_revenue = rev

    if not historical:
        last_revenue = 10000.0

    growth_rate = 0.05
    forecast: list[dict[str, Any]] = []
    for i in range(1, 4):
        anchor = now + timedelta(days=30 * i)
        forecast.append(
            {
                "month": anchor.strftime("%Y-%m"),
                "forecast_revenue": round(last_revenue * ((1 + growth_rate) ** i), 2),
            }
        )

    return {"historical": historical, "forecast": forecast}


def _locker_pipeline_stage(lk: Locker) -> str | None:
    if not lk.metadata_json:
        return None
    try:
        meta = json.loads(lk.metadata_json)
        raw = meta.get("pipeline_stage") or meta.get("status_pipeline") or ""
        s = str(raw).strip().lower()
        return s or None
    except (json.JSONDecodeError, TypeError):
        return None


@router.get("/expansion/pipeline", dependencies=[Depends(require_ceo_access)])
async def get_expansion_pipeline(db: Session = Depends(get_db)) -> dict[str, Any]:
    lockers = db.query(Locker).all()
    pipeline_lockers: list[Locker] = []
    for lk in lockers:
        stage = _locker_pipeline_stage(lk)
        if stage in {"proposed", "analysis"} or not lk.active:
            pipeline_lockers.append(lk)

    pending_approvals = sum(1 for lk in pipeline_lockers if _locker_pipeline_stage(lk) == "analysis")

    roi_calculations: list[dict[str, Any]] = []
    revenue_by_locker = (
        db.query(Order.totem_id, func.coalesce(func.sum(Order.amount_cents), 0).label("cents"))
        .filter(
            Order.paid_at.isnot(None),
            Order.created_at >= datetime.now(timezone.utc) - timedelta(days=365),
            Order.status.notin_([OrderStatus.CANCELLED, OrderStatus.REFUNDED]),
        )
        .group_by(Order.totem_id)
        .all()
    )
    rev_map = {str(r.totem_id): int(r.cents or 0) for r in revenue_by_locker}

    for lk in lockers:
        cents = rev_map.get(str(lk.id), 0)
        installation_cost = None
        if lk.metadata_json:
            try:
                meta = json.loads(lk.metadata_json)
                installation_cost = meta.get("installation_cost")
                if installation_cost is None:
                    installation_cost = meta.get("installation_cost_cents")
                    if installation_cost is not None:
                        installation_cost = float(installation_cost) / 100.0
            except (json.JSONDecodeError, TypeError):
                installation_cost = None
        cost_f = float(installation_cost) if installation_cost not in (None, "", 0) else 0.0
        annual_revenue = (cents / 100.0) * 12
        roi_percent = ((annual_revenue / cost_f) * 100) if cost_f > 0 else 0.0
        if cost_f > 0 or annual_revenue > 0:
            roi_calculations.append(
                {
                    "city": lk.city or "",
                    "region": lk.region,
                    "annual_revenue": round(annual_revenue, 2),
                    "installation_cost": round(cost_f, 2),
                    "roi_percent": round(roi_percent, 1),
                }
            )

    roi_calculations.sort(key=lambda x: x["roi_percent"], reverse=True)

    return {
        "pipeline_count": len(pipeline_lockers),
        "pending_approvals": min(pending_approvals, len(pipeline_lockers)),
        "roi_by_location": roi_calculations[:10],
    }


@router.get("/partners/top", dependencies=[Depends(require_ceo_access)])
async def get_top_partners(
    db: Session = Depends(get_db),
    limit: int = 10,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    month_start = _month_start_utc(now.date())

    rows = (
        db.query(
            PartnerSettlementBatch.partner_id,
            func.coalesce(func.sum(PartnerSettlementBatch.net_amount_cents), 0).label("cents"),
        )
        .filter(
            PartnerSettlementBatch.status == "PAID",
            PartnerSettlementBatch.settled_at.isnot(None),
            PartnerSettlementBatch.settled_at >= month_start,
        )
        .group_by(PartnerSettlementBatch.partner_id)
        .order_by(func.sum(PartnerSettlementBatch.net_amount_cents).desc())
        .limit(limit)
        .all()
    )

    top_partners: list[dict[str, Any]] = []
    for row in rows:
        name_row = db.execute(
            text("SELECT name FROM ecommerce_partners WHERE id = :id LIMIT 1"),
            {"id": str(row.partner_id)},
        ).mappings().first()
        name = str(name_row["name"]) if name_row else str(row.partner_id)
        cents = int(row.cents or 0)
        top_partners.append({"name": name, "total_revenue": cents / 100.0})

    total_partners = db.execute(text("SELECT COUNT(*) AS c FROM ecommerce_partners")).mappings().first()
    churned = db.execute(
        text("SELECT COUNT(*) AS c FROM ecommerce_partners WHERE UPPER(COALESCE(status,'')) LIKE '%CHURN%'")
    ).mappings().first()
    tp = int((total_partners or {}).get("c") or 0)
    ch = int((churned or {}).get("c") or 0)
    churn_rate = (ch / tp * 100) if tp else 0.0

    period_month = now.strftime("%Y-%m")
    sla_row = (
        db.query(func.avg(PartnerPerformanceMetric.sla_compliance_pct))
        .filter(PartnerPerformanceMetric.period_month == period_month)
        .scalar()
    )
    sla_compliance = float(sla_row) if sla_row is not None else 0.0

    return {
        "top_partners": top_partners,
        "partner_churn_rate": round(churn_rate, 1),
        "sla_compliance": round(sla_compliance, 1),
        "as_of": now.isoformat(),
    }
