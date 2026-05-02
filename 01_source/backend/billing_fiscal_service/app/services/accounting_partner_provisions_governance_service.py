"""P0 Contábil Partners — governança de provisões e ajustes (`MANUAL_ADJUSTMENT` em `ellanlab_revenue_recognition`)."""

from __future__ import annotations

from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

SCOPE_PARTNER_PROVISIONS_GOVERNANCE = "SPRINT2_PARTNER_PROVISIONS_GOVERNANCE"


def build_partner_provisions_governance_report(
    db: Session,
    *,
    as_of_date: date,
    currency: str | None = None,
    partner_limit: int = 200,
) -> dict:
    """
    Agrega linhas `MANUAL_ADJUSTMENT` até `as_of_date` (inclusive) por `partner_id`,
    com totais globais, quebra por `recognition_rule` e contagem sem `governance_owner` em metadata.
    """
    cur = (currency or "").strip() or None
    lim = max(1, min(int(partner_limit or 200), 500))

    totals = db.execute(
        text(
            """
            SELECT COUNT(*)::INT AS total_lines,
                   COUNT(DISTINCT partner_id)::INT AS distinct_partners,
                   COALESCE(SUM(recognized_amount_cents), 0)::BIGINT AS recognized_cents,
                   COALESCE(SUM(deferred_amount_cents), 0)::BIGINT AS deferred_cents
              FROM ellanlab_revenue_recognition
             WHERE source_type = 'MANUAL_ADJUSTMENT'
               AND recognition_date <= CAST(:d AS DATE)
               AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
            """
        ),
        {"d": as_of_date.isoformat(), "currency": cur},
    ).mappings().first()

    missing_owner = db.execute(
        text(
            """
            SELECT COUNT(*)::INT AS n
              FROM ellanlab_revenue_recognition
             WHERE source_type = 'MANUAL_ADJUSTMENT'
               AND recognition_date <= CAST(:d AS DATE)
               AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
               AND (
                    metadata_json->>'governance_owner' IS NULL
                 OR TRIM(metadata_json->>'governance_owner') = ''
               )
            """
        ),
        {"d": as_of_date.isoformat(), "currency": cur},
    ).mappings().first()

    by_rule = db.execute(
        text(
            """
            SELECT recognition_rule,
                   COUNT(*)::INT AS line_count,
                   COALESCE(SUM(recognized_amount_cents), 0)::BIGINT AS recognized_cents,
                   COALESCE(SUM(deferred_amount_cents), 0)::BIGINT AS deferred_cents
              FROM ellanlab_revenue_recognition
             WHERE source_type = 'MANUAL_ADJUSTMENT'
               AND recognition_date <= CAST(:d AS DATE)
               AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
             GROUP BY recognition_rule
             ORDER BY recognition_rule
            """
        ),
        {"d": as_of_date.isoformat(), "currency": cur},
    ).mappings().all()

    per_partner = db.execute(
        text(
            """
            SELECT partner_id::text AS partner_id,
                   COUNT(*)::INT AS manual_lines,
                   COALESCE(SUM(recognized_amount_cents), 0)::BIGINT AS recognized_cents,
                   COALESCE(SUM(deferred_amount_cents), 0)::BIGINT AS deferred_cents,
                   MAX(recognition_date)::text AS last_adjustment_date
              FROM ellanlab_revenue_recognition
             WHERE source_type = 'MANUAL_ADJUSTMENT'
               AND recognition_date <= CAST(:d AS DATE)
               AND (:currency IS NULL OR UPPER(TRIM(currency)) = UPPER(TRIM(:currency)))
             GROUP BY partner_id
             ORDER BY manual_lines DESC, partner_id
             LIMIT :lim
            """
        ),
        {"d": as_of_date.isoformat(), "currency": cur, "lim": lim},
    ).mappings().all()

    total_lines = int((totals or {}).get("total_lines") or 0)
    missing_n = int((missing_owner or {}).get("n") or 0)

    return {
        "scope": SCOPE_PARTNER_PROVISIONS_GOVERNANCE,
        "as_of_date": as_of_date.isoformat(),
        "currency_filter": cur,
        "summary": {
            "total_manual_lines": total_lines,
            "distinct_partners": int((totals or {}).get("distinct_partners") or 0),
            "recognized_cents_total": int((totals or {}).get("recognized_cents") or 0),
            "deferred_cents_total": int((totals or {}).get("deferred_cents") or 0),
            "manual_lines_missing_governance_owner": missing_n,
            "governance_owner_coverage_pct": round(100.0 * (total_lines - missing_n) / total_lines, 2) if total_lines else 100.0,
        },
        "by_recognition_rule": [
            {
                "recognition_rule": str(r.get("recognition_rule") or ""),
                "line_count": int(r.get("line_count") or 0),
                "recognized_cents": int(r.get("recognized_cents") or 0),
                "deferred_cents": int(r.get("deferred_cents") or 0),
            }
            for r in by_rule
        ],
        "per_partner": [
            {
                "partner_id": str(r.get("partner_id") or ""),
                "manual_lines": int(r.get("manual_lines") or 0),
                "recognized_cents": int(r.get("recognized_cents") or 0),
                "deferred_cents": int(r.get("deferred_cents") or 0),
                "last_adjustment_date": r.get("last_adjustment_date"),
            }
            for r in per_partner
        ],
    }
