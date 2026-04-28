from __future__ import annotations

from datetime import date
from uuid import uuid4

from sqlalchemy import text

from app.core.db import SessionLocal
from app.services.financial_pnl_service import recompute_daily_kpis, recompute_daily_revenue_recognition


def _seed_invoice_for_fa5_invariants(db, partner_id: str, cycle_id: str, invoice_id: str, target_date: date) -> None:
    db.execute(
        text(
            """
            INSERT INTO partner_billing_plans (
                id,
                partner_id,
                partner_type,
                plan_name,
                billing_model,
                currency,
                valid_from
            )
            VALUES (
                :plan_id,
                :partner_id,
                'ENTERPRISE',
                'pytest-fa5-plan',
                'HYBRID',
                'BRL',
                :valid_from
            )
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "plan_id": "pytest-plan-fa5",
            "partner_id": partner_id,
            "valid_from": target_date.replace(day=1).isoformat(),
        },
    )

    db.execute(
        text(
            """
            INSERT INTO partner_billing_cycles (
                id,
                partner_id,
                locker_id,
                partner_type,
                billing_plan_id,
                currency,
                period_start,
                period_end,
                total_amount_cents,
                status
            )
            VALUES (
                :cycle_id,
                :partner_id,
                :locker_id,
                'ENTERPRISE',
                :plan_id,
                'BRL',
                :period_start,
                :period_end,
                :total_amount_cents,
                'REVIEW'
            )
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "cycle_id": cycle_id,
            "partner_id": partner_id,
            "locker_id": "pytest-locker-fa5",
            "plan_id": "pytest-plan-fa5",
            "period_start": target_date.replace(day=1).isoformat(),
            "period_end": target_date.isoformat(),
            "total_amount_cents": 10000,
        },
    )

    db.execute(
        text(
            """
            INSERT INTO partner_b2b_invoices (
                id,
                cycle_id,
                partner_id,
                document_type,
                amount_cents,
                currency,
                status,
                issued_at
            )
            VALUES (
                :invoice_id,
                :cycle_id,
                :partner_id,
                'INVOICE',
                :amount_cents,
                'BRL',
                'ISSUED',
                :issued_at
            )
            ON CONFLICT (id) DO NOTHING
            """
        ),
        {
            "invoice_id": invoice_id,
            "cycle_id": cycle_id,
            "partner_id": partner_id,
            "amount_cents": 10000,
            "issued_at": f"{target_date.isoformat()}T12:00:00+00:00",
        },
    )
    db.commit()


def _cleanup_seed(db, partner_id: str) -> None:
    db.rollback()
    db.execute(text("DELETE FROM financial_kpi_daily WHERE partner_id = :partner_id"), {"partner_id": partner_id})
    db.execute(text("DELETE FROM ellanlab_revenue_recognition WHERE partner_id = :partner_id"), {"partner_id": partner_id})
    db.execute(text("DELETE FROM partner_b2b_invoices WHERE partner_id = :partner_id"), {"partner_id": partner_id})
    db.execute(text("DELETE FROM partner_billing_cycles WHERE partner_id = :partner_id"), {"partner_id": partner_id})
    db.execute(text("DELETE FROM partner_billing_plans WHERE partner_id = :partner_id"), {"partner_id": partner_id})
    db.commit()


def test_fa5_sql_invariants_dedupe_and_non_negative():
    db = SessionLocal()
    partner_id = f"pytest-fa5-{uuid4().hex[:12]}"
    cycle_id = f"cycle-{uuid4().hex[:10]}"
    invoice_id = f"inv-{uuid4().hex[:10]}"
    target_date = date.today()
    try:
        _seed_invoice_for_fa5_invariants(db, partner_id=partner_id, cycle_id=cycle_id, invoice_id=invoice_id, target_date=target_date)
        recompute_daily_revenue_recognition(db, snapshot_date=target_date, partner_id=partner_id)
        recompute_daily_revenue_recognition(db, snapshot_date=target_date, partner_id=partner_id)  # idempotência: não duplica
        recompute_daily_kpis(db, snapshot_date=target_date, partner_id=partner_id)
        recompute_daily_kpis(db, snapshot_date=target_date, partner_id=partner_id)  # idempotência: não duplica

        duplicate_err = db.execute(
            text(
                """
                SELECT COUNT(*) FROM (
                    SELECT dedupe_key
                    FROM ellanlab_revenue_recognition
                    WHERE partner_id = :partner_id AND dedupe_key IS NOT NULL
                    GROUP BY dedupe_key
                    HAVING COUNT(*) > 1
                ) d
                """
            ),
            {"partner_id": partner_id},
        ).scalar_one()
        assert int(duplicate_err) == 0

        duplicate_fkd = db.execute(
            text(
                """
                SELECT COUNT(*) FROM (
                    SELECT dedupe_key
                    FROM financial_kpi_daily
                    WHERE partner_id = :partner_id AND dedupe_key IS NOT NULL
                    GROUP BY dedupe_key
                    HAVING COUNT(*) > 1
                ) d
                """
            ),
            {"partner_id": partner_id},
        ).scalar_one()
        assert int(duplicate_fkd) == 0

        negative_err = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM ellanlab_revenue_recognition
                WHERE partner_id = :partner_id
                  AND (recognized_amount_cents < 0 OR deferred_amount_cents < 0)
                """
            ),
            {"partner_id": partner_id},
        ).scalar_one()
        assert int(negative_err) == 0
    finally:
        _cleanup_seed(db, partner_id)
        db.close()


def test_fa5_sql_invariants_dso_formula_consistency():
    db = SessionLocal()
    partner_id = f"pytest-fa5-{uuid4().hex[:12]}"
    cycle_id = f"cycle-{uuid4().hex[:10]}"
    invoice_id = f"inv-{uuid4().hex[:10]}"
    target_date = date.today()
    try:
        _seed_invoice_for_fa5_invariants(db, partner_id=partner_id, cycle_id=cycle_id, invoice_id=invoice_id, target_date=target_date)
        recompute_daily_revenue_recognition(db, snapshot_date=target_date, partner_id=partner_id)
        recompute_daily_kpis(db, snapshot_date=target_date, partner_id=partner_id)

        mismatched_dso = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM financial_kpi_daily
                WHERE partner_id = :partner_id
                  AND (
                    CASE
                      WHEN revenue_recognized_cents <= 0 THEN dso_days <> 0
                      ELSE ABS(dso_days - ROUND((ar_open_cents::numeric / revenue_recognized_cents::numeric) * 30, 2)) > 0.01
                    END
                  )
                """
            ),
            {"partner_id": partner_id},
        ).scalar_one()
        assert int(mismatched_dso) == 0
    finally:
        _cleanup_seed(db, partner_id)
        db.close()
