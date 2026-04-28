from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class FinancialKpi:
    month: date
    partner_id: str
    locker_id: str | None
    revenue_cents: int
    gross_profit_cents: int
    gross_margin_pct: float
    arpl_cents: int
    dso_days: float


@dataclass(frozen=True)
class FinancialKpiDaily:
    snapshot_date: date
    partner_id: str
    locker_id: str | None
    revenue_recognized_cents: int
    ar_open_cents: int
    arpl_cents: int
    gross_margin_pct: float
    dso_days: float


def _month_start(target: date | None) -> date:
    now = target or date.today()
    return date(now.year, now.month, 1)


def _safe_pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 4)


def _safe_dso(ar_open_cents: int, revenue_cents: int, month_days: int = 30) -> float:
    if revenue_cents <= 0:
        return 0.0
    return round((ar_open_cents / revenue_cents) * month_days, 2)


def recompute_monthly_pnl(db: Session, month: date | None = None) -> dict:
    month_start = _month_start(month)

    depreciation_result = db.execute(
        text(
            """
            INSERT INTO ellanlab_depreciation_schedule (
                asset_id,
                depreciation_month,
                partner_id,
                locker_id,
                depreciation_amount_cents,
                accumulated_depreciation_cents,
                nbv_cents,
                currency,
                dedupe_key,
                metadata_json
            )
            SELECT
                a.id,
                :month_start::date,
                a.partner_id,
                a.locker_id,
                GREATEST((a.acquisition_cost_cents - a.residual_value_cents) / a.useful_life_months, 0)::BIGINT,
                GREATEST(
                    LEAST(
                        ((a.acquisition_cost_cents - a.residual_value_cents) / a.useful_life_months)
                        * (
                            (
                                EXTRACT(YEAR FROM AGE(:month_start::date, COALESCE(a.in_service_date, a.acquisition_date)))::INT * 12
                            ) + EXTRACT(MONTH FROM AGE(:month_start::date, COALESCE(a.in_service_date, a.acquisition_date)))::INT + 1
                        ),
                        (a.acquisition_cost_cents - a.residual_value_cents)
                    ),
                    0
                )::BIGINT AS accumulated_depreciation_cents,
                GREATEST(
                    a.residual_value_cents,
                    a.acquisition_cost_cents - LEAST(
                        ((a.acquisition_cost_cents - a.residual_value_cents) / a.useful_life_months)
                        * (
                            (
                                EXTRACT(YEAR FROM AGE(:month_start::date, COALESCE(a.in_service_date, a.acquisition_date)))::INT * 12
                            ) + EXTRACT(MONTH FROM AGE(:month_start::date, COALESCE(a.in_service_date, a.acquisition_date)))::INT + 1
                        ),
                        (a.acquisition_cost_cents - a.residual_value_cents)
                    )
                )::BIGINT AS nbv_cents,
                a.currency,
                CONCAT('dep:', a.id, ':', :month_start::date),
                jsonb_build_object('method', a.depreciation_method)
            FROM ellanlab_hardware_assets a
            WHERE a.status = 'ACTIVE'
              AND COALESCE(a.in_service_date, a.acquisition_date) <= :month_start::date
            ON CONFLICT (asset_id, depreciation_month)
            DO UPDATE SET
                depreciation_amount_cents = EXCLUDED.depreciation_amount_cents,
                accumulated_depreciation_cents = EXCLUDED.accumulated_depreciation_cents,
                nbv_cents = EXCLUDED.nbv_cents,
                updated_at = NOW()
            """
        ),
        {"month_start": month_start.isoformat()},
    )

    pnl_result = db.execute(
        text(
            """
            INSERT INTO ellanlab_monthly_pnl (
                pnl_month,
                partner_id,
                locker_id,
                currency,
                country_code,
                jurisdiction_code,
                revenue_cents,
                cogs_cents,
                opex_cents,
                depreciation_cents,
                gross_profit_cents,
                gross_margin_pct,
                ebitda_cents,
                net_income_cents,
                ar_open_cents,
                dso_days,
                metadata_json
            )
            SELECT
                :month_start::date AS pnl_month,
                src.partner_id,
                src.locker_id,
                src.currency,
                src.country_code,
                src.jurisdiction_code,
                src.revenue_cents,
                src.cogs_cents,
                src.opex_cents,
                src.depreciation_cents,
                (src.revenue_cents - src.cogs_cents) AS gross_profit_cents,
                CASE
                    WHEN src.revenue_cents = 0 THEN 0
                    ELSE ROUND(((src.revenue_cents - src.cogs_cents)::numeric / src.revenue_cents::numeric) * 100, 4)
                END AS gross_margin_pct,
                (src.revenue_cents - src.cogs_cents - src.opex_cents) AS ebitda_cents,
                (src.revenue_cents - src.cogs_cents - src.opex_cents - src.depreciation_cents) AS net_income_cents,
                src.ar_open_cents,
                CASE
                    WHEN src.revenue_cents <= 0 THEN 0
                    ELSE ROUND((src.ar_open_cents::numeric / src.revenue_cents::numeric) * 30, 2)
                END AS dso_days,
                jsonb_build_object('computed_by', 'financial_pnl_service_v1')
            FROM (
                SELECT
                    c.partner_id,
                    c.locker_id,
                    c.currency,
                    c.country_code,
                    c.jurisdiction_code,
                    SUM(c.total_amount_cents)::BIGINT AS revenue_cents,
                    0::BIGINT AS cogs_cents,
                    COALESCE((
                        SELECT SUM(o.amount_cents)::BIGINT
                        FROM ellanlab_opex_entries o
                        WHERE o.partner_id = c.partner_id
                          AND COALESCE(o.locker_id, '') = COALESCE(c.locker_id, '')
                          AND o.expense_month = :month_start::date
                    ), 0::BIGINT) AS opex_cents,
                    COALESCE((
                        SELECT SUM(d.depreciation_amount_cents)::BIGINT
                        FROM ellanlab_depreciation_schedule d
                        WHERE d.partner_id = c.partner_id
                          AND COALESCE(d.locker_id, '') = COALESCE(c.locker_id, '')
                          AND d.depreciation_month = :month_start::date
                          AND d.status = 'POSTED'
                    ), 0::BIGINT) AS depreciation_cents,
                    COALESCE((
                        SELECT SUM(i.amount_cents)::BIGINT
                        FROM partner_b2b_invoices i
                        WHERE i.partner_id = c.partner_id
                          AND i.status IN ('ISSUED', 'SENT', 'VIEWED', 'OVERDUE', 'DISPUTED')
                          AND date_trunc('month', COALESCE(i.issued_at, i.created_at))::date = :month_start::date
                    ), 0::BIGINT) AS ar_open_cents
                FROM partner_billing_cycles c
                WHERE date_trunc('month', c.period_start)::date = :month_start::date
                GROUP BY c.partner_id, c.locker_id, c.currency, c.country_code, c.jurisdiction_code
            ) src
            ON CONFLICT (partner_id, locker_id, pnl_month)
            DO UPDATE SET
                revenue_cents = EXCLUDED.revenue_cents,
                cogs_cents = EXCLUDED.cogs_cents,
                opex_cents = EXCLUDED.opex_cents,
                depreciation_cents = EXCLUDED.depreciation_cents,
                gross_profit_cents = EXCLUDED.gross_profit_cents,
                gross_margin_pct = EXCLUDED.gross_margin_pct,
                ebitda_cents = EXCLUDED.ebitda_cents,
                net_income_cents = EXCLUDED.net_income_cents,
                ar_open_cents = EXCLUDED.ar_open_cents,
                dso_days = EXCLUDED.dso_days,
                metadata_json = EXCLUDED.metadata_json,
                computed_at = NOW(),
                updated_at = NOW()
            """
        ),
        {"month_start": month_start.isoformat()},
    )
    db.commit()
    return {
        "month": month_start.isoformat(),
        "depreciation_upserted": int(depreciation_result.rowcount or 0),
        "pnl_upserted": int(pnl_result.rowcount or 0),
    }


def list_monthly_pnl(db: Session, month: date | None = None, limit: int = 200, offset: int = 0) -> dict:
    month_start = _month_start(month)
    rows = (
        db.execute(
            text(
                """
                SELECT
                    pnl_month,
                    partner_id,
                    locker_id,
                    currency,
                    revenue_cents,
                    gross_profit_cents,
                    gross_margin_pct,
                    ebitda_cents,
                    net_income_cents,
                    ar_open_cents,
                    dso_days
                FROM ellanlab_monthly_pnl
                WHERE pnl_month = :month_start::date
                ORDER BY revenue_cents DESC, partner_id ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            {"month_start": month_start.isoformat(), "limit": int(limit), "offset": int(offset)},
        )
        .mappings()
        .all()
    )
    return {"month": month_start.isoformat(), "count": len(rows), "items": [dict(r) for r in rows]}


def calculate_monthly_kpis(db: Session, month: date | None = None) -> dict:
    month_start = _month_start(month)
    rows = (
        db.execute(
            text(
                """
                SELECT partner_id, locker_id, revenue_cents, gross_profit_cents, ar_open_cents
                FROM ellanlab_monthly_pnl
                WHERE pnl_month = :month_start::date
                """
            ),
            {"month_start": month_start.isoformat()},
        )
        .mappings()
        .all()
    )
    items: list[dict] = []
    for r in rows:
        revenue = int(r.get("revenue_cents") or 0)
        gross_profit = int(r.get("gross_profit_cents") or 0)
        ar_open = int(r.get("ar_open_cents") or 0)
        items.append(
            FinancialKpi(
                month=month_start,
                partner_id=str(r.get("partner_id")),
                locker_id=r.get("locker_id"),
                revenue_cents=revenue,
                gross_profit_cents=gross_profit,
                gross_margin_pct=_safe_pct(gross_profit, revenue),
                arpl_cents=revenue,
                dso_days=_safe_dso(ar_open, revenue),
            ).__dict__
        )
    return {"month": month_start.isoformat(), "count": len(items), "items": items}


def recompute_daily_revenue_recognition(
    db: Session,
    snapshot_date: date | None = None,
    partner_id: str | None = None,
) -> dict:
    target = snapshot_date or date.today()
    partner_filter_sql = "AND i.partner_id = :partner_id" if (partner_id or "").strip() else ""
    result = db.execute(
        text(
            f"""
            INSERT INTO ellanlab_revenue_recognition (
                recognition_date,
                partner_id,
                locker_id,
                source_type,
                source_id,
                recognition_rule,
                recognized_amount_cents,
                deferred_amount_cents,
                currency,
                country_code,
                jurisdiction_code,
                dedupe_key,
                metadata_json
            )
            SELECT
                CAST(:target_date AS DATE),
                i.partner_id,
                c.locker_id,
                'PARTNER_INVOICE',
                i.id,
                'ACCRUAL_DAILY',
                i.amount_cents,
                0,
                i.currency,
                i.country_code,
                i.jurisdiction_code,
                CONCAT('revrec:invoice:', i.id, ':', CAST(:target_date AS DATE)),
                jsonb_build_object('invoice_status', i.status, 'origin', 'partner_b2b_invoices')
            FROM partner_b2b_invoices i
            LEFT JOIN partner_billing_cycles c ON c.id = i.cycle_id
            WHERE COALESCE(i.issued_at::date, i.created_at::date) = CAST(:target_date AS DATE)
              AND i.status IN ('ISSUED', 'SENT', 'VIEWED', 'PAID', 'OVERDUE', 'DISPUTED')
              {partner_filter_sql}
            ON CONFLICT (source_type, source_id, recognition_date)
            DO UPDATE SET
                recognized_amount_cents = EXCLUDED.recognized_amount_cents,
                deferred_amount_cents = EXCLUDED.deferred_amount_cents,
                currency = EXCLUDED.currency,
                country_code = EXCLUDED.country_code,
                jurisdiction_code = EXCLUDED.jurisdiction_code,
                metadata_json = EXCLUDED.metadata_json,
                updated_at = NOW()
            """
        ),
        {"target_date": target.isoformat(), "partner_id": (partner_id or "").strip()},
    )
    db.commit()
    return {"snapshot_date": target.isoformat(), "revenue_recognition_upserted": int(result.rowcount or 0)}


def recompute_daily_kpis(
    db: Session,
    snapshot_date: date | None = None,
    partner_id: str | None = None,
) -> dict:
    target = snapshot_date or date.today()
    partner_filter_sql = "AND rr.partner_id = :partner_id" if (partner_id or "").strip() else ""
    result = db.execute(
        text(
            f"""
            INSERT INTO financial_kpi_daily (
                snapshot_date,
                partner_id,
                locker_id,
                currency,
                country_code,
                jurisdiction_code,
                revenue_recognized_cents,
                ar_open_cents,
                arpl_cents,
                gross_margin_pct,
                dso_days,
                active_invoice_count,
                metadata_json,
                dedupe_key
            )
            SELECT
                CAST(:target_date AS DATE),
                src.partner_id,
                src.locker_id,
                src.currency,
                src.country_code,
                src.jurisdiction_code,
                src.revenue_recognized_cents,
                src.ar_open_cents,
                src.revenue_recognized_cents AS arpl_cents,
                src.gross_margin_pct,
                CASE
                    WHEN src.revenue_recognized_cents <= 0 THEN 0
                    ELSE ROUND((src.ar_open_cents::numeric / src.revenue_recognized_cents::numeric) * 30, 2)
                END AS dso_days,
                src.active_invoice_count,
                jsonb_build_object('computed_by', 'financial_pnl_service_v2_daily'),
                CONCAT('kpi:', src.partner_id, ':', COALESCE(src.locker_id, 'GLOBAL'), ':', CAST(:target_date AS DATE))
            FROM (
                SELECT
                    rr.partner_id,
                    rr.locker_id,
                    MAX(rr.currency) AS currency,
                    MAX(rr.country_code) AS country_code,
                    MAX(rr.jurisdiction_code) AS jurisdiction_code,
                    SUM(rr.recognized_amount_cents)::BIGINT AS revenue_recognized_cents,
                    COALESCE((
                        SELECT SUM(i.amount_cents)::BIGINT
                        FROM partner_b2b_invoices i
                        LEFT JOIN partner_billing_cycles c ON c.id = i.cycle_id
                        WHERE i.partner_id = rr.partner_id
                          AND COALESCE(c.locker_id, '') = COALESCE(rr.locker_id, '')
                          AND i.status IN ('ISSUED', 'SENT', 'VIEWED', 'OVERDUE', 'DISPUTED')
                          AND COALESCE(i.issued_at::date, i.created_at::date) <= CAST(:target_date AS DATE)
                    ), 0::BIGINT) AS ar_open_cents,
                    COALESCE((
                        SELECT p.gross_margin_pct
                        FROM ellanlab_monthly_pnl p
                        WHERE p.partner_id = rr.partner_id
                          AND COALESCE(p.locker_id, '') = COALESCE(rr.locker_id, '')
                          AND p.pnl_month = date_trunc('month', CAST(:target_date AS DATE))::date
                        LIMIT 1
                    ), 0::numeric) AS gross_margin_pct,
                    COALESCE((
                        SELECT COUNT(*)::INT
                        FROM partner_b2b_invoices i
                        LEFT JOIN partner_billing_cycles c ON c.id = i.cycle_id
                        WHERE i.partner_id = rr.partner_id
                          AND COALESCE(c.locker_id, '') = COALESCE(rr.locker_id, '')
                          AND i.status IN ('ISSUED', 'SENT', 'VIEWED', 'OVERDUE', 'DISPUTED')
                    ), 0) AS active_invoice_count
                FROM ellanlab_revenue_recognition rr
                WHERE rr.recognition_date = CAST(:target_date AS DATE)
                  {partner_filter_sql}
                GROUP BY rr.partner_id, rr.locker_id
            ) src
            ON CONFLICT (partner_id, locker_id, snapshot_date)
            DO UPDATE SET
                currency = EXCLUDED.currency,
                country_code = EXCLUDED.country_code,
                jurisdiction_code = EXCLUDED.jurisdiction_code,
                revenue_recognized_cents = EXCLUDED.revenue_recognized_cents,
                ar_open_cents = EXCLUDED.ar_open_cents,
                arpl_cents = EXCLUDED.arpl_cents,
                gross_margin_pct = EXCLUDED.gross_margin_pct,
                dso_days = EXCLUDED.dso_days,
                active_invoice_count = EXCLUDED.active_invoice_count,
                metadata_json = EXCLUDED.metadata_json,
                dedupe_key = EXCLUDED.dedupe_key,
                computed_at = NOW(),
                updated_at = NOW()
            """
        ),
        {"target_date": target.isoformat(), "partner_id": (partner_id or "").strip()},
    )
    db.commit()
    return {"snapshot_date": target.isoformat(), "kpi_daily_upserted": int(result.rowcount or 0)}


def list_revenue_recognition(
    db: Session,
    from_date: date | None = None,
    to_date: date | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict:
    fdate = from_date or date.today()
    tdate = to_date or fdate
    rows = (
        db.execute(
            text(
                """
                SELECT
                    recognition_date,
                    partner_id,
                    locker_id,
                    source_type,
                    source_id,
                    recognized_amount_cents,
                    deferred_amount_cents,
                    currency
                FROM ellanlab_revenue_recognition
                WHERE recognition_date BETWEEN :from_date::date AND :to_date::date
                ORDER BY recognition_date DESC, created_at DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "from_date": fdate.isoformat(),
                "to_date": tdate.isoformat(),
                "limit": int(limit),
                "offset": int(offset),
            },
        )
        .mappings()
        .all()
    )
    return {
        "from_date": fdate.isoformat(),
        "to_date": tdate.isoformat(),
        "count": len(rows),
        "items": [dict(r) for r in rows],
    }


def list_daily_kpis(db: Session, snapshot_date: date | None = None, limit: int = 200, offset: int = 0) -> dict:
    target = snapshot_date or date.today()
    rows = (
        db.execute(
            text(
                """
                SELECT
                    snapshot_date,
                    partner_id,
                    locker_id,
                    currency,
                    revenue_recognized_cents,
                    ar_open_cents,
                    arpl_cents,
                    gross_margin_pct,
                    dso_days,
                    active_invoice_count
                FROM financial_kpi_daily
                WHERE snapshot_date = :snapshot_date::date
                ORDER BY revenue_recognized_cents DESC, partner_id ASC
                LIMIT :limit OFFSET :offset
                """
            ),
            {
                "snapshot_date": target.isoformat(),
                "limit": int(limit),
                "offset": int(offset),
            },
        )
        .mappings()
        .all()
    )
    items: list[dict] = []
    for r in rows:
        items.append(
            FinancialKpiDaily(
                snapshot_date=target,
                partner_id=str(r.get("partner_id")),
                locker_id=r.get("locker_id"),
                revenue_recognized_cents=int(r.get("revenue_recognized_cents") or 0),
                ar_open_cents=int(r.get("ar_open_cents") or 0),
                arpl_cents=int(r.get("arpl_cents") or 0),
                gross_margin_pct=float(r.get("gross_margin_pct") or 0),
                dso_days=float(r.get("dso_days") or 0),
            ).__dict__
            | {"active_invoice_count": int(r.get("active_invoice_count") or 0), "currency": r.get("currency")}
        )
    return {"snapshot_date": target.isoformat(), "count": len(items), "items": items}
