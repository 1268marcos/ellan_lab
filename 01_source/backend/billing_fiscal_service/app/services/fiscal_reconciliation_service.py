from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import outerjoin, select
from sqlalchemy.orm import Session

from app.models.external_domain_event import DomainEvent
from app.models.fiscal_reconciliation_gap import FiscalReconciliationGap
from app.models.invoice_model import Invoice, InvoiceStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class GapCandidate:
    dedupe_key: str
    gap_type: str
    severity: str
    order_id: str | None
    invoice_id: str | None
    details_json: dict


def _build_gap_candidates(
    *,
    paid_without_invoice: list[str],
    issued_without_paid: list[tuple[str, str]],
) -> list[GapCandidate]:
    out: list[GapCandidate] = []
    for order_id in paid_without_invoice:
        out.append(
            GapCandidate(
                dedupe_key=f"paid_without_invoice:{order_id}",
                gap_type="PAID_WITHOUT_INVOICE",
                severity="ERROR",
                order_id=order_id,
                invoice_id=None,
                details_json={"message": "order.paid existe, mas não há invoice para o pedido."},
            )
        )
    for order_id, invoice_id in issued_without_paid:
        out.append(
            GapCandidate(
                dedupe_key=f"issued_without_paid:{invoice_id}",
                gap_type="ISSUED_WITHOUT_PAID",
                severity="ERROR",
                order_id=order_id,
                invoice_id=invoice_id,
                details_json={"message": "Invoice ISSUED sem evento order.paid correspondente."},
            )
        )
    return out


def _collect_paid_without_invoice(db: Session, *, since: datetime, limit: int) -> list[str]:
    join_stmt = outerjoin(DomainEvent, Invoice, DomainEvent.aggregate_id == Invoice.order_id)
    stmt = (
        select(DomainEvent.aggregate_id)
        .select_from(join_stmt)
        .where(DomainEvent.aggregate_type == "order")
        .where(DomainEvent.event_name == "order.paid")
        .where(DomainEvent.occurred_at >= since)
        .where(Invoice.id.is_(None))
        .order_by(DomainEvent.occurred_at.desc())
        .limit(limit)
    )
    return [str(x) for x in db.execute(stmt).scalars().all() if x]


def _collect_issued_without_paid(db: Session, *, since: datetime, limit: int) -> list[tuple[str, str]]:
    join_stmt = outerjoin(
        Invoice,
        DomainEvent,
        (DomainEvent.aggregate_id == Invoice.order_id)
        & (DomainEvent.aggregate_type == "order")
        & (DomainEvent.event_name == "order.paid"),
    )
    stmt = (
        select(Invoice.order_id, Invoice.id)
        .select_from(join_stmt)
        .where(Invoice.status == InvoiceStatus.ISSUED)
        .where(Invoice.created_at >= since)
        .where(DomainEvent.id.is_(None))
        .order_by(Invoice.created_at.desc())
        .limit(limit)
    )
    return [(str(order_id), str(invoice_id)) for order_id, invoice_id in db.execute(stmt).all()]


def scan_and_persist_reconciliation_gaps(
    db: Session,
    *,
    lookback_days: int = 7,
    limit_per_type: int = 500,
) -> dict:
    now = _utc_now()
    since = now - timedelta(days=max(1, lookback_days))
    paid_wo_invoice = _collect_paid_without_invoice(db, since=since, limit=limit_per_type)
    issued_wo_paid = _collect_issued_without_paid(db, since=since, limit=limit_per_type)
    candidates = _build_gap_candidates(
        paid_without_invoice=paid_wo_invoice,
        issued_without_paid=issued_wo_paid,
    )

    current_keys = {c.dedupe_key for c in candidates}
    existing = {
        row.dedupe_key: row
        for row in db.query(FiscalReconciliationGap)
        .filter(FiscalReconciliationGap.status == "OPEN")
        .all()
    }

    created = 0
    updated = 0
    for c in candidates:
        row = existing.get(c.dedupe_key)
        if row is None:
            row = FiscalReconciliationGap(
                id=f"frg_{uuid.uuid4().hex[:24]}",
                dedupe_key=c.dedupe_key,
                gap_type=c.gap_type,
                severity=c.severity,
                status="OPEN",
                order_id=c.order_id,
                invoice_id=c.invoice_id,
                details_json=c.details_json,
                first_detected_at=now,
                last_detected_at=now,
            )
            db.add(row)
            created += 1
        else:
            row.last_detected_at = now
            row.details_json = c.details_json
            row.severity = c.severity
            row.order_id = c.order_id
            row.invoice_id = c.invoice_id
            row.resolved_at = None
            updated += 1

    resolved = 0
    for key, row in existing.items():
        if key not in current_keys:
            row.status = "RESOLVED"
            row.resolved_at = now
            resolved += 1

    db.commit()
    return {
        "paid_without_invoice": len(paid_wo_invoice),
        "issued_without_paid": len(issued_wo_paid),
        "open_total": len(candidates),
        "created": created,
        "updated": updated,
        "resolved": resolved,
        "lookback_days": lookback_days,
    }


def list_reconciliation_gaps(
    db: Session,
    *,
    status: str = "OPEN",
    date_from: datetime | None = None,
    limit: int = 200,
) -> list[FiscalReconciliationGap]:
    q = db.query(FiscalReconciliationGap).order_by(FiscalReconciliationGap.last_detected_at.desc())
    if status:
        q = q.filter(FiscalReconciliationGap.status == status)
    if date_from:
        q = q.filter(FiscalReconciliationGap.last_detected_at >= date_from)
    return q.limit(max(1, min(limit, 1000))).all()
