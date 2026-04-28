from __future__ import annotations

from fastapi import HTTPException

from app.api import routes_partner_billing as rpb


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


class _FakeDBWithRows:
    def __init__(self):
        self._cycle_rows = [
            {
                "id": "cycle_001",
                "partner_id": "partner_test",
                "status": "DISPUTED",
                "currency": "USD",
                "country_code": "US",
                "jurisdiction_code": "US-CA",
                "period_timezone": "America/Los_Angeles",
                "period_start": "2026-04-01",
                "period_end": "2026-04-30",
                "total_amount_cents": 120000,
                "dedupe_key": "cycle_compute:partner_test:US:US-CA:2026-04-01:2026-04-30",
                "computed_at": "2026-04-28T00:00:00+00:00",
            }
        ]

    def execute(self, statement, params=None):
        sql = str(statement)
        if "COUNT(*)" in sql and "partner_billing_cycles" in sql:
            return _FakeFetchResult((1,))
        if "FROM partner_billing_cycles" in sql:
            return _FakeMappingsResult(self._cycle_rows)
        if "COUNT(*)" in sql:
            return _FakeFetchResult((0,))
        return _FakeMappingsResult([])


def test_invoices_invalid_status_returns_standardized_error():
    db = _FakeDB()
    try:
        rpb.list_partner_b2b_invoices(
            partner_id="partner_test",
            status="INVALID_STATUS",
            from_date=None,
            to_date=None,
            country_code=None,
            jurisdiction_code=None,
            document_type=None,
            sort_by="created_at",
            sort_order="DESC",
            limit=100,
            offset=0,
            db=db,
            _=None,
        )
        assert False, "Expected HTTPException for invalid status"
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"]["code"] == "INVALID_INVOICE_STATUS"


def test_credit_notes_invalid_sort_field_returns_standardized_error():
    db = _FakeDB()
    try:
        rpb.list_partner_credit_notes(
            partner_id="partner_test",
            status=None,
            reason_code=None,
            country_code=None,
            jurisdiction_code=None,
            sort_by="hacker_field",
            sort_order="DESC",
            limit=100,
            offset=0,
            db=db,
            _=None,
        )
        assert False, "Expected HTTPException for invalid sort field"
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"]["code"] == "INVALID_SORT_FIELD"


def test_cycles_valid_sort_and_status_returns_paginated_payload():
    db = _FakeDB()
    out = rpb.list_partner_cycles(
        partner_id="partner_test",
        year=None,
        status="DISPUTED",
        country_code="US",
        jurisdiction_code="US-CA",
        from_date=None,
        to_date=None,
        sort_by="total_amount_cents",
        sort_order="DESC",
        limit=10,
        offset=0,
        db=db,
        _=None,
    )
    assert out["count"] == 0
    assert out["total"] == 0
    assert out["limit"] == 10
    assert out["offset"] == 0
    assert out["sort_by"] == "total_amount_cents"
    assert out["sort_order"] == "DESC"


def test_cycles_invalid_sort_order_returns_standardized_error():
    db = _FakeDB()
    try:
        rpb.list_partner_cycles(
            partner_id="partner_test",
            year=None,
            status=None,
            country_code=None,
            jurisdiction_code=None,
            from_date=None,
            to_date=None,
            sort_by="period_start",
            sort_order="DROP_TABLE",
            limit=10,
            offset=0,
            db=db,
            _=None,
        )
        assert False, "Expected HTTPException for invalid sort order"
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"]["code"] == "INVALID_SORT_ORDER"


def test_credit_notes_invalid_reason_code_returns_standardized_error():
    db = _FakeDB()
    try:
        rpb.list_partner_credit_notes(
            partner_id="partner_test",
            status=None,
            reason_code="NOT_ALLOWED",
            country_code=None,
            jurisdiction_code=None,
            sort_by="created_at",
            sort_order="DESC",
            limit=100,
            offset=0,
            db=db,
            _=None,
        )
        assert False, "Expected HTTPException for invalid reason code"
    except HTTPException as exc:
        assert exc.status_code == 422
        assert exc.detail["error"]["code"] == "INVALID_CREDIT_NOTE_REASON_CODE"


def test_cycles_filters_with_pagination_returns_expected_contract():
    db = _FakeDBWithRows()
    out = rpb.list_partner_cycles(
        partner_id="partner_test",
        year=2026,
        status="DISPUTED",
        country_code="US",
        jurisdiction_code="US-CA",
        from_date="2026-04-01",
        to_date="2026-04-30",
        sort_by="total_amount_cents",
        sort_order="DESC",
        limit=1,
        offset=0,
        db=db,
        _=None,
    )
    assert out["count"] == 1
    assert out["total"] == 1
    assert out["limit"] == 1
    assert out["offset"] == 0
    assert out["sort_by"] == "total_amount_cents"
    assert out["sort_order"] == "DESC"
    assert out["items"][0].id == "cycle_001"
