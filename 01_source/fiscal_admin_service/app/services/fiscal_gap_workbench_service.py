from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.fiscal_core import FiscalReconciliationGap
from app.schemas.fiscal import GapUpdate
from app.services import billing_fiscal_client, fiscal_core_service


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def _admin_gap_to_unified(row: FiscalReconciliationGap) -> dict[str, Any]:
    details = row.details_json
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            details = {"raw": details}
    return {
        "id": row.id,
        "source": "admin",
        "dedupe_key": row.dedupe_key,
        "gap_type": row.gap_type,
        "severity": row.severity,
        "status": row.status,
        "order_id": row.order_id,
        "invoice_id": row.invoice_id,
        "details": details if isinstance(details, dict) else None,
        "first_detected_at": _iso(row.first_detected_at),
        "last_detected_at": _iso(row.last_detected_at),
        "resolved_at": _iso(row.resolved_at),
    }


def _billing_gap_to_unified(item: dict[str, Any]) -> dict[str, Any]:
    details = item.get("details_json")
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except json.JSONDecodeError:
            details = {"raw": details}
    return {
        "id": item["id"],
        "source": "billing",
        "dedupe_key": item.get("dedupe_key"),
        "gap_type": item.get("gap_type"),
        "severity": item.get("severity"),
        "status": item.get("status"),
        "order_id": item.get("order_id"),
        "invoice_id": item.get("invoice_id"),
        "details": details if isinstance(details, dict) else None,
        "first_detected_at": item.get("first_detected_at"),
        "last_detected_at": item.get("last_detected_at"),
        "resolved_at": item.get("resolved_at"),
    }


def list_gaps_workbench(
    db: Session,
    *,
    status: str | None = "OPEN",
    date: str | None = None,
    refresh_billing: bool = False,
    include_snapshot: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    admin_rows = fiscal_core_service.list_gaps(db, status=status, limit=limit)
    admin_items = [_admin_gap_to_unified(r) for r in admin_rows]

    billing_items: list[dict[str, Any]] = []
    billing_error: str | None = None
    billing_scan: dict[str, Any] | None = None
    billing_enabled = billing_fiscal_client.is_billing_fiscal_enabled()

    if billing_enabled:
        try:
            payload = billing_fiscal_client.fetch_reconciliation_gaps(
                status=status or "OPEN",
                date=date,
                refresh=refresh_billing,
                limit=limit,
            )
            billing_items = [_billing_gap_to_unified(i) for i in payload.get("items", [])]
            if refresh_billing and isinstance(payload.get("scan"), dict):
                billing_scan = payload["scan"]
        except billing_fiscal_client.BillingFiscalClientError as exc:
            billing_error = str(exc)
    else:
        billing_error = "billing_fiscal_live_disabled"

    merged = admin_items + billing_items
    merged.sort(key=lambda x: x.get("last_detected_at") or "", reverse=True)

    snapshot: dict[str, Any] | None = None
    if include_snapshot and billing_enabled and not billing_error:
        try:
            snap_date = date.fromisoformat(date) if date else date.today()
            snapshot = billing_fiscal_client.fetch_gap_conciliation_snapshot(
                snapshot_date=snap_date,
                refresh_scan=refresh_billing,
            )
        except billing_fiscal_client.BillingFiscalClientError as exc:
            snapshot = {"error": str(exc)}

    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for item in merged:
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1
        by_type[item["gap_type"]] = by_type.get(item["gap_type"], 0) + 1

    return {
        "items": merged[:limit],
        "total": len(merged),
        "summary": {
            "admin_count": len(admin_items),
            "billing_count": len(billing_items),
            "by_severity": by_severity,
            "by_gap_type": by_type,
        },
        "billing_available": billing_enabled and billing_error is None,
        "billing_error": billing_error,
        "billing_scan": billing_scan,
        "snapshot": snapshot,
    }


def resolve_gap_workbench(db: Session, *, gap_id: str, source: str, body: GapUpdate) -> dict[str, Any]:
    if source == "billing":
        if not billing_fiscal_client.is_billing_fiscal_enabled():
            raise ValueError("billing_fiscal_live_disabled")
        if body.status and body.status != "RESOLVED":
            raise ValueError("only_RESOLVED_supported_for_billing")
        row = billing_fiscal_client.resolve_reconciliation_gap(gap_id)
        return _billing_gap_to_unified(row)
    row = fiscal_core_service.patch_gap(db, gap_id, body)
    return _admin_gap_to_unified(row)
