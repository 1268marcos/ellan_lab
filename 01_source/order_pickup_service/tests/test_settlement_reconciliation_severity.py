"""Testes unitarios das regras de severidade e filtro min_severity (sem DB)."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.routers.partners import (
    _parse_min_settlement_severity,
    _settlement_reconciliation_severity,
    _settlement_severity_meets_minimum,
)


@pytest.mark.parametrize(
    "d_orders,d_gross,d_share,expected",
    [
        (0, -1, 0, "HIGH"),
        (0, 100, 0, "HIGH"),
        (2, 0, 40, "MEDIUM"),
        (0, 0, 15, "MEDIUM"),
        (0, 0, 5, "LOW"),
        (0, 0, 0, "MEDIUM"),
    ],
)
def test_settlement_reconciliation_severity(d_orders, d_gross, d_share, expected):
    assert (
        _settlement_reconciliation_severity(
            delta_total_orders=d_orders,
            delta_gross_revenue_cents=d_gross,
            delta_revenue_share_cents=d_share,
        )
        == expected
    )


def test_parse_min_severity_none_and_invalid():
    assert _parse_min_settlement_severity(None) is None
    assert _parse_min_settlement_severity("") is None
    assert _parse_min_settlement_severity("  high  ") == "HIGH"
    with pytest.raises(HTTPException) as exc:
        _parse_min_settlement_severity("FOO")
    assert exc.value.status_code == 422
    assert exc.value.detail["type"] == "INVALID_MIN_SEVERITY"


@pytest.mark.parametrize(
    "severity,min_sev,expected",
    [
        ("HIGH", "HIGH", True),
        ("MEDIUM", "HIGH", False),
        ("LOW", "HIGH", False),
        ("HIGH", "MEDIUM", True),
        ("MEDIUM", "MEDIUM", True),
        ("LOW", "MEDIUM", False),
        ("HIGH", "LOW", True),
        ("MEDIUM", "LOW", True),
        ("LOW", "LOW", True),
        ("HIGH", None, True),
    ],
)
def test_settlement_severity_meets_minimum(severity, min_sev, expected):
    assert _settlement_severity_meets_minimum(severity=severity, min_severity=min_sev) is expected
