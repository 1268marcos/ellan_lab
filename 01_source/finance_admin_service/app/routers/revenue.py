from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_revenue import (
    RevenueEntryListOut,
    RevenueEntryOut,
    RevenueRunOut,
    RevenueScheduleListOut,
    RevenueScheduleOut,
)
from app.services import finance_revenue_service as rev_svc

router = APIRouter(tags=["revenue-recognition"])


@router.get("/revenue-schedules", response_model=RevenueScheduleListOut)
def list_revenue_schedules(partner_id: str | None = Query(None), db: Session = Depends(get_db)) -> RevenueScheduleListOut:
    rows = rev_svc.list_schedules(db, partner_id)
    items = [RevenueScheduleOut.model_validate(r) for r in rows]
    return RevenueScheduleListOut(items=items, total=len(items))


@router.post("/revenue-schedules/from-cycle/{cycle_id}", response_model=RevenueScheduleOut)
def create_schedule_from_cycle(cycle_id: str, db: Session = Depends(get_db)) -> RevenueScheduleOut:
    return RevenueScheduleOut.model_validate(rev_svc.create_schedule_from_cycle(db, cycle_id))


@router.get("/revenue-recognition-entries", response_model=RevenueEntryListOut)
def list_revenue_entries(
    schedule_id: str | None = Query(None),
    partner_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> RevenueEntryListOut:
    rows = rev_svc.list_entries(db, schedule_id=schedule_id, partner_id=partner_id)
    items = [RevenueEntryOut.model_validate(r) for r in rows]
    return RevenueEntryListOut(items=items, total=len(items))


@router.post("/revenue-recognition/run", response_model=RevenueRunOut)
def run_revenue_recognition(
    through_date: date | None = Query(None),
    sync_fiscal: bool = Query(True),
    db: Session = Depends(get_db),
) -> RevenueRunOut:
    result = rev_svc.run_straight_line_recognition(db, through_date=through_date)
    fiscal = None
    if sync_fiscal:
        fiscal = rev_svc.sync_recognition_to_fiscal(db, snapshot_date=through_date or date.today())
    return RevenueRunOut(**result, fiscal=fiscal)
