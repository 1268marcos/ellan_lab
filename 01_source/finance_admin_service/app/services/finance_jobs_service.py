from __future__ import annotations

import json
from datetime import date, datetime, timezone

from sqlalchemy.orm import Session

from app.models.finance_extended import PartnerSettlementBatch
from app.models.finance_revenue import FinanceScheduledJobRun
from app.services import finance_advanced_service as adv_svc
from app.services.billing_fiscal_client import (
    BillingFiscalClientError,
    fetch_fiscal_gap_snapshot,
    is_fiscal_live_enabled,
)
from app.services.crypto_util import new_id
from app.services.finance_ecosystem_intelligence_service import run_full_intelligence_scan
from app.services.finance_readiness_service import recompute_all_readiness
from app.services.finance_revenue_service import run_straight_line_recognition, sync_recognition_to_fiscal

JOB_CODES = (
    "DUNNING_SCAN",
    "SETTLEMENT_RECONCILE",
    "REVENUE_RECOGNITION",
    "FISCAL_GAP_SYNC",
    "READINESS_RECOMPUTE",
    "ECOSYSTEM_INTELLIGENCE_SCAN",
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _start_run(db: Session, job_code: str) -> FinanceScheduledJobRun:
    row = FinanceScheduledJobRun(
        id=new_id(),
        job_code=job_code,
        started_at=_utcnow(),
        status="RUNNING",
        result_json="{}",
    )
    db.add(row)
    db.flush()
    return row


def _finish_run(db: Session, run: FinanceScheduledJobRun, result: dict, *, error: str | None = None) -> None:
    run.finished_at = _utcnow()
    run.status = "FAILED" if error else "COMPLETED"
    run.result_json = json.dumps(result)
    run.error_message = error
    db.commit()


def run_job(db: Session, job_code: str) -> dict:
    if job_code not in JOB_CODES:
        return {"error": f"unknown_job: {job_code}"}

    run = _start_run(db, job_code)
    try:
        if job_code == "DUNNING_SCAN":
            result = adv_svc.scan_overdue_invoices(db)
        elif job_code == "SETTLEMENT_RECONCILE":
            result = _run_settlement_reconcile_all(db)
        elif job_code == "REVENUE_RECOGNITION":
            result = run_straight_line_recognition(db, through_date=date.today())
            if is_fiscal_live_enabled():
                result["fiscal"] = sync_recognition_to_fiscal(db, snapshot_date=date.today())
        elif job_code == "FISCAL_GAP_SYNC":
            result = _sync_fiscal_gaps(db)
        elif job_code == "READINESS_RECOMPUTE":
            n, avg = recompute_all_readiness(db)
            result = {"recomputed": n, "average_score": round(avg, 2)}
        elif job_code == "ECOSYSTEM_INTELLIGENCE_SCAN":
            result = run_full_intelligence_scan(db)
        else:
            result = {}
        _finish_run(db, run, result)
        return {"job_run_id": run.id, "job_code": job_code, "status": "COMPLETED", **result}
    except Exception as exc:
        _finish_run(db, run, {}, error=str(exc))
        return {"job_run_id": run.id, "job_code": job_code, "status": "FAILED", "error": str(exc)}


def _run_settlement_reconcile_all(db: Session) -> dict:
    batches = (
        db.query(PartnerSettlementBatch)
        .filter(PartnerSettlementBatch.status.in_(("DRAFT", "REVIEW")))
        .limit(20)
        .all()
    )
    reconciled = 0
    for batch in batches:
        adv_svc.reconcile_settlement_batch(db, batch.id)
        reconciled += 1
    return {"batches_reconciled": reconciled}


def _sync_fiscal_gaps(db: Session) -> dict:
    if not is_fiscal_live_enabled():
        return {"skipped": True, "reason": "billing_fiscal_live_disabled"}
    try:
        snapshot = fetch_fiscal_gap_snapshot(snapshot_date=date.today(), refresh_scan=True)
    except BillingFiscalClientError as exc:
        return {"error": str(exc)}

    from app.models.finance_extended import FiscalReconciliationGap
    from app.services.crypto_util import new_id as nid

    upserted = 0
    samples = snapshot.get("sample_open_gaps") or snapshot.get("sample_gaps") or snapshot.get("gaps") or []
    for item in samples:
        if not isinstance(item, dict):
            continue
        dedupe = item.get("dedupe_key") or f"fiscal|{item.get('gap_type')}|{item.get('order_id')}"
        if db.query(FiscalReconciliationGap).filter(FiscalReconciliationGap.dedupe_key == dedupe).first():
            continue
        now = _utcnow()
        db.add(
            FiscalReconciliationGap(
                id=nid(),
                dedupe_key=dedupe[:180],
                gap_type=str(item.get("gap_type") or "FISCAL_MISMATCH"),
                severity=str(item.get("severity") or "MEDIUM"),
                status="OPEN",
                order_id=item.get("order_id"),
                details_json=json.dumps(item),
                first_detected_at=now,
                last_detected_at=now,
            )
        )
        upserted += 1
    db.commit()
    summary = snapshot.get("summary") or {}
    return {"gaps_upserted": upserted, "open_gaps_total": summary.get("open_gaps_total", 0)}


def list_job_runs(db: Session, job_code: str | None = None, limit: int = 50) -> list[FinanceScheduledJobRun]:
    q = db.query(FinanceScheduledJobRun).order_by(FinanceScheduledJobRun.started_at.desc())
    if job_code:
        q = q.filter(FinanceScheduledJobRun.job_code == job_code)
    return q.limit(limit).all()
