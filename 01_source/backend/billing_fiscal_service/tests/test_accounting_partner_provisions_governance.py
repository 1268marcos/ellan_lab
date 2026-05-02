"""P0 Contábil Partners: GET /admin/fiscal/accounting/partner-provisions-governance."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_accounting_partner_provisions_governance
from app.services.accounting_partner_provisions_governance_service import (
    SCOPE_PARTNER_PROVISIONS_GOVERNANCE,
    build_partner_provisions_governance_report,
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


class _FakeDBProvGov:
    def __init__(self):
        self.totals = {
            "total_lines": 5,
            "distinct_partners": 2,
            "recognized_cents": 1_200,
            "deferred_cents": 300,
        }
        self.missing_owner = {"n": 1}
        self.by_rule = [
            {
                "recognition_rule": "MANUAL",
                "line_count": 4,
                "recognized_cents": 1000,
                "deferred_cents": 200,
            },
            {
                "recognition_rule": "ACCRUAL_DAILY",
                "line_count": 1,
                "recognized_cents": 200,
                "deferred_cents": 100,
            },
        ]
        self.per_partner = [
            {
                "partner_id": "p_alpha",
                "manual_lines": 3,
                "recognized_cents": 900,
                "deferred_cents": 200,
                "last_adjustment_date": "2026-05-01",
            },
            {
                "partner_id": "p_beta",
                "manual_lines": 2,
                "recognized_cents": 300,
                "deferred_cents": 100,
                "last_adjustment_date": "2026-04-28",
            },
        ]

    def execute(self, statement, params=None):
        s = str(statement)
        if "metadata_json->>'governance_owner'" in s:
            return _FakeResult(first=self.missing_owner)
        if "GROUP BY recognition_rule" in s:
            return _FakeResult(rows=self.by_rule)
        if "GROUP BY partner_id" in s and "LIMIT" in s:
            return _FakeResult(rows=self.per_partner)
        if "FROM ellanlab_revenue_recognition" in s and "COUNT(*)" in s and "DISTINCT partner_id" in s:
            return _FakeResult(first=self.totals)
        raise AssertionError(f"SQL inesperado (partner provisions governance): {s[:500]}")


def test_build_partner_provisions_governance_report():
    out = build_partner_provisions_governance_report(_FakeDBProvGov(), as_of_date=date(2026, 5, 2), currency=None, partner_limit=50)
    assert out["scope"] == SCOPE_PARTNER_PROVISIONS_GOVERNANCE
    assert out["summary"]["total_manual_lines"] == 5
    assert out["summary"]["manual_lines_missing_governance_owner"] == 1
    assert out["summary"]["governance_owner_coverage_pct"] == 80.0
    assert len(out["per_partner"]) == 2


def test_get_accounting_partner_provisions_governance_route_ok():
    out = get_accounting_partner_provisions_governance(
        date="2026-05-02",
        currency=None,
        partner_limit=50,
        db=_FakeDBProvGov(),
        _=None,
    )
    assert out["ok"] is True
    assert out["scope"] == SCOPE_PARTNER_PROVISIONS_GOVERNANCE


def test_get_accounting_partner_provisions_governance_invalid_date():
    with pytest.raises(HTTPException) as ei:
        get_accounting_partner_provisions_governance(
            date="x",
            currency=None,
            partner_limit=50,
            db=_FakeDBProvGov(),
            _=None,
        )
    assert ei.value.status_code == 400
