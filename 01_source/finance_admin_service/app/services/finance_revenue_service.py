from __future__ import annotations

import json
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.finance import PartnerBillingCycle, PartnerB2bInvoice
from app.models.finance_revenue import PartnerRevenueRecognitionEntry, PartnerRevenueSchedule
from app.services.billing_fiscal_client import (
    BillingFiscalClientError,
    is_fiscal_live_enabled,
    recompute_fiscal_revenue_recognition,
)
from app.services.crypto_util import new_id
from app.services.finance_audit_service import log_audit


def create_schedule_from_cycle(db: Session, cycle_id: str, *, method: str = "STRAIGHT_LINE") -> PartnerRevenueSchedule:
    cycle = db.get(PartnerBillingCycle, cycle_id)
    if not cycle:
        raise HTTPException(status_code=404, detail="Billing cycle not found")
    if cycle.status != "CLOSED":
        raise HTTPException(status_code=409, detail="Cycle must be CLOSED to create revenue schedule")

    existing = (
        db.query(PartnerRevenueSchedule)
        .filter(PartnerRevenueSchedule.source_type == "BILLING_CYCLE", PartnerRevenueSchedule.source_id == cycle_id)
        .first()
    )
    if existing:
        return existing

    total = int(cycle.total_amount_cents or 0)
    row = PartnerRevenueSchedule(
        id=new_id(),
        partner_id=cycle.partner_id,
        source_type="BILLING_CYCLE",
        source_id=cycle_id,
        total_cents=total,
        recognized_cents=0,
        deferred_cents=total,
        recognition_method=method,
        period_start=cycle.period_start,
        period_end=cycle.period_end,
        currency=cycle.currency,
        status="ACTIVE",
    )
    db.add(row)
    log_audit(db, action="CREATE_REVENUE_SCHEDULE", entity_type="billing_cycle", entity_id=cycle_id, after={"total_cents": total})
    db.commit()
    db.refresh(row)
    return row


def run_straight_line_recognition(db: Session, *, through_date: date | None = None) -> dict[str, int]:
    """Gera entradas diárias proporcionais (diferimento) até through_date."""
    target = through_date or date.today()
    schedules = db.query(PartnerRevenueSchedule).filter(PartnerRevenueSchedule.status == "ACTIVE").all()
    entries_created = 0
    schedules_updated = 0

    for sched in schedules:
        days = (sched.period_end - sched.period_start).days + 1
        if days <= 0:
            days = 1
        daily = int(sched.total_cents // days)
        remainder = int(sched.total_cents) - daily * days

        current = sched.period_start
        recognized_total = 0
        day_index = 0
        while current <= sched.period_end and current <= target:
            amount = daily + (remainder if day_index == days - 1 else 0)
            exists = (
                db.query(PartnerRevenueRecognitionEntry)
                .filter(
                    PartnerRevenueRecognitionEntry.schedule_id == sched.id,
                    PartnerRevenueRecognitionEntry.recognition_date == current,
                )
                .first()
            )
            if not exists and amount > 0:
                db.add(
                    PartnerRevenueRecognitionEntry(
                        id=new_id(),
                        schedule_id=sched.id,
                        partner_id=sched.partner_id,
                        recognition_date=current,
                        amount_cents=amount,
                        entry_status="RECOGNIZED",
                        fiscal_synced=False,
                    )
                )
                entries_created += 1
                recognized_total += amount
            current += timedelta(days=1)
            day_index += 1

        all_entries = (
            db.query(PartnerRevenueRecognitionEntry)
            .filter(PartnerRevenueRecognitionEntry.schedule_id == sched.id)
            .all()
        )
        rec_sum = sum(int(e.amount_cents) for e in all_entries)
        sched.recognized_cents = rec_sum
        sched.deferred_cents = max(0, int(sched.total_cents) - rec_sum)
        if sched.period_end <= target and sched.deferred_cents == 0:
            sched.status = "COMPLETED"
        schedules_updated += 1

    db.commit()
    return {"entries_created": entries_created, "schedules_updated": schedules_updated}


def sync_recognition_to_fiscal(db: Session, *, snapshot_date: date | None = None) -> dict:
    """Envia reconhecimento ao billing_fiscal (Timescale ellanlab_revenue_recognition)."""
    if not is_fiscal_live_enabled():
        return {"skipped": True, "reason": "billing_fiscal_live_disabled"}

    target = snapshot_date or date.today()
    try:
        fiscal_result = recompute_fiscal_revenue_recognition(snapshot_date=target)
    except BillingFiscalClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    pending = (
        db.query(PartnerRevenueRecognitionEntry)
        .filter(
            PartnerRevenueRecognitionEntry.recognition_date == target,
            PartnerRevenueRecognitionEntry.fiscal_synced.is_(False),
        )
        .all()
    )
    for row in pending:
        row.fiscal_synced = True
    db.commit()
    return {
        "fiscal_synced": len(pending),
        "fiscal_service": fiscal_result,
    }


def list_schedules(db: Session, partner_id: str | None = None) -> list[PartnerRevenueSchedule]:
    q = db.query(PartnerRevenueSchedule).order_by(PartnerRevenueSchedule.period_start.desc())
    if partner_id:
        q = q.filter(PartnerRevenueSchedule.partner_id == partner_id)
    return q.all()


def list_entries(db: Session, *, schedule_id: str | None = None, partner_id: str | None = None) -> list[PartnerRevenueRecognitionEntry]:
    q = db.query(PartnerRevenueRecognitionEntry).order_by(PartnerRevenueRecognitionEntry.recognition_date.desc())
    if schedule_id:
        q = q.filter(PartnerRevenueRecognitionEntry.schedule_id == schedule_id)
    if partner_id:
        q = q.filter(PartnerRevenueRecognitionEntry.partner_id == partner_id)
    return q.limit(500).all()
