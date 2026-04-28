from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from app.api import routes_admin_fiscal as raf


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
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def execute(self, statement, params=None):
        sql = str(statement)
        if "COUNT(*)" in sql:
            return _FakeFetchResult((len(self._rows),))
        return _FakeMappingsResult(self._rows)


def test_ledger_compat_audit_returns_side_by_side_payload():
    db = _FakeDB(
        rows=[
            {
                "external_reference": "acct:BILLING_CYCLE_COMPUTED:partner_billing_cycle:cycle_1",
                "ledger_entry_type": "BILLING_REVENUE",
                "ledger_amount_cents": 12000,
                "ledger_currency": "BRL",
                "ledger_status": "POSTED",
                "ledger_metadata": {"event_type": "BILLING_CYCLE_COMPUTED"},
                "ledger_created_at": datetime(2026, 4, 28, tzinfo=timezone.utc),
                "journal_entry_id": "je_1",
                "journal_reference_type": "BILLING_CYCLE_COMPUTED",
                "journal_description": "Billing cycle computed: cycle_1",
                "journal_currency": "BRL",
                "journal_created_at": datetime(2026, 4, 28, tzinfo=timezone.utc),
                "journal_debit_total": Decimal("120.00"),
                "journal_credit_total": Decimal("120.00"),
            }
        ]
    )

    out = raf.get_ledger_compat_audit(
        external_reference=None,
        event_type=None,
        from_date=None,
        to_date=None,
        limit=100,
        offset=0,
        db=db,
        _=None,
    )
    assert out["count"] == 1
    assert out["total"] == 1
    item = out["items"][0]
    assert item["audit"]["has_journal_entry"] is True
    assert item["audit"]["journal_balanced"] is True
    assert item["audit"]["amount_matches_compat"] is True
    assert item["ledger"]["amount_cents"] == 12000
    assert item["journal"]["amount_cents_derived"] == 12000


def test_ledger_compat_audit_only_mismatches_flag_is_propagated():
    db = _FakeDB(rows=[])
    out = raf.get_ledger_compat_audit(
        external_reference=None,
        event_type=None,
        only_mismatches=True,
        from_date=None,
        to_date=None,
        limit=50,
        offset=0,
        db=db,
        _=None,
    )
    assert out["only_mismatches"] is True

