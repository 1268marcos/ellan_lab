from __future__ import annotations

from decimal import Decimal

from app.services.accounting_service import JournalLineIn, validate_journal_lines


def test_validate_journal_lines_balanced_passes():
    result = validate_journal_lines(
        [
            JournalLineIn(account_id="cash", debit_amount=Decimal("100.00"), credit_amount=Decimal("0")),
            JournalLineIn(account_id="revenue", debit_amount=Decimal("0"), credit_amount=Decimal("100.00")),
        ]
    )
    assert result["is_balanced"] is True
    assert result["debit_total"] == Decimal("100.00")
    assert result["credit_total"] == Decimal("100.00")


def test_validate_journal_lines_rejects_unbalanced():
    try:
        validate_journal_lines(
            [
                JournalLineIn(account_id="cash", debit_amount=Decimal("100.00"), credit_amount=Decimal("0")),
                JournalLineIn(account_id="revenue", debit_amount=Decimal("0"), credit_amount=Decimal("99.00")),
            ]
        )
        assert False, "Expected ValueError for unbalanced entry"
    except ValueError as exc:
        assert "not balanced" in str(exc)


def test_validate_journal_lines_rejects_double_side_line():
    try:
        validate_journal_lines(
            [JournalLineIn(account_id="invalid", debit_amount=Decimal("10.00"), credit_amount=Decimal("10.00"))]
        )
        assert False, "Expected ValueError for invalid line side"
    except ValueError as exc:
        assert "exactly one side" in str(exc)

