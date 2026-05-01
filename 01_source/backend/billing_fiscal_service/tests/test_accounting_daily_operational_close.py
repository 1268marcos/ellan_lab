"""Sprint 2 D14: GET /admin/fiscal/accounting/daily-operational-close + agregados de fechamento diário."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_accounting_daily_operational_close
from app.services.accounting_daily_operational_close_service import (
    SCOPE_DAILY_OPERATIONAL_CLOSE,
    build_daily_operational_close_report,
)


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


class _FakeDBDailyClose:
    def __init__(self):
        self.rev_all = {
            "line_count": 10,
            "distinct_partners": 3,
            "recognized_cents": 50_000,
            "deferred_cents": 100,
        }
        self.rev_manual = {
            "line_count": 1,
            "recognized_cents": 500,
            "deferred_cents": 0,
        }
        self.kpi = {
            "row_count": 4,
            "distinct_partners": 2,
            "revenue_recognized_cents": 48_000,
            "ar_open_cents": 12_000,
        }
        self.ledger = [
            {"entry_type": "BILLING_REVENUE", "n": 2, "amount_sum": 9000},
            {"entry_type": "BILLING_REVERSAL", "n": 1, "amount_sum": 500},
        ]
        self.cycles = {
            "cycles_open_on_date": 5,
            "distinct_partners": 2,
            "pipeline_total_cents": 20_000,
        }

    def execute(self, statement, params=None):
        s = str(statement)
        if "FROM ellanlab_revenue_recognition" in s and "MANUAL_ADJUSTMENT" in s:
            return _FakeResult(first=self.rev_manual)
        if "FROM ellanlab_revenue_recognition" in s:
            return _FakeResult(first=self.rev_all)
        if "FROM financial_kpi_daily" in s:
            return _FakeResult(first=self.kpi)
        if "FROM financial_ledger" in s and "GROUP BY entry_type" in s:
            return _FakeResult(rows=self.ledger)
        if "FROM partner_billing_cycles" in s and "period_start <=" in s:
            return _FakeResult(first=self.cycles)
        raise AssertionError(f"SQL inesperado (D14 daily close): {s[:500]}")


def test_build_daily_operational_close_report_structure():
    out = build_daily_operational_close_report(_FakeDBDailyClose(), snapshot_date=date(2026, 5, 3), currency=None)
    assert out["scope"] == SCOPE_DAILY_OPERATIONAL_CLOSE
    assert out["summary"]["revenue_recognition"]["line_count"] == 10
    assert out["summary"]["manual_adjustments_provisions"]["line_count"] == 1
    assert out["summary"]["health_flags"]["has_manual_adjustment_lines"] is True
    assert len(out["ledger_by_entry_type"]) == 2


def test_get_accounting_daily_operational_close_route_ok():
    out = get_accounting_daily_operational_close(date="2026-05-03", currency=None, db=_FakeDBDailyClose(), _=None)
    assert out["ok"] is True
    assert out["scope"] == SCOPE_DAILY_OPERATIONAL_CLOSE


def test_get_accounting_daily_operational_close_invalid_date():
    with pytest.raises(HTTPException) as ei:
        get_accounting_daily_operational_close(date="nope", currency=None, db=_FakeDBDailyClose(), _=None)
    assert ei.value.status_code == 400
