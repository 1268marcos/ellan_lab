"""Sprint 2 — conciliação P0: ciclos `partner_billing_cycles` (computados no dia) vs `financial_ledger` BILLING_REVENUE ligado ao ciclo."""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

SCOPE_PARTNER_SETTLEMENT_RECONCILE = "SPRINT2_D16_PARTNER_SETTLEMENT_RECONCILE"


def _safe_residual_cents(a: int, b: int) -> int:
    return abs(int(a) - int(b))


def build_partner_settlement_reconcile_report(
    db: Session,
    *,
    snapshot_date: date,
    currency: str | None = None,
    partner_limit: int = 200,
) -> dict:
    """
    Por `partner_id`: total em ciclos com `computed_at` no dia civil vs soma de linhas
    `financial_ledger` (BILLING_REVENUE, metadata.reference_source=partner_billing_cycle)
    no mesmo dia para ciclos desse parceiro.
    """
    cur = (currency or "").strip() or None
    lim = max(1, min(int(partner_limit or 200), 500))

    cycle_rows = db.execute(
        text(
            """
            SELECT partner_id::text AS partner_id,
                   COUNT(*)::INT AS cycles_computed_on_date,
                   COALESCE(SUM(total_amount_cents), 0)::BIGINT AS cycle_total_cents_computed_on_date
            FROM partner_billing_cycles
            WHERE computed_at IS NOT NULL
              AND computed_at::date = CAST(:d AS DATE)
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            GROUP BY partner_id
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().all()

    ledger_rows = db.execute(
        text(
            """
            SELECT c.partner_id::text AS partner_id,
                   COUNT(fl.id)::INT AS ledger_lines_on_date,
                   COALESCE(SUM(ABS(fl.amount_cents)), 0)::BIGINT AS ledger_billing_cents_on_date
            FROM financial_ledger fl
            INNER JOIN partner_billing_cycles c ON c.id = (fl.metadata->>'reference_id')
            WHERE fl.created_at::date = CAST(:d AS DATE)
              AND fl.entry_type = 'BILLING_REVENUE'
              AND (fl.metadata->>'reference_source') = 'partner_billing_cycle'
              AND (:currency IS NULL OR UPPER(TRIM(fl.currency)) = UPPER(TRIM(:currency)))
            GROUP BY c.partner_id
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().all()

    orphan_row = db.execute(
        text(
            """
            SELECT COUNT(*)::INT AS n
            FROM financial_ledger fl
            WHERE fl.created_at::date = CAST(:d AS DATE)
              AND fl.entry_type = 'BILLING_REVENUE'
              AND (fl.metadata->>'reference_source') = 'partner_billing_cycle'
              AND (:currency IS NULL OR UPPER(TRIM(fl.currency)) = UPPER(TRIM(:currency)))
              AND NOT EXISTS (
                  SELECT 1 FROM partner_billing_cycles c
                  WHERE c.id = (fl.metadata->>'reference_id')
              )
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().first()
    orphan_ledger_lines = int((orphan_row or {}).get("n") or 0)

    by_partner_cycle: dict[str, dict[str, int]] = {}
    for row in cycle_rows:
        pid = str(row.get("partner_id") or "").strip() or "UNKNOWN"
        by_partner_cycle[pid] = {
            "cycles_computed_on_date": int(row.get("cycles_computed_on_date") or 0),
            "cycle_total_cents_computed_on_date": int(row.get("cycle_total_cents_computed_on_date") or 0),
        }

    by_partner_ledger: dict[str, dict[str, int]] = {}
    for row in ledger_rows:
        pid = str(row.get("partner_id") or "").strip() or "UNKNOWN"
        by_partner_ledger[pid] = {
            "ledger_lines_on_date": int(row.get("ledger_lines_on_date") or 0),
            "ledger_billing_cents_on_date": int(row.get("ledger_billing_cents_on_date") or 0),
        }

    partner_ids = sorted(set(by_partner_cycle) | set(by_partner_ledger))
    per_partner: list[dict] = []
    partners_with_residual = 0
    sum_cycle = 0
    sum_ledger = 0
    max_residual = 0

    for pid in partner_ids:
        c_part = by_partner_cycle.get(pid, {"cycles_computed_on_date": 0, "cycle_total_cents_computed_on_date": 0})
        l_part = by_partner_ledger.get(pid, {"ledger_lines_on_date": 0, "ledger_billing_cents_on_date": 0})
        cycle_total = int(c_part["cycle_total_cents_computed_on_date"])
        ledger_total = int(l_part["ledger_billing_cents_on_date"])
        residual = _safe_residual_cents(cycle_total, ledger_total)
        sum_cycle += cycle_total
        sum_ledger += ledger_total
        if residual > 0:
            partners_with_residual += 1
        max_residual = max(max_residual, residual)
        per_partner.append(
            {
                "partner_id": pid,
                "cycles_computed_on_date": int(c_part["cycles_computed_on_date"]),
                "cycle_total_cents_computed_on_date": cycle_total,
                "ledger_lines_on_date": int(l_part["ledger_lines_on_date"]),
                "ledger_billing_cents_on_date": ledger_total,
                "residual_cents": residual,
            }
        )

    per_partner.sort(key=lambda r: int(r["residual_cents"]), reverse=True)
    per_partner_limited = per_partner[:lim]
    cycles_computed_total = sum(int(by_partner_cycle[p]["cycles_computed_on_date"]) for p in by_partner_cycle)

    return {
        "scope": SCOPE_PARTNER_SETTLEMENT_RECONCILE,
        "snapshot_date": snapshot_date.isoformat(),
        "currency_filter": cur,
        "summary": {
            "distinct_partners": len(partner_ids),
            "cycles_computed_on_date_total": cycles_computed_total,
            "cycle_total_cents_computed_on_date_sum": sum_cycle,
            "ledger_billing_cents_on_date_sum": sum_ledger,
            "partners_with_nonzero_residual": partners_with_residual,
            "max_residual_cents_across_partners": max_residual,
            "orphan_ledger_lines_partner_cycle_ref": orphan_ledger_lines,
        },
        "per_partner": per_partner_limited,
    }
