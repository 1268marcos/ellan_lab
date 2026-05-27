#!/usr/bin/env python3
"""
Reprocessa reconciliation_pending presas (PROCESSING antigo, FAILED/PENDING envelhecidas).

Uso (a partir de order_pickup_service/):
  PYTHONPATH=. python scripts/retry_stuck_pending.py --dry-run
  PYTHONPATH=. python scripts/retry_stuck_pending.py --run-reconcile --batch-size 25
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.jobs.reconciliation_retry import run_reconciliation_retry_once
from app.models.reconciliation_pending import ReconciliationPending
from app.services.ops_audit_service import record_ops_action_audit

AUDIT_ACTION = "SCRIPT_RETRY_STUCK_RECONCILIATION"
DEFAULT_STALE_PROCESSING_MIN = 5
DEFAULT_MIN_AGE_SEC = 3600


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class PendingResetDecision:
    pending_id: str
    order_id: str
    reason: str
    previous_status: str
    age_sec: int
    action: str


def find_stuck_pending(
    db: Session,
    *,
    min_age_sec: int,
    stale_processing_min: int,
    limit: int,
    pending_id: str | None,
) -> list[ReconciliationPending]:
    now = _utc_now()
    stale_before = now - timedelta(minutes=max(int(stale_processing_min), 1))
    age_before = now - timedelta(seconds=max(int(min_age_sec), 1))

    q = db.query(ReconciliationPending).order_by(ReconciliationPending.created_at.asc())
    if pending_id:
        row = q.filter(ReconciliationPending.id == str(pending_id).strip()).first()
        if not row:
            return []
        if str(row.status or "").upper() in {"DONE", "FAILED_FINAL"}:
            return []
        return [row]

    rows = q.filter(
        ReconciliationPending.status.in_(["PENDING", "PROCESSING", "FAILED"])
    ).limit(max(int(limit), 1) * 5).all()

    stuck: list[ReconciliationPending] = []
    for row in rows:
        if len(stuck) >= limit:
            break
        status = str(row.status or "").upper()
        created = row.created_at
        if created is not None and getattr(created, "tzinfo", None) is None:
            created = created.replace(tzinfo=timezone.utc)
        age_sec = int(max(0, (now - created).total_seconds())) if created else 0

        is_stale_processing = (
            status == "PROCESSING"
            and row.processing_started_at is not None
            and row.processing_started_at <= stale_before
        )
        is_old_open = status in {"PENDING", "FAILED"} and created is not None and created <= age_before
        is_failed_ready = (
            status == "FAILED"
            and (row.next_retry_at is None or row.next_retry_at <= now)
            and age_sec >= min_age_sec
        )

        if is_stale_processing or is_old_open or is_failed_ready:
            stuck.append(row)
    return stuck


def _reset_pending_row(row: ReconciliationPending, *, now: datetime) -> None:
    row.status = "PENDING"
    row.processing_started_at = None
    row.next_retry_at = None
    row.updated_at = now
    payload = dict(row.payload_json or {})
    payload["script_retry_stuck_at"] = now.isoformat()
    row.payload_json = payload


def _audit_batch(
    db: Session,
    *,
    correlation_id: str,
    dry_run: bool,
    decisions: list[PendingResetDecision],
    reconcile_processed: int | None = None,
) -> None:
    record_ops_action_audit(
        db=db,
        action=AUDIT_ACTION,
        result="DRY_RUN" if dry_run else "SUCCESS",
        correlation_id=correlation_id,
        user_id=None,
        role="system_script",
        order_id=decisions[0].order_id if len(decisions) == 1 else None,
        details={
            "dry_run": dry_run,
            "script": "retry_stuck_pending.py",
            "reset_count": len(decisions),
            "reconcile_processed": reconcile_processed,
            "items": [asdict(d) for d in decisions[:50]],
        },
    )


def run_retry_stuck_pending(
    db: Session,
    *,
    dry_run: bool,
    limit: int,
    min_age_sec: int,
    stale_processing_min: int,
    pending_id: str | None,
    run_reconcile: bool,
    batch_size: int,
    correlation_id: str,
) -> dict[str, Any]:
    now = _utc_now()
    rows = find_stuck_pending(
        db,
        min_age_sec=min_age_sec,
        stale_processing_min=stale_processing_min,
        limit=limit,
        pending_id=pending_id,
    )

    decisions: list[PendingResetDecision] = []
    for row in rows:
        created = row.created_at
        if created is not None and getattr(created, "tzinfo", None) is None:
            created = created.replace(tzinfo=timezone.utc)
        age_sec = int(max(0, (now - created).total_seconds())) if created else 0
        decisions.append(
            PendingResetDecision(
                pending_id=row.id,
                order_id=row.order_id,
                reason=str(row.reason or ""),
                previous_status=str(row.status or ""),
                age_sec=age_sec,
                action="reset_to_pending",
            )
        )
        if not dry_run:
            _reset_pending_row(row, now=now)

    reconcile_processed: int | None = None
    if not dry_run:
        if run_reconcile and rows:
            db.commit()
            reconcile_processed = run_reconciliation_retry_once(db, batch_size=batch_size)
        else:
            db.commit()

    if decisions and not dry_run:
        audit_db = SessionLocal()
        try:
            _audit_batch(
                audit_db,
                correlation_id=correlation_id,
                dry_run=dry_run,
                decisions=decisions,
                reconcile_processed=reconcile_processed,
            )
            if not dry_run:
                audit_db.commit()
            else:
                audit_db.rollback()
        finally:
            audit_db.close()

    return {
        "correlation_id": correlation_id,
        "dry_run": dry_run,
        "reset_count": len(decisions),
        "reconcile_processed": reconcile_processed,
        "decisions": [asdict(d) for d in decisions],
    }


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Reabre reconciliation_pending presas e opcionalmente reexecuta worker.")
    p.add_argument("--dry-run", action="store_true", help="Lista ações sem persistir.")
    p.add_argument("--limit", type=int, default=50, help="Máximo de pendências a resetar.")
    p.add_argument("--pending-id", type=str, default=None, help="Resetar uma pendência específica.")
    p.add_argument(
        "--min-age-sec",
        type=int,
        default=DEFAULT_MIN_AGE_SEC,
        help="Idade mínima (s) para PENDING/FAILED consideradas presas.",
    )
    p.add_argument(
        "--stale-processing-min",
        type=int,
        default=DEFAULT_STALE_PROCESSING_MIN,
        help="PROCESSING mais antigo que N minutos é considerado preso.",
    )
    p.add_argument(
        "--run-reconcile",
        action="store_true",
        help="Após reset, chama run_reconciliation_retry_once.",
    )
    p.add_argument("--batch-size", type=int, default=25, help="Batch do worker de reconciliação.")
    p.add_argument("--correlation-id", type=str, default=None)
    p.add_argument("--json", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    correlation_id = str(args.correlation_id or f"retry-stuck-{uuid.uuid4().hex[:16]}")

    db = SessionLocal()
    try:
        summary = run_retry_stuck_pending(
            db,
            dry_run=bool(args.dry_run),
            limit=int(args.limit),
            min_age_sec=int(args.min_age_sec),
            stale_processing_min=int(args.stale_processing_min),
            pending_id=args.pending_id,
            run_reconcile=bool(args.run_reconcile),
            batch_size=int(args.batch_size),
            correlation_id=correlation_id,
        )
    except Exception as exc:
        print(f"retry_stuck_pending failed: {exc}", file=sys.stderr)
        db.rollback()
        return 1
    finally:
        db.close()

    if args.json:
        print(json.dumps(summary, indent=2, default=str))
    else:
        mode = "DRY-RUN" if args.dry_run else "APPLY"
        print(f"[{mode}] correlation_id={correlation_id}")
        print(f"reset_count={summary['reset_count']} reconcile_processed={summary['reconcile_processed']}")
        for d in summary["decisions"]:
            print(
                f"  pending={d['pending_id']} order={d['order_id']} "
                f"was={d['previous_status']} age_sec={d['age_sec']} reason={d['reason']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
