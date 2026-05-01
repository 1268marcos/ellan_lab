"""Sprint 2 D15: GET /admin/fiscal/accounting/revenue-credits-delta + serviço de agregação."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_accounting_revenue_credits_delta
from app.services.accounting_revenue_credits_delta_service import build_revenue_credits_delta_report


class _FakeResult:
    def __init__(self, *, first=None, rows=None):
        self._first = first
        self._rows = rows or []

    def mappings(self):
        return self

    def first(self):
        return self._first

    def all(self):
        return self._rows


class _FakeDBDelta:
    def __init__(self):
        self.rev_first = {
            "line_count": 2,
            "recognized_total": 5000,
            "deferred_total": 100,
        }
        self.agg_rows = [
            {"entry_type": "BILLING_REVENUE", "n": 1, "amount_sum": 5000},
            {"entry_type": "BILLING_REVERSAL", "n": 1, "amount_sum": 200},
            {"entry_type": "CREDIT_NOTE_APPLIED", "n": 1, "amount_sum": 100},
        ]
        self.sample_rows = [
            {
                "id": "fl_1",
                "entry_type": "BILLING_REVERSAL",
                "amount_cents": 200,
                "currency": "BRL",
                "external_reference": "acct:PARTNER_INVOICE_CANCELLED:x:y",
                "metadata": {"event_type": "PARTNER_INVOICE_CANCELLED"},
                "created_at": None,
            }
        ]

    def execute(self, statement, params=None):
        s = str(statement)
        if "ellanlab_revenue_recognition" in s and "SUM(recognized_amount_cents)" in s:
            return _FakeResult(first=self.rev_first)
        if "GROUP BY entry_type" in s:
            return _FakeResult(rows=self.agg_rows)
        if "FROM financial_ledger" in s and "LIMIT :lim" in s:
            return _FakeResult(rows=self.sample_rows)
        raise AssertionError(f"SQL inesperado (delta D15): {s[:400]}")


def test_build_revenue_credits_delta_report_aggregates_and_residual():
    db = _FakeDBDelta()
    out = build_revenue_credits_delta_report(db, snapshot_date=date(2026, 5, 1), currency=None, ledger_sample_limit=10)
    assert out["scope"] == "SPRINT2_D15_REVENUE_CREDITS_DELTA"
    assert out["summary"]["recognized_revenue_cents_total"] == 5000
    assert out["summary"]["ledger_reversal_cents"] == 200
    assert out["summary"]["ledger_credit_note_cents"] == 100
    assert out["summary"]["divergence_residual_pct"] == pytest.approx(6.0)
    assert len(out["ledger_entries_sample"]) == 1


def test_get_accounting_revenue_credits_delta_route_wraps_ok():
    db = _FakeDBDelta()
    out = get_accounting_revenue_credits_delta(
        date="2026-05-01",
        currency=None,
        ledger_sample_limit=10,
        db=db,
        _=None,
    )
    assert out["ok"] is True
    assert out["scope"] == "SPRINT2_D15_REVENUE_CREDITS_DELTA"


def test_get_accounting_revenue_credits_delta_invalid_date():
    with pytest.raises(HTTPException) as ei:
        get_accounting_revenue_credits_delta(date="not-a-date", currency=None, ledger_sample_limit=10, db=_FakeDBDelta(), _=None)
    assert ei.value.status_code == 400
