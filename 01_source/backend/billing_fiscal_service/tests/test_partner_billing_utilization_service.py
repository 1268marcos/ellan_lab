from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException

from app.api import routes_partner_billing as rpb
from app.services.partner_billing_utilization_service import classify_divergence


class _FakeMappingsResult:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeFetchResult:
    def __init__(self, row: tuple | None):
        self._row = row

    def fetchone(self):
        return self._row


class _FakeDB:
    def execute(self, statement, params=None):
        sql = str(statement)
        if "COUNT(*)" in sql:
            return _FakeFetchResult((0,))
        return _FakeMappingsResult([])


def test_classify_divergence_missing_billing():
    result = classify_divergence(Decimal("12"), Decimal("0"))
    assert result.status == "MISSING_BILLING"
    assert result.difference_hours == Decimal("12")


def test_classify_divergence_under_billed():
    result = classify_divergence(Decimal("10"), Decimal("4"), tolerance_hours=Decimal("0.5"))
    assert result.status == "UNDER_BILLED"
    assert result.difference_hours == Decimal("6")


def test_classify_divergence_over_billed():
    result = classify_divergence(Decimal("8"), Decimal("12"), tolerance_hours=Decimal("0.5"))
    assert result.status == "OVER_BILLED"
    assert result.difference_hours == Decimal("-4")


def test_utilization_invalid_status_returns_standardized_error():
    db = _FakeDB()
    try:
        rpb.list_utilization_divergences(
            snapshot_date=None,
            from_date=None,
            to_date=None,
            partner_id=None,
            locker_id=None,
            country_code=None,
            jurisdiction_code=None,
            divergence_status="NOT_VALID",
            sort_by="snapshot_date",
            sort_order="DESC",
            limit=20,
            offset=0,
            db=db,
            _=None,
        )
        assert False, "Expected HTTPException for invalid utilization status"
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"]["code"] == "INVALID_UTILIZATION_STATUS"

