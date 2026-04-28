from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class DivergenceResult:
    status: str
    difference_hours: Decimal
    difference_pct: Decimal | None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def classify_divergence(
    measured_occupied_hours: Decimal,
    billed_storage_hours: Decimal,
    tolerance_hours: Decimal = Decimal("0.50"),
) -> DivergenceResult:
    measured = Decimal(measured_occupied_hours or 0)
    billed = Decimal(billed_storage_hours or 0)
    diff = measured - billed
    if measured <= 0 and billed <= 0:
        return DivergenceResult(status="OK", difference_hours=Decimal("0"), difference_pct=Decimal("0"))
    if measured > 0 and billed <= 0:
        return DivergenceResult(status="MISSING_BILLING", difference_hours=diff, difference_pct=Decimal("100.0000"))

    pct = (diff / measured) * Decimal("100") if measured > 0 else Decimal("0")
    if abs(diff) <= tolerance_hours:
        return DivergenceResult(status="OK", difference_hours=diff, difference_pct=pct)
    if diff > 0:
        return DivergenceResult(status="UNDER_BILLED", difference_hours=diff, difference_pct=pct)
    return DivergenceResult(status="OVER_BILLED", difference_hours=diff, difference_pct=pct)


def recompute_daily_utilization_snapshot(
    db: Session,
    *,
    snapshot_date: date,
    partner_id: str | None = None,
    locker_id: str | None = None,
) -> dict:
    clauses = ["c.period_start <= :snapshot_date", "c.period_end >= :snapshot_date"]
    params: dict[str, object] = {"snapshot_date": snapshot_date}
    if partner_id:
        clauses.append("c.partner_id = :partner_id")
        params["partner_id"] = partner_id
    if locker_id:
        clauses.append("c.locker_id = :locker_id")
        params["locker_id"] = locker_id

    cycle_rows = db.execute(
        text(
            f"""
            SELECT c.partner_id, c.locker_id, c.country_code, c.jurisdiction_code, c.currency, c.period_timezone
            FROM partner_billing_cycles c
            WHERE c.locker_id IS NOT NULL
              AND {' AND '.join(clauses)}
            """
        ),
        params,
    ).mappings().all()

    processed = 0
    for cycle in cycle_rows:
        cycle_dict = dict(cycle)
        measured_row = db.execute(
            text(
                """
                SELECT COALESCE(SUM(occupied_duration_minutes), 0) AS measured_minutes
                FROM locker_slot_hourly_occupancy
                WHERE locker_id = :locker_id
                  AND hour_bucket::date = :snapshot_date
                  AND is_occupied = TRUE
                """
            ),
            {"locker_id": cycle_dict["locker_id"], "snapshot_date": snapshot_date},
        ).mappings().first()
        measured_minutes = int((measured_row or {}).get("measured_minutes") or 0)
        measured_hours = (Decimal(measured_minutes) / Decimal("60")).quantize(Decimal("0.0001"))

        billed_row = db.execute(
            text(
                """
                SELECT
                    COALESCE(SUM(quantity), 0) AS billed_units,
                    COALESCE(SUM(total_cents), 0) AS billed_amount_cents
                FROM partner_billing_line_items
                WHERE partner_id = :partner_id
                  AND locker_id = :locker_id
                  AND line_type = 'STORAGE_DAY_FEE'
                  AND (
                    (period_from IS NOT NULL AND period_from::date <= :snapshot_date AND (period_to IS NULL OR period_to::date >= :snapshot_date))
                    OR (period_from IS NULL AND period_to IS NULL AND created_at::date = :snapshot_date)
                  )
                """
            ),
            {
                "partner_id": cycle_dict["partner_id"],
                "locker_id": cycle_dict["locker_id"],
                "snapshot_date": snapshot_date,
            },
        ).mappings().first()

        billed_units = Decimal((billed_row or {}).get("billed_units") or 0).quantize(Decimal("0.0001"))
        billed_hours = (billed_units * Decimal("24")).quantize(Decimal("0.0001"))
        billed_amount_cents = int((billed_row or {}).get("billed_amount_cents") or 0)

        divergence = classify_divergence(measured_hours, billed_hours)
        dedupe_key = f"lus:{cycle_dict['partner_id']}:{cycle_dict['locker_id']}:{snapshot_date.isoformat()}"
        db.execute(
            text(
                """
                INSERT INTO locker_utilization_snapshots (
                    snapshot_date, partner_id, locker_id, country_code, jurisdiction_code, currency, timezone,
                    measured_occupied_minutes, measured_occupied_hours,
                    billed_storage_units, billed_storage_hours, billed_storage_amount_cents,
                    difference_hours, difference_pct, divergence_status, dedupe_key, metadata_json, created_at, updated_at
                )
                VALUES (
                    :snapshot_date, :partner_id, :locker_id, :country_code, :jurisdiction_code, :currency, :timezone,
                    :measured_occupied_minutes, :measured_occupied_hours,
                    :billed_storage_units, :billed_storage_hours, :billed_storage_amount_cents,
                    :difference_hours, :difference_pct, :divergence_status, :dedupe_key, :metadata_json::jsonb, :created_at, :updated_at
                )
                ON CONFLICT (partner_id, locker_id, snapshot_date)
                DO UPDATE SET
                    country_code = EXCLUDED.country_code,
                    jurisdiction_code = EXCLUDED.jurisdiction_code,
                    currency = EXCLUDED.currency,
                    timezone = EXCLUDED.timezone,
                    measured_occupied_minutes = EXCLUDED.measured_occupied_minutes,
                    measured_occupied_hours = EXCLUDED.measured_occupied_hours,
                    billed_storage_units = EXCLUDED.billed_storage_units,
                    billed_storage_hours = EXCLUDED.billed_storage_hours,
                    billed_storage_amount_cents = EXCLUDED.billed_storage_amount_cents,
                    difference_hours = EXCLUDED.difference_hours,
                    difference_pct = EXCLUDED.difference_pct,
                    divergence_status = EXCLUDED.divergence_status,
                    dedupe_key = EXCLUDED.dedupe_key,
                    metadata_json = EXCLUDED.metadata_json,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "snapshot_date": snapshot_date,
                "partner_id": cycle_dict["partner_id"],
                "locker_id": cycle_dict["locker_id"],
                "country_code": cycle_dict.get("country_code"),
                "jurisdiction_code": cycle_dict.get("jurisdiction_code"),
                "currency": cycle_dict.get("currency") or "BRL",
                "timezone": cycle_dict.get("period_timezone") or "UTC",
                "measured_occupied_minutes": measured_minutes,
                "measured_occupied_hours": measured_hours,
                "billed_storage_units": billed_units,
                "billed_storage_hours": billed_hours,
                "billed_storage_amount_cents": billed_amount_cents,
                "difference_hours": divergence.difference_hours,
                "difference_pct": divergence.difference_pct,
                "divergence_status": divergence.status,
                "dedupe_key": dedupe_key,
                "metadata_json": "{}",
                "created_at": _utc_now(),
                "updated_at": _utc_now(),
            },
        )
        processed += 1

    db.commit()
    return {"snapshot_date": snapshot_date.isoformat(), "processed": processed}

