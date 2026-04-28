from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class JournalLineIn:
    account_id: str
    debit_amount: Decimal = Decimal("0")
    credit_amount: Decimal = Decimal("0")


def _to_decimal(value: Decimal | int | float | str | None) -> Decimal:
    return Decimal(str(value or 0))


def validate_journal_lines(lines: list[JournalLineIn]) -> dict:
    if not lines:
        raise ValueError("journal entry requires at least one line")

    debit_total = Decimal("0")
    credit_total = Decimal("0")
    for idx, line in enumerate(lines, start=1):
        debit = _to_decimal(line.debit_amount)
        credit = _to_decimal(line.credit_amount)
        if debit < 0 or credit < 0:
            raise ValueError(f"line {idx}: debit/credit must be non-negative")
        has_debit = debit > 0
        has_credit = credit > 0
        if has_debit == has_credit:
            raise ValueError(f"line {idx}: line must have exactly one side (DEBIT or CREDIT)")
        debit_total += debit
        credit_total += credit

    if debit_total != credit_total:
        raise ValueError(
            f"journal entry is not balanced: debit_total={debit_total} credit_total={credit_total}"
        )
    return {"debit_total": debit_total, "credit_total": credit_total, "is_balanced": True}

