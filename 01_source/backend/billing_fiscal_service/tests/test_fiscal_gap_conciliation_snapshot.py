"""Sprint 2 P0 Fiscal: GET /admin/fiscal/fiscal-gap-conciliation-snapshot + agregados de gaps."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from fastapi import HTTPException

from app.api.routes_admin_fiscal import get_fiscal_gap_conciliation_snapshot
from app.services.fiscal_gap_conciliation_snapshot_service import (
    SCOPE_FISCAL_GAP_CONCILIATION_SNAPSHOT,
    build_fiscal_gap_conciliation_snapshot,
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


class _FakeDBGapSnapshot:
    def execute(self, statement, params=None):
        s = str(statement)
        if "details_json->>'partner_id'" in s:
            return _FakeResult(
                rows=[
                    {"partner_bucket": "partner_demo_001", "n": 2},
                    {"partner_bucket": "UNKNOWN", "n": 1},
                ]
            )
        if "ORDER BY last_detected_at DESC" in s and "LIMIT 40" in s:
            ts = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
            return _FakeResult(
                rows=[
                    {
                        "id": "g1",
                        "dedupe_key": "k1",
                        "gap_type": "PAID_WITHOUT_INVOICE",
                        "severity": "ERROR",
                        "status": "OPEN",
                        "order_id": "ord1",
                        "invoice_id": None,
                        "details_json": {"partner_id": "partner_demo_001"},
                        "first_detected_at": ts,
                        "last_detected_at": ts,
                    },
                ]
            )
        if "GROUP BY gap_type" in s:
            return _FakeResult(rows=[{"gap_type": "PAID_WITHOUT_INVOICE", "n": 2}, {"gap_type": "ISSUED_WITHOUT_PAID", "n": 1}])
        if "GROUP BY severity" in s:
            return _FakeResult(rows=[{"severity": "ERROR", "n": 3}])
        if "first_detected_at AT TIME ZONE 'UTC'" in s:
            return _FakeResult(first={"c": 5})
        if "WHERE status = 'OPEN'" in s and "COUNT(*)" in s and "GROUP BY" not in s:
            return _FakeResult(first={"c": 3})
        raise AssertionError(f"SQL inesperado (fiscal gap snapshot): {s[:600]}")


def test_build_fiscal_gap_conciliation_snapshot_structure():
    out = build_fiscal_gap_conciliation_snapshot(_FakeDBGapSnapshot(), snapshot_date=date(2026, 5, 1), refresh_scan=False)
    assert out["scope"] == SCOPE_FISCAL_GAP_CONCILIATION_SNAPSHOT
    assert out["snapshot_date"] == "2026-05-01"
    assert out["refreshed_scan"] is False
    assert out["summary"]["open_gaps_total"] == 3
    assert out["summary"]["first_detected_on_snapshot_date_total"] == 5
    assert len(out["summary"]["by_gap_type"]) == 2
    assert len(out["summary"]["by_partner_id"]) == 2
    assert out["summary"]["by_partner_id"][0]["partner_id"] == "partner_demo_001"
    assert len(out["sample_open_gaps"]) == 1
    assert out["sample_open_gaps"][0]["gap_type"] == "PAID_WITHOUT_INVOICE"


def test_get_fiscal_gap_conciliation_snapshot_route_ok():
    out = get_fiscal_gap_conciliation_snapshot(date="2026-05-01", refresh=False, db=_FakeDBGapSnapshot(), _=None)
    assert out["ok"] is True
    assert out["scope"] == SCOPE_FISCAL_GAP_CONCILIATION_SNAPSHOT


def test_get_fiscal_gap_conciliation_snapshot_invalid_date():
    with pytest.raises(HTTPException) as ei:
        get_fiscal_gap_conciliation_snapshot(date="nope", refresh=False, db=_FakeDBGapSnapshot(), _=None)
    assert ei.value.status_code == 400
