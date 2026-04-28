from __future__ import annotations

from decimal import Decimal

from app.services.accounting_posting_service import (
    EVENT_LEDGER_ENTRY_TYPE,
    PostingEvent,
    _event_lines,
)
from app.services.accounting_service import validate_journal_lines


def _fake_accounts():
    return {
        "1100_AR_PARTNERS": "acc_ar",
        "4100_BILLING_REVENUE": "acc_rev",
        "4190_BILLING_REVERSALS": "acc_rev_reversal",
        "4200_CREDIT_NOTES": "acc_credit",
    }


def test_event_lines_billing_are_balanced():
    lines = _event_lines(
        PostingEvent(
            event_type="BILLING_CYCLE_COMPUTED",
            reference_source="partner_billing_cycle",
            reference_id="cycle_1",
            amount=Decimal("120.00"),
        ),
        _fake_accounts(),
    )
    out = validate_journal_lines(lines)
    assert out["is_balanced"] is True


def test_event_lines_cancellation_are_balanced():
    lines = _event_lines(
        PostingEvent(
            event_type="PARTNER_INVOICE_CANCELLED",
            reference_source="partner_b2b_invoice",
            reference_id="inv_1",
            amount=Decimal("120.00"),
        ),
        _fake_accounts(),
    )
    out = validate_journal_lines(lines)
    assert out["is_balanced"] is True


def test_event_lines_credit_note_are_balanced():
    lines = _event_lines(
        PostingEvent(
            event_type="PARTNER_CREDIT_NOTE_APPLIED",
            reference_source="partner_credit_note",
            reference_id="cn_1",
            amount=Decimal("22.00"),
        ),
        _fake_accounts(),
    )
    out = validate_journal_lines(lines)
    assert out["is_balanced"] is True


def test_event_ledger_entry_type_mapping():
    assert EVENT_LEDGER_ENTRY_TYPE["BILLING_CYCLE_COMPUTED"] == "BILLING_REVENUE"
    assert EVENT_LEDGER_ENTRY_TYPE["PARTNER_INVOICE_CANCELLED"] == "BILLING_REVERSAL"
    assert EVENT_LEDGER_ENTRY_TYPE["PARTNER_CREDIT_NOTE_APPLIED"] == "CREDIT_NOTE_APPLIED"

