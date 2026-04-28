from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def list_eligible_billing_cycle_ids(db: Session, batch_size: int = 100) -> list[str]:
    rows = db.execute(
        text(
            """
            SELECT id
            FROM partner_billing_cycles
            WHERE status IN ('OPEN', 'COMPUTING')
            ORDER BY created_at ASC
            LIMIT :batch_size
            """
        ),
        {"batch_size": int(batch_size)},
    ).fetchall()
    return [str(r[0]) for r in rows]


def claim_cycle_for_compute(db: Session, cycle_id: str) -> bool:
    updated = db.execute(
        text(
            """
            UPDATE partner_billing_cycles
            SET status = 'COMPUTING',
                updated_at = NOW()
            WHERE id = :cycle_id
              AND status IN ('OPEN', 'COMPUTING')
            """
        ),
        {"cycle_id": cycle_id},
    )
    db.commit()
    return int(updated.rowcount or 0) > 0


def _sum_line_items(db: Session, cycle_id: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT
                COALESCE(SUM(CASE WHEN line_type = 'BASE_FEE' THEN total_cents ELSE 0 END), 0) AS base_fee_cents,
                COALESCE(SUM(CASE
                    WHEN line_type IN ('DELIVERY_FEE','PICKUP_FEE','STORAGE_DAY_FEE')
                    THEN total_cents ELSE 0 END), 0) AS usage_fee_cents,
                COALESCE(SUM(CASE WHEN line_type = 'OVERAGE_FEE' THEN total_cents ELSE 0 END), 0) AS overage_fee_cents,
                COALESCE(SUM(CASE WHEN line_type = 'SLA_PENALTY' THEN total_cents ELSE 0 END), 0) AS sla_penalty_cents,
                COALESCE(SUM(CASE WHEN line_type = 'DISCOUNT' THEN total_cents ELSE 0 END), 0) AS discount_cents,
                COALESCE(SUM(CASE WHEN line_type = 'TAX' THEN total_cents ELSE 0 END), 0) AS tax_cents,
                COALESCE(SUM(total_cents), 0) AS total_amount_cents,
                COALESCE(SUM(CASE WHEN line_type = 'DELIVERY_FEE' THEN quantity ELSE 0 END), 0) AS total_deliveries,
                COALESCE(SUM(CASE WHEN line_type = 'PICKUP_FEE' THEN quantity ELSE 0 END), 0) AS total_pickups,
                COALESCE(SUM(CASE WHEN line_type = 'STORAGE_DAY_FEE' THEN quantity ELSE 0 END), 0) AS total_slot_days
            FROM partner_billing_line_items
            WHERE cycle_id = :cycle_id
            """
        ),
        {"cycle_id": cycle_id},
    ).mappings().first()
    return dict(row or {})


def _cycle_context(db: Session, cycle_id: str) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT id, partner_id, country_code, jurisdiction_code, period_start, period_end
            FROM partner_billing_cycles
            WHERE id = :cycle_id
            """
        ),
        {"cycle_id": cycle_id},
    ).mappings().first()
    return dict(row) if row else None


def _build_cycle_dedupe_key(ctx: dict) -> str:
    period_start = ctx.get("period_start")
    period_end = ctx.get("period_end")
    if isinstance(period_start, date):
        period_start = period_start.isoformat()
    if isinstance(period_end, date):
        period_end = period_end.isoformat()
    return (
        f"cycle_compute:{ctx.get('partner_id')}:{ctx.get('country_code') or 'GLOBAL'}:"
        f"{ctx.get('jurisdiction_code') or 'GLOBAL'}:{period_start}:{period_end}"
    )


def compute_cycle_once(db: Session, cycle_id: str) -> dict | None:
    if not claim_cycle_for_compute(db, cycle_id):
        logger.info("partner_billing_cycle_claim_skipped cycle_id=%s", cycle_id)
        return None

    ctx = _cycle_context(db, cycle_id)
    if not ctx:
        logger.warning("partner_billing_cycle_missing cycle_id=%s", cycle_id)
        return None

    dedupe_key = _build_cycle_dedupe_key(ctx)
    existing = db.execute(
        text(
            """
            SELECT id
            FROM partner_billing_cycles
            WHERE dedupe_key = :dedupe_key
              AND id <> :cycle_id
            LIMIT 1
            """
        ),
        {"dedupe_key": dedupe_key, "cycle_id": cycle_id},
    ).fetchone()
    if existing:
        db.execute(
            text(
                """
                UPDATE partner_billing_cycles
                SET status = 'REVIEW',
                    notes = COALESCE(notes, '') || :note_suffix,
                    updated_at = NOW()
                WHERE id = :cycle_id
                """
            ),
            {
                "cycle_id": cycle_id,
                "note_suffix": "\n[IDEMPOTENCY] dedupe_key já utilizado em outro ciclo.",
            },
        )
        db.commit()
        return {"cycle_id": cycle_id, "status": "REVIEW", "dedupe_conflict": True}

    sums = _sum_line_items(db, cycle_id)
    base_fee_cents = int(sums.get("base_fee_cents") or 0)
    usage_fee_cents = int(sums.get("usage_fee_cents") or 0)
    overage_fee_cents = int(sums.get("overage_fee_cents") or 0)
    sla_penalty_cents = int(sums.get("sla_penalty_cents") or 0)
    discount_cents = int(sums.get("discount_cents") or 0)
    tax_cents = int(sums.get("tax_cents") or 0)
    total_amount_cents = int(sums.get("total_amount_cents") or 0)
    total_deliveries = int(Decimal(sums.get("total_deliveries") or 0))
    total_pickups = int(Decimal(sums.get("total_pickups") or 0))
    total_slot_days = Decimal(sums.get("total_slot_days") or 0)

    db.execute(
        text(
            """
            UPDATE partner_billing_cycles
            SET
                total_deliveries = :total_deliveries,
                total_pickups = :total_pickups,
                total_slot_days = :total_slot_days,
                base_fee_cents = :base_fee_cents,
                usage_fee_cents = :usage_fee_cents,
                overage_fee_cents = :overage_fee_cents,
                sla_penalty_cents = :sla_penalty_cents,
                discount_cents = :discount_cents,
                tax_cents = :tax_cents,
                total_amount_cents = :total_amount_cents,
                dedupe_key = :dedupe_key,
                status = 'REVIEW',
                computed_at = :computed_at,
                updated_at = NOW()
            WHERE id = :cycle_id
            """
        ),
        {
            "cycle_id": cycle_id,
            "total_deliveries": total_deliveries,
            "total_pickups": total_pickups,
            "total_slot_days": total_slot_days,
            "base_fee_cents": base_fee_cents,
            "usage_fee_cents": usage_fee_cents,
            "overage_fee_cents": overage_fee_cents,
            "sla_penalty_cents": sla_penalty_cents,
            "discount_cents": discount_cents,
            "tax_cents": tax_cents,
            "total_amount_cents": total_amount_cents,
            "dedupe_key": dedupe_key,
            "computed_at": _utc_now(),
        },
    )
    db.commit()

    return {
        "cycle_id": cycle_id,
        "status": "REVIEW",
        "dedupe_key": dedupe_key,
        "total_amount_cents": total_amount_cents,
    }


def open_cycle_dispute(db: Session, cycle_id: str, reason: str) -> dict:
    normalized_reason = (reason or "").strip()
    if not normalized_reason:
        raise ValueError("reason is required")

    row = db.execute(
        text(
            """
            UPDATE partner_billing_cycles
            SET status = 'DISPUTED',
                dispute_reason = :reason,
                updated_at = NOW()
            WHERE id = :cycle_id
            RETURNING id, partner_id, status, dispute_reason
            """
        ),
        {"cycle_id": cycle_id, "reason": normalized_reason},
    ).mappings().first()
    db.commit()
    if not row:
        raise ValueError("cycle not found")
    return dict(row)
