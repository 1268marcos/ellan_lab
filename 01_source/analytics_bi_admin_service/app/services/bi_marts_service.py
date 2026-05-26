from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.bi_marts import CompanyMrrTrend, LockerPnl, PartnerRevenueMonthly
from app.schemas.bi_core import CompanyMrrTrendOut, LockerPnlOut, MartListOut, PartnerRevenueMonthlyOut


def list_marts(db: Session, limit: int = 50) -> MartListOut:
    mrr = db.query(CompanyMrrTrend).order_by(CompanyMrrTrend.month_ref.desc()).limit(limit).all()
    pnl = db.query(LockerPnl).order_by(LockerPnl.month_ref.desc()).limit(limit).all()
    rev = db.query(PartnerRevenueMonthly).order_by(PartnerRevenueMonthly.month_ref.desc()).limit(limit).all()
    return MartListOut(
        mrr=[CompanyMrrTrendOut.model_validate(r) for r in mrr],
        locker_pnl=[LockerPnlOut.model_validate(r) for r in pnl],
        partner_revenue=[PartnerRevenueMonthlyOut.model_validate(r) for r in rev],
    )


def upsert_mrr(
    db: Session,
    month_ref: date,
    currency: str,
    mrr_cents: float,
    active_partner_count: int,
    active_locker_count: int,
) -> CompanyMrrTrend:
    row = (
        db.query(CompanyMrrTrend)
        .filter(CompanyMrrTrend.month_ref == month_ref, CompanyMrrTrend.currency == currency)
        .first()
    )
    now = datetime.now(timezone.utc)
    if row:
        row.mrr_cents = mrr_cents
        row.active_partner_count = active_partner_count
        row.active_locker_count = active_locker_count
        row.updated_at = now
    else:
        row = CompanyMrrTrend(
            month_ref=month_ref,
            currency=currency,
            mrr_cents=mrr_cents,
            active_partner_count=active_partner_count,
            active_locker_count=active_locker_count,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row
