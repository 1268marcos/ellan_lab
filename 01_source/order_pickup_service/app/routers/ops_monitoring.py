# Dashboard OPS — créditos, reconciliação e alocações presas.

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth_dep import require_user_roles
from app.core.db import get_db
from app.services.ops_monitoring_service import (
    fetch_credits_health,
    fetch_ops_monitoring_summary,
    fetch_reconciliation_lag,
    fetch_runtime_deadlocks,
)

router = APIRouter(
    prefix="/ops/monitoring",
    tags=["ops-monitoring"],
    dependencies=[Depends(require_user_roles(allowed_roles={"admin_operacao", "auditoria", "suporte"}))],
)


class TopUserExpiringOut(BaseModel):
    user_id: str
    credits_count: int
    nearest_expires_at: str | None = None
    total_amount_cents: int = 0


class CreditsHealthOut(BaseModel):
    ok: bool = True
    as_of: str
    period_utc_day_start: str
    total_credits: int
    used_today: int
    expired_today: int
    available_expiring_within_days: int = 0
    expiring_within_days: int = 7
    by_status: dict[str, int] = Field(default_factory=dict)
    top_users_expiring: list[TopUserExpiringOut] = Field(default_factory=list)


class ReconciliationStatusCountOut(BaseModel):
    status: str
    count: int


class ReconciliationLagOut(BaseModel):
    ok: bool = True
    as_of: str
    open_pending_count: int
    avg_pending_age_sec: float
    max_pending_age_sec: int
    oldest_open: dict | None = None
    status_distribution: dict[str, int] = Field(default_factory=dict)
    stale_processing_count: int = 0
    alert: bool = False


class RuntimeDeadlockItemOut(BaseModel):
    allocation_id: str
    order_id: str
    locker_id: str | None = None
    slot: int
    state: str
    locked_until: str | None = None
    lock_expired: bool = False
    updated_at: str | None = None
    age_sec: int | None = None


class RuntimeDeadlocksOut(BaseModel):
    ok: bool = True
    as_of: str
    lock_age_threshold_sec: int
    stuck_count: int
    items: list[RuntimeDeadlockItemOut] = Field(default_factory=list)
    alert: bool = False


class OpsMonitoringAlertOut(BaseModel):
    code: str
    severity: str
    message: str


class OpsMonitoringSummaryOut(BaseModel):
    ok: bool
    as_of: str
    alerts: list[OpsMonitoringAlertOut] = Field(default_factory=list)
    credits_health: CreditsHealthOut
    reconciliation_lag: ReconciliationLagOut
    runtime_deadlocks: RuntimeDeadlocksOut


@router.get("/credits-health", response_model=CreditsHealthOut)
def get_credits_health(
    expiring_within_days: int = Query(7, ge=1, le=90),
    top_users_limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    payload = fetch_credits_health(
        db,
        expiring_within_days=expiring_within_days,
        top_users_limit=top_users_limit,
    )
    return CreditsHealthOut(**payload)


@router.get("/reconciliation-lag", response_model=ReconciliationLagOut)
def get_reconciliation_lag(db: Session = Depends(get_db)):
    payload = fetch_reconciliation_lag(db)
    return ReconciliationLagOut(**payload)


@router.get("/runtime-deadlocks", response_model=RuntimeDeadlocksOut)
def get_runtime_deadlocks(
    lock_age_sec: int = Query(3600, ge=60, le=86400),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    payload = fetch_runtime_deadlocks(db, lock_age_sec=lock_age_sec, limit=limit)
    return RuntimeDeadlocksOut(**payload)


@router.get("/summary", response_model=OpsMonitoringSummaryOut)
def get_ops_monitoring_summary(db: Session = Depends(get_db)):
    payload = fetch_ops_monitoring_summary(db)
    return OpsMonitoringSummaryOut(**payload)
