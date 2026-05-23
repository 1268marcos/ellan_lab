"""Multas automáticas por atraso em faturas rental."""
from __future__ import annotations

import uuid
from datetime import timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.routers.rental_ops_common import utc_now as _utc_now


def _get_active_late_fee_policy(db: Session) -> dict[str, Any] | None:
    try:
        row = db.execute(
            text(
                """
                SELECT code, grace_days, fee_type, fee_value, daily_cap_cents, max_fee_cents
                FROM rental_late_fee_policies
                WHERE active = TRUE
                ORDER BY priority ASC
                LIMIT 1
                """
            )
        ).mappings().first()
        return dict(row) if row else None
    except Exception:
        return None


def _compute_fee_cents(policy: dict[str, Any], base_cents: int, days_overdue: int) -> int:
    days_overdue = max(0, days_overdue)
    fee_type = str(policy.get("fee_type") or "BPS")
    fee_value = float(policy.get("fee_value") or 0)
    daily_cap = int(policy.get("daily_cap_cents") or 0)
    max_fee = int(policy.get("max_fee_cents") or 0)

    if fee_type == "FLAT":
        fee = int(fee_value)
    elif fee_type == "DAILY_BPS":
        fee = int(base_cents * fee_value / 10000 * days_overdue)
        if daily_cap > 0:
            fee = min(fee, daily_cap * days_overdue)
    else:
        fee = int(base_cents * fee_value / 10000)

    if max_fee > 0:
        fee = min(fee, max_fee)
    return max(0, fee)


def apply_automatic_late_fees(db: Session) -> dict[str, int]:
    """
    Para faturas OVERDUE além do grace period: aplica multa uma vez por fatura
    (registro em rental_late_fee_charges + incremento em late_fee_cents na invoice).
    """
    policy = _get_active_late_fee_policy(db)
    if not policy:
        return {"applied": 0, "skipped": 0}

    now = _utc_now()
    grace_days = int(policy.get("grace_days") or 3)
    rows = db.execute(
        text(
            """
            SELECT i.id, i.contract_id, i.amount_cents, i.late_fee_cents, i.due_at, i.currency
            FROM rental_billing_invoices i
            WHERE i.status = 'OVERDUE'
              AND i.due_at IS NOT NULL
              AND i.due_at < :cutoff
            """
        ),
        {"cutoff": now - timedelta(days=grace_days)},
    ).mappings().all()

    applied = 0
    skipped = 0
    for inv in rows:
        iid = str(inv["id"])
        if db.execute(
            text("SELECT id FROM rental_late_fee_charges WHERE invoice_id = :i LIMIT 1"),
            {"i": iid},
        ).mappings().first():
            skipped += 1
            continue

        due_at = inv.get("due_at")
        if hasattr(due_at, "timestamp"):
            days_over = max(1, (now - due_at).days)
        else:
            days_over = grace_days + 1

        base = int(inv["amount_cents"]) - int(inv.get("late_fee_cents") or 0)
        fee = _compute_fee_cents(policy, base, days_over)
        if fee <= 0:
            skipped += 1
            continue

        db.execute(
            text(
                """
                INSERT INTO rental_late_fee_charges (
                    id, contract_id, invoice_id, policy_code, days_overdue,
                    fee_cents, currency, applied_at, created_at
                ) VALUES (
                    :id, :cid, :iid, :code, :days, :fee, :cur, :now, :now
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "cid": str(inv["contract_id"]),
                "iid": iid,
                "code": str(policy["code"]),
                "days": days_over,
                "fee": fee,
                "cur": str(inv.get("currency") or "BRL"),
                "now": now,
            },
        )
        db.execute(
            text(
                """
                UPDATE rental_billing_invoices
                SET late_fee_cents = COALESCE(late_fee_cents, 0) + :fee,
                    amount_cents = amount_cents + :fee,
                    updated_at = :now
                WHERE id = :iid
                """
            ),
            {"fee": fee, "iid": iid, "now": now},
        )
        applied += 1

    return {"applied": applied, "skipped": skipped, "policy_code": str(policy["code"])}
