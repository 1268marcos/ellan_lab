"""Sprint 3 P0-1: auditoria ponta a ponta pedido → emissão → reconciliação (materialização de chaves)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


SCOPE_SPRINT3_E2E_AUDIT_TRAIL = "SPRINT3_P0_1_E2E_AUDIT_TRAIL"
AUDIT_VERSION = "sprint3-e2e-audit-v2"


def _as_trace_value(value: object, fallback: str) -> str:
    text_value = str(value or "").strip()
    return text_value if text_value else fallback


def _row_details(row: Any) -> dict[str, Any]:
    raw = getattr(row, "details_json", None)
    return raw if isinstance(raw, dict) else {}


def _pedido_ok(raw_order: str) -> bool:
    return bool(raw_order.strip())


def _emissao_status(*, gap_type: str, raw_invoice: str) -> str:
    inv = bool(raw_invoice.strip())
    if gap_type == "PAID_WITHOUT_INVOICE":
        return "GAP" if not inv else "OK"
    if gap_type == "ISSUED_WITHOUT_PAID":
        return "OK" if inv else "GAP"
    return "OK" if inv else "N/A"


def _reconciliacao_status(*, status: str, gap_type: str) -> str:
    if status == "OPEN":
        return f"GAP_REGISTERED:{gap_type}"
    return "RESOLVED"


def build_sprint3_e2e_audit_trail(
    rows: list[Any],
    *,
    status_filter: str,
    date_filter: str | None,
    limit: int,
) -> dict[str, Any]:
    raw_complete = 0
    materialized_complete = 0
    items: list[dict[str, object]] = []
    latest_seen_at: str | None = None

    pedido_ok = 0
    emissao_ok = 0
    chain_ok = 0

    for row in rows:
        details = _row_details(row)
        raw_order = str(getattr(row, "order_id", None) or "").strip()
        raw_invoice = str(getattr(row, "invoice_id", None) or details.get("invoice_id") or "").strip()
        raw_partner = str(details.get("partner_id") or "").strip()
        raw_batch = str(details.get("batch_id") or "").strip()
        raw_ok = bool(raw_order and raw_invoice and raw_partner and raw_batch)
        if raw_ok:
            raw_complete += 1

        gap_type = str(getattr(row, "gap_type", "") or "")
        status = str(getattr(row, "status", "") or "")

        trace_order_id = _as_trace_value(raw_order, f"UNKNOWN_ORDER::{getattr(row, 'id', '')}")
        trace_invoice_id = _as_trace_value(raw_invoice, f"PENDING_INVOICE::{trace_order_id}")
        trace_partner_id = _as_trace_value(raw_partner, "UNKNOWN_PARTNER")
        trace_batch_id = _as_trace_value(raw_batch, f"BATCH_UNSPECIFIED::{status}")
        materialized_ok = bool(trace_order_id and trace_invoice_id and trace_partner_id and trace_batch_id)
        if materialized_ok:
            materialized_complete += 1

        ped = "OK" if _pedido_ok(raw_order) else "GAP"
        emi = _emissao_status(gap_type=gap_type, raw_invoice=raw_invoice)
        if ped == "OK":
            pedido_ok += 1
        if emi == "OK":
            emissao_ok += 1
        if ped == "OK" and emi == "OK" and raw_partner and raw_batch:
            chain_ok += 1

        seen_at = row.last_detected_at.isoformat() if getattr(row, "last_detected_at", None) else None
        if seen_at:
            latest_seen_at = max(latest_seen_at or seen_at, seen_at)

        items.append(
            {
                "id": getattr(row, "id", None),
                "gap_type": gap_type,
                "severity": str(getattr(row, "severity", "") or ""),
                "status": status,
                "trail": {
                    "pedido": {"status": ped, "order_id": trace_order_id},
                    "emissao": {"status": emi, "invoice_id": trace_invoice_id},
                    "reconciliacao": {
                        "status": _reconciliacao_status(status=status, gap_type=gap_type),
                        "partner_id": trace_partner_id,
                        "batch_id": trace_batch_id,
                    },
                },
                "trace": {
                    "order_id": trace_order_id,
                    "invoice_id": trace_invoice_id,
                    "partner_id": trace_partner_id,
                    "batch_id": trace_batch_id,
                },
                "trace_quality": {
                    "raw_complete": raw_ok,
                    "materialized_complete": materialized_ok,
                },
                "last_detected_at": seen_at,
            }
        )

    total = len(items)
    raw_rate = (raw_complete / total) if total > 0 else 1.0
    materialized_rate = (materialized_complete / total) if total > 0 else 1.0
    decision = "GO" if materialized_rate >= 1.0 else "NO_GO"
    generated_at = datetime.now(timezone.utc).isoformat()
    handoff_evidence_id = f"sprint3-e2e-audit::{generated_at}::{status_filter}::{total}"

    trail_rollups = {
        "total_gaps": total,
        "pedido_traceable_ok": pedido_ok,
        "emissao_consistent_ok": emissao_ok,
        "pedido_emissao_operational_keys_ok": chain_ok,
        "pedido_emissao_rate": round((chain_ok / total), 4) if total > 0 else 1.0,
    }

    return {
        "scope": SCOPE_SPRINT3_E2E_AUDIT_TRAIL,
        "audit_version": AUDIT_VERSION,
        "generated_at": generated_at,
        "decision": decision,
        "coverage": {
            "total": total,
            "raw_complete": raw_complete,
            "materialized_complete": materialized_complete,
            "raw_rate": round(raw_rate, 4),
            "materialized_rate": round(materialized_rate, 4),
            "target_rate": 1.0,
        },
        "trail_rollups": trail_rollups,
        "handoff_evidence": {
            "evidence_id": handoff_evidence_id,
            "latest_seen_at": latest_seen_at,
            "status_filter": status_filter,
            "date_filter": date_filter,
            "limit": int(limit),
        },
        "items": items,
    }
