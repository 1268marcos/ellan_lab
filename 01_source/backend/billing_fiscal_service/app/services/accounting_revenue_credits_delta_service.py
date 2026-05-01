"""Sprint 2 — D15: snapshot contábil receita vs estornos/créditos (compat `financial_ledger`)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session


def _safe_residual_pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 4)


def build_revenue_credits_delta_report(
    db: Session,
    *,
    snapshot_date: date,
    currency: str | None = None,
    ledger_sample_limit: int = 40,
) -> dict:
    """
    Consolida `ellanlab_revenue_recognition` (receita reconhecida no dia) com agregados
    do `financial_ledger` (BILLING_REVENUE, BILLING_REVERSAL, CREDIT_NOTE_APPLIED) no mesmo dia civil.
    """
    cur = (currency or "").strip() or None
    rev_row = db.execute(
        text(
            """
            SELECT
                COUNT(*)::INT AS line_count,
                COALESCE(SUM(recognized_amount_cents), 0)::BIGINT AS recognized_total,
                COALESCE(SUM(deferred_amount_cents), 0)::BIGINT AS deferred_total
            FROM ellanlab_revenue_recognition
            WHERE recognition_date = CAST(:d AS DATE)
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().first()
    line_count = int((rev_row or {}).get("line_count") or 0)
    recognized_total = int((rev_row or {}).get("recognized_total") or 0)
    deferred_total = int((rev_row or {}).get("deferred_total") or 0)

    ledger_agg_rows = db.execute(
        text(
            """
            SELECT
                entry_type,
                COUNT(*)::INT AS n,
                COALESCE(SUM(ABS(amount_cents)), 0)::BIGINT AS amount_sum
            FROM financial_ledger
            WHERE created_at::date = CAST(:d AS DATE)
              AND entry_type IN ('BILLING_REVENUE', 'BILLING_REVERSAL', 'CREDIT_NOTE_APPLIED')
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            GROUP BY entry_type
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur},
    ).mappings().all()

    by_type: dict[str, dict[str, int]] = {}
    for row in ledger_agg_rows:
        et = str(row.get("entry_type") or "")
        by_type[et] = {"count": int(row.get("n") or 0), "amount_cents": int(row.get("amount_sum") or 0)}

    rev_ledger = by_type.get("BILLING_REVENUE", {"count": 0, "amount_cents": 0})
    rev_cents = int(rev_ledger.get("amount_cents") or 0)
    reversal_cents = int(by_type.get("BILLING_REVERSAL", {}).get("amount_cents") or 0)
    credit_note_cents = int(by_type.get("CREDIT_NOTE_APPLIED", {}).get("amount_cents") or 0)
    numerator = reversal_cents + credit_note_cents
    denom = recognized_total if recognized_total > 0 else rev_cents

    sample_rows = db.execute(
        text(
            """
            SELECT id, entry_type, amount_cents, currency, external_reference, metadata, created_at
            FROM financial_ledger
            WHERE created_at::date = CAST(:d AS DATE)
              AND entry_type IN ('BILLING_REVENUE', 'BILLING_REVERSAL', 'CREDIT_NOTE_APPLIED')
              AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            ORDER BY created_at DESC
            LIMIT :lim
            """
        ),
        {"d": snapshot_date.isoformat(), "currency": cur, "lim": int(ledger_sample_limit)},
    ).mappings().all()
    sample: list[dict] = []
    for r in sample_rows:
        sample.append(
            {
                "id": r.get("id"),
                "entry_type": r.get("entry_type"),
                "amount_cents": int(r.get("amount_cents") or 0),
                "currency": r.get("currency"),
                "external_reference": r.get("external_reference"),
                "metadata": r.get("metadata") if isinstance(r.get("metadata"), dict) else (r.get("metadata") or {}),
                "created_at": r.get("created_at").isoformat() if r.get("created_at") else None,
            }
        )

    return {
        "scope": "SPRINT2_D15_REVENUE_CREDITS_DELTA",
        "snapshot_date": snapshot_date.isoformat(),
        "currency_filter": cur,
        "summary": {
            "revenue_recognition_lines": line_count,
            "recognized_revenue_cents_total": recognized_total,
            "deferred_revenue_cents_total": deferred_total,
            "ledger_billing_revenue_lines": int(rev_ledger.get("count") or 0),
            "ledger_billing_revenue_cents": rev_cents,
            "ledger_reversal_lines": int(by_type.get("BILLING_REVERSAL", {}).get("count") or 0),
            "ledger_reversal_cents": reversal_cents,
            "ledger_credit_note_lines": int(by_type.get("CREDIT_NOTE_APPLIED", {}).get("count") or 0),
            "ledger_credit_note_cents": credit_note_cents,
            "divergence_residual_pct": _safe_residual_pct(numerator, denom),
        },
        "ledger_entries_sample": sample,
    }
