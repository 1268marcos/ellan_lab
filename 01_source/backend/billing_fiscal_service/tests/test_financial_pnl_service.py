from __future__ import annotations

from datetime import date

from app.services.financial_pnl_service import _month_start, _safe_dso, _safe_pct


def test_month_start_normalizes_date():
    out = _month_start(date(2026, 4, 28))
    assert out == date(2026, 4, 1)


def test_safe_pct_handles_zero_denominator():
    assert _safe_pct(100, 0) == 0.0
    assert _safe_pct(50, 200) == 25.0


def test_safe_dso_handles_non_positive_revenue():
    assert _safe_dso(1000, 0) == 0.0
    assert _safe_dso(15000, 30000, month_days=30) == 15.0
