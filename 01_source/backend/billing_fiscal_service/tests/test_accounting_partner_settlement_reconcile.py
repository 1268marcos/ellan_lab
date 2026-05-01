"""Sprint 2 P0: GET /admin/fiscal/accounting/partner-settlement-reconcile + agregação por parceiro."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_accounting_partner_settlement_reconcile
from app.services.accounting_partner_settlement_reconcile_service import (
    SCOPE_PARTNER_SETTLEMENT_RECONCILE,
    build_partner_settlement_reconcile_report,
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


class _FakeDBPartnerReconcile:
    def __init__(self):
        self.cycle_rows = [
            {
                "partner_id": "p1",
                "cycles_computed_on_date": 2,
                "cycle_total_cents_computed_on_date": 10_000,
            },
            {
                "partner_id": "p2",
                "cycles_computed_on_date": 1,
                "cycle_total_cents_computed_on_date": 3000,
            },
        ]
        self.ledger_rows = [
            {"partner_id": "p1", "ledger_lines_on_date": 2, "ledger_billing_cents_on_date": 10_000},
            {"partner_id": "p2", "ledger_lines_on_date": 1, "ledger_billing_cents_on_date": 2500},
        ]
        self.orphan_first = {"n": 1}

    def execute(self, statement, params=None):
        s = str(statement)
        if "FROM partner_billing_cycles" in s and "GROUP BY partner_id" in s and "financial_ledger" not in s:
            return _FakeResult(rows=self.cycle_rows)
        if "FROM financial_ledger fl" in s and "INNER JOIN partner_billing_cycles" in s:
            return _FakeResult(rows=self.ledger_rows)
        if "NOT EXISTS" in s:
            return _FakeResult(first=self.orphan_first)
        raise AssertionError(f"SQL inesperado (partner settlement): {s[:500]}")


def test_build_partner_settlement_reconcile_merges_and_residuals():
    db = _FakeDBPartnerReconcile()
    out = build_partner_settlement_reconcile_report(db, snapshot_date=date(2026, 5, 2), currency=None, partner_limit=50)
    assert out["scope"] == SCOPE_PARTNER_SETTLEMENT_RECONCILE
    assert out["summary"]["distinct_partners"] == 2
    assert out["summary"]["orphan_ledger_lines_partner_cycle_ref"] == 1
    assert out["summary"]["partners_with_nonzero_residual"] == 1
    assert out["summary"]["max_residual_cents_across_partners"] == 500
    p2 = next(r for r in out["per_partner"] if r["partner_id"] == "p2")
    assert p2["residual_cents"] == 500


def test_get_accounting_partner_settlement_reconcile_route_ok():
    db = _FakeDBPartnerReconcile()
    out = get_accounting_partner_settlement_reconcile(
        date="2026-05-02",
        currency=None,
        partner_limit=50,
        db=db,
        _=None,
    )
    assert out["ok"] is True
    assert out["scope"] == SCOPE_PARTNER_SETTLEMENT_RECONCILE


def test_get_accounting_partner_settlement_reconcile_invalid_date():
    with pytest.raises(HTTPException) as ei:
        get_accounting_partner_settlement_reconcile(
            date="bad",
            currency=None,
            partner_limit=50,
            db=_FakeDBPartnerReconcile(),
            _=None,
        )
    assert ei.value.status_code == 400
