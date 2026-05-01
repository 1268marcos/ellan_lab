"""Sprint 2 — P0 Fiscal: snapshot agregado de gaps de conciliação (parceiro / tipo / severidade) para evidência auditável."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.fiscal_reconciliation_service import scan_and_persist_reconciliation_gaps

SCOPE_FISCAL_GAP_CONCILIATION_SNAPSHOT = "SPRINT2_FISCAL_GAP_CONCILIATION_SNAPSHOT"


def _iso(dt: datetime | str | None) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    return None


def build_fiscal_gap_conciliation_snapshot(
    db: Session,
    *,
    snapshot_date: date,
    refresh_scan: bool = False,
) -> dict[str, Any]:
    """
    Agrega `fiscal_reconciliation_gaps` em aberto (OPEN) por tipo, severidade e `partner_id` em `details_json`.
    `snapshot_date` ancora o relatório (contagem de gaps cuja primeira deteção foi nesse dia civil UTC).
    """
    refreshed = False
    if refresh_scan:
        scan_and_persist_reconciliation_gaps(db)
        refreshed = True

    d_iso = snapshot_date.isoformat()

    open_row = db.execute(
        text(
            """
            SELECT COUNT(*)::INT AS c
              FROM fiscal_reconciliation_gaps
             WHERE status = 'OPEN'
            """
        ),
    ).mappings().first()
    open_total = int((open_row or {}).get("c") or 0)

    new_on_day = db.execute(
        text(
            """
            SELECT COUNT(*)::INT AS c
              FROM fiscal_reconciliation_gaps
             WHERE (first_detected_at AT TIME ZONE 'UTC')::date = CAST(:d AS DATE)
            """
        ),
        {"d": d_iso},
    ).mappings().first()
    first_detected_on_snapshot_date = int((new_on_day or {}).get("c") or 0)

    by_type_rows = db.execute(
        text(
            """
            SELECT gap_type, COUNT(*)::INT AS n
              FROM fiscal_reconciliation_gaps
             WHERE status = 'OPEN'
             GROUP BY gap_type
             ORDER BY n DESC, gap_type
            """
        ),
    ).mappings().all()

    by_severity_rows = db.execute(
        text(
            """
            SELECT severity, COUNT(*)::INT AS n
              FROM fiscal_reconciliation_gaps
             WHERE status = 'OPEN'
             GROUP BY severity
             ORDER BY n DESC, severity
            """
        ),
    ).mappings().all()

    by_partner_rows = db.execute(
        text(
            """
            SELECT COALESCE(NULLIF(TRIM(details_json->>'partner_id'), ''), 'UNKNOWN') AS partner_bucket,
                   COUNT(*)::INT AS n
              FROM fiscal_reconciliation_gaps
             WHERE status = 'OPEN'
             GROUP BY 1
             ORDER BY n DESC NULLS LAST, partner_bucket
             LIMIT 100
            """
        ),
    ).mappings().all()

    sample_rows = db.execute(
        text(
            """
            SELECT id, dedupe_key, gap_type, severity, status, order_id, invoice_id, details_json,
                   first_detected_at, last_detected_at
              FROM fiscal_reconciliation_gaps
             WHERE status = 'OPEN'
             ORDER BY last_detected_at DESC NULLS LAST
             LIMIT 40
            """
        ),
    ).mappings().all()

    samples: list[dict[str, Any]] = []
    for row in sample_rows:
        samples.append(
            {
                "id": str(row.get("id") or ""),
                "dedupe_key": str(row.get("dedupe_key") or ""),
                "gap_type": str(row.get("gap_type") or ""),
                "severity": str(row.get("severity") or ""),
                "status": str(row.get("status") or ""),
                "order_id": row.get("order_id"),
                "invoice_id": row.get("invoice_id"),
                "details_json": row.get("details_json"),
                "first_detected_at": _iso(row.get("first_detected_at")),
                "last_detected_at": _iso(row.get("last_detected_at")),
            }
        )

    return {
        "scope": SCOPE_FISCAL_GAP_CONCILIATION_SNAPSHOT,
        "snapshot_date": d_iso,
        "refreshed_scan": refreshed,
        "summary": {
            "open_gaps_total": open_total,
            "first_detected_on_snapshot_date_total": first_detected_on_snapshot_date,
            "by_gap_type": [{"gap_type": str(r.get("gap_type") or ""), "count": int(r.get("n") or 0)} for r in by_type_rows],
            "by_severity": [{"severity": str(r.get("severity") or ""), "count": int(r.get("n") or 0)} for r in by_severity_rows],
            "by_partner_id": [
                {"partner_id": str(r.get("partner_bucket") or "UNKNOWN"), "open_count": int(r.get("n") or 0)} for r in by_partner_rows
            ],
        },
        "sample_open_gaps": samples,
    }
