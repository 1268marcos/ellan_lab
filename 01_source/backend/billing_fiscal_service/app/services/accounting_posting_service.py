from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.accounting_service import JournalLineIn, validate_journal_lines


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class PostingEvent:
    event_type: str
    reference_source: str
    reference_id: str
    amount: Decimal
    currency: str = "BRL"
    description: str = ""
    entry_date: date | None = None


SYSTEM_ACCOUNT_DEFS = {
    "1100_AR_PARTNERS": ("Contas a Receber - Partners", "ASSET", "DEBIT"),
    "4100_BILLING_REVENUE": ("Receita de Billing B2B", "REVENUE", "CREDIT"),
    "4190_BILLING_REVERSALS": ("Estornos e Cancelamentos B2B", "REVENUE", "DEBIT"),
    "4200_CREDIT_NOTES": ("Créditos Concedidos a Partners", "EXPENSE", "DEBIT"),
}

EVENT_LEDGER_ENTRY_TYPE = {
    "BILLING_CYCLE_COMPUTED": "BILLING_REVENUE",
    "PARTNER_INVOICE_CANCELLED": "BILLING_REVERSAL",
    "PARTNER_CREDIT_NOTE_APPLIED": "CREDIT_NOTE_APPLIED",
}


def _dedupe_key(event: PostingEvent) -> str:
    return f"acct:{event.event_type}:{event.reference_source}:{event.reference_id}"


def _event_lines(event: PostingEvent, account_ids: dict[str, str]) -> list[JournalLineIn]:
    amount = Decimal(event.amount or 0)
    if amount <= 0:
        raise ValueError("amount must be greater than zero")

    if event.event_type == "BILLING_CYCLE_COMPUTED":
        return [
            JournalLineIn(account_id=account_ids["1100_AR_PARTNERS"], debit_amount=amount, credit_amount=Decimal("0")),
            JournalLineIn(account_id=account_ids["4100_BILLING_REVENUE"], debit_amount=Decimal("0"), credit_amount=amount),
        ]
    if event.event_type == "PARTNER_INVOICE_CANCELLED":
        return [
            JournalLineIn(account_id=account_ids["4190_BILLING_REVERSALS"], debit_amount=amount, credit_amount=Decimal("0")),
            JournalLineIn(account_id=account_ids["1100_AR_PARTNERS"], debit_amount=Decimal("0"), credit_amount=amount),
        ]
    if event.event_type == "PARTNER_CREDIT_NOTE_APPLIED":
        return [
            JournalLineIn(account_id=account_ids["4200_CREDIT_NOTES"], debit_amount=amount, credit_amount=Decimal("0")),
            JournalLineIn(account_id=account_ids["1100_AR_PARTNERS"], debit_amount=Decimal("0"), credit_amount=amount),
        ]
    raise ValueError(f"unsupported event_type: {event.event_type}")


def _ensure_system_accounts(db: Session) -> dict[str, str]:
    now = _utc_now()
    account_ids: dict[str, str] = {}
    for code, (name, acc_type, normal_balance) in SYSTEM_ACCOUNT_DEFS.items():
        row = db.execute(
            text("SELECT id FROM chart_of_accounts WHERE account_code = :account_code"),
            {"account_code": code},
        ).fetchone()
        if row:
            account_ids[code] = str(row[0])
            continue
        account_id = str(uuid4())
        db.execute(
            text(
                """
                INSERT INTO chart_of_accounts (
                    id, account_code, account_name, account_type, normal_balance,
                    currency, is_active, metadata_json, created_at, updated_at
                )
                VALUES (
                    :id, :account_code, :account_name, :account_type, :normal_balance,
                    'BRL', TRUE, '{}'::jsonb, :created_at, :updated_at
                )
                """
            ),
            {
                "id": account_id,
                "account_code": code,
                "account_name": name,
                "account_type": acc_type,
                "normal_balance": normal_balance,
                "created_at": now,
                "updated_at": now,
            },
        )
        account_ids[code] = account_id
    return account_ids


def post_event(db: Session, event: PostingEvent) -> dict:
    dedupe_key = _dedupe_key(event)
    existing = db.execute(
        text("SELECT id FROM journal_entries WHERE dedupe_key = :dedupe_key LIMIT 1"),
        {"dedupe_key": dedupe_key},
    ).fetchone()
    if existing:
        return {"journal_entry_id": str(existing[0]), "dedupe_key": dedupe_key, "already_posted": True}

    account_ids = _ensure_system_accounts(db)
    lines = _event_lines(event, account_ids)
    validation = validate_journal_lines(lines)

    journal_entry_id = str(uuid4())
    now = _utc_now()
    db.execute(
        text(
            """
            INSERT INTO journal_entries (
                id, entry_date, description, reference_type, reference_id, reference_source,
                dedupe_key, currency, is_posted, posted_at, created_at
            )
            VALUES (
                :id, :entry_date, :description, :reference_type, :reference_id, :reference_source,
                :dedupe_key, :currency, TRUE, :posted_at, :created_at
            )
            """
        ),
        {
            "id": journal_entry_id,
            "entry_date": event.entry_date or now.date(),
            "description": event.description or event.event_type,
            "reference_type": event.event_type,
            "reference_id": event.reference_id,
            "reference_source": event.reference_source,
            "dedupe_key": dedupe_key,
            "currency": event.currency or "BRL",
            "posted_at": now,
            "created_at": now,
        },
    )

    for idx, line in enumerate(lines, start=1):
        db.execute(
            text(
                """
                INSERT INTO journal_entry_lines (
                    journal_entry_id, line_number, account_id, description,
                    debit_amount, credit_amount, currency, reference_source, reference_id, created_at
                )
                VALUES (
                    :journal_entry_id, :line_number, :account_id, :description,
                    :debit_amount, :credit_amount, :currency, :reference_source, :reference_id, :created_at
                )
                """
            ),
            {
                "journal_entry_id": journal_entry_id,
                "line_number": idx,
                "account_id": line.account_id,
                "description": event.description or event.event_type,
                "debit_amount": Decimal(line.debit_amount or 0),
                "credit_amount": Decimal(line.credit_amount or 0),
                "currency": event.currency or "BRL",
                "reference_source": event.reference_source,
                "reference_id": event.reference_id,
                "created_at": now,
            },
        )

    # Camada de compatibilidade: espelha movimento líquido no financial_ledger.
    # Fonte primária permanece em journal_entries/journal_entry_lines (double-entry).
    ledger_entry_type = EVENT_LEDGER_ENTRY_TYPE.get(event.event_type, "ACCOUNTING_EVENT")
    amount_cents = int((Decimal(event.amount) * Decimal("100")).quantize(Decimal("1")))
    if amount_cents == 0:
        raise ValueError("compat ledger amount cannot be zero")
    db.execute(
        text(
            """
            INSERT INTO financial_ledger (
                id, entry_type, amount_cents, currency, status, external_reference, metadata, created_at
            )
            VALUES (
                :id, :entry_type, :amount_cents, :currency, 'POSTED', :external_reference, :metadata::jsonb, :created_at
            )
            """
        ),
        {
            "id": str(uuid4()),
            "entry_type": ledger_entry_type,
            "amount_cents": amount_cents,
            "currency": event.currency or "BRL",
            "external_reference": dedupe_key,
            "metadata": json.dumps(
                {
                    "compat_mode": "derived_from_double_entry",
                    "journal_entry_id": journal_entry_id,
                    "event_type": event.event_type,
                    "reference_source": event.reference_source,
                    "reference_id": event.reference_id,
                }
            ),
            "created_at": now,
        },
    )
    db.commit()
    return {
        "journal_entry_id": journal_entry_id,
        "dedupe_key": dedupe_key,
        "already_posted": False,
        "debit_total": validation["debit_total"],
        "credit_total": validation["credit_total"],
    }

