"""Sprint 2 — D14: snapshot de fechamento contábil operacional diário (ELLAN LAB) — agregados auditáveis."""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

SCOPE_DAILY_OPERATIONAL_CLOSE = "SPRINT2_D14_ACCOUNTING_DAILY_OPERATIONAL_CLOSE"


def build_daily_operational_close_report(
    db: Session,
    *,
    snapshot_date: date,
    currency: str | None = None,
) -> dict:
    """
    Consolida, para o dia civil `snapshot_date`: reconhecimento de receita (incl. ajustes manuais),
    KPI financeiro diário, movimentos do `financial_ledger` e ciclos de billing com período ativo no dia.
    """
    cur = (currency or "").strip() or None

    rev_all = db.execute(
        text(
            """
            SELECT
                COUNT(*)::INT AS line_count,
                COUNT(DISTINCT partner_id)::INT AS distinct_partners,
                COALESCE(SUM(recognized_amount_cents), 0)::BIGINT AS recognized_cents,
                COALESCE(SUM(deferred_amount_cents), 0)::BIGINT AS deferred_cents
            FROM ellanlab_revenue_recognition
            WHERE recognition_date = CAST(:d AS DATE)
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().first()

    rev_manual = db.execute(
        text(
            """
            SELECT
                COUNT(*)::INT AS line_count,
                COALESCE(SUM(recognized_amount_cents), 0)::BIGINT AS recognized_cents,
                COALESCE(SUM(deferred_amount_cents), 0)::BIGINT AS deferred_cents
            FROM ellanlab_revenue_recognition
            WHERE recognition_date = CAST(:d AS DATE)
              AND source_type = 'MANUAL_ADJUSTMENT'
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().first()

    kpi = db.execute(
        text(
            """
            SELECT
                COUNT(*)::INT AS row_count,
                COUNT(DISTINCT partner_id)::INT AS distinct_partners,
                COALESCE(SUM(revenue_recognized_cents), 0)::BIGINT AS revenue_recognized_cents,
                COALESCE(SUM(ar_open_cents), 0)::BIGINT AS ar_open_cents
            FROM financial_kpi_daily
            WHERE snapshot_date = CAST(:d AS DATE)
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().first()

    ledger_rows = db.execute(
        text(
            """
            SELECT entry_type,
                   COUNT(*)::INT AS n,
                   COALESCE(SUM(ABS(amount_cents)), 0)::BIGINT AS amount_sum
            FROM financial_ledger
            WHERE created_at::date = CAST(:d AS DATE)
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            GROUP BY entry_type
            ORDER BY entry_type
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().all()

    cycles = db.execute(
        text(
            """
            SELECT
                COUNT(*)::INT AS cycles_open_on_date,
                COUNT(DISTINCT partner_id)::INT AS distinct_partners,
                COALESCE(SUM(total_amount_cents), 0)::BIGINT AS pipeline_total_cents
            FROM partner_billing_cycles
            WHERE period_start <= CAST(:d AS DATE)
              AND period_end >= CAST(:d AS DATE)
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().first()

    rev_lines = int((rev_all or {}).get("line_count") or 0)
    kpi_rows = int((kpi or {}).get("row_count") or 0)
    manual_lines = int((rev_manual or {}).get("line_count") or 0)

    health_flags = {
        "kpi_rows_without_rev_rec_lines": bool(kpi_rows > 0 and rev_lines == 0),
        "has_revenue_recognition_lines": rev_lines > 0,
        "has_financial_kpi_daily_rows": kpi_rows > 0,
        "has_manual_adjustment_lines": manual_lines > 0,
        "has_open_billing_cycles": int((cycles or {}).get("cycles_open_on_date") or 0) > 0,
    }

    ledger_by_type: list[dict] = []
    for row in ledger_rows:
        ledger_by_type.append(
            {
                "entry_type": str(row.get("entry_type") or ""),
                "line_count": int(row.get("n") or 0),
                "amount_cents_abs_sum": int(row.get("amount_sum") or 0),
            }
        )

    return {
        "scope": SCOPE_DAILY_OPERATIONAL_CLOSE,
        "snapshot_date": snapshot_date.isoformat(),
        "currency_filter": cur,
        "summary": {
            "revenue_recognition": {
                "line_count": rev_lines,
                "distinct_partners": int((rev_all or {}).get("distinct_partners") or 0),
                "recognized_cents_total": int((rev_all or {}).get("recognized_cents") or 0),
                "deferred_cents_total": int((rev_all or {}).get("deferred_cents") or 0),
            },
            "manual_adjustments_provisions": {
                "line_count": manual_lines,
                "recognized_cents_total": int((rev_manual or {}).get("recognized_cents") or 0),
                "deferred_cents_total": int((rev_manual or {}).get("deferred_cents") or 0),
            },
            "financial_kpi_daily": {
                "row_count": kpi_rows,
                "distinct_partners": int((kpi or {}).get("distinct_partners") or 0),
                "revenue_recognized_cents_total": int((kpi or {}).get("revenue_recognized_cents") or 0),
                "ar_open_cents_total": int((kpi or {}).get("ar_open_cents") or 0),
            },
            "partner_billing_cycles_open_pipeline": {
                "cycles_open_on_date": int((cycles or {}).get("cycles_open_on_date") or 0),
                "distinct_partners": int((cycles or {}).get("distinct_partners") or 0),
                "pipeline_total_cents": int((cycles or {}).get("pipeline_total_cents") or 0),
            },
            "health_flags": health_flags,
        },
        "ledger_by_entry_type": ledger_by_type,
    }
