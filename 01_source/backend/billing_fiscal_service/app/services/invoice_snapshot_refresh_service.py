"""Atualiza `order_snapshot` e colunas F-1 a partir do order_pickup (perfil fiscal alterado)."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.integrations.order_pickup_client import OrderPickupClientError, get_order_snapshot_for_invoice
from app.models.invoice_model import Invoice, InvoiceStatus
from app.services.invoice_issue_service import reset_invoice_for_retry
from app.services.invoice_orchestrator import _resolve_country_from_snapshot, _resolve_invoice_type
from app.services.invoice_snapshot_fiscal import fiscal_columns_from_order_snapshot

logger = logging.getLogger(__name__)


def _apply_snapshot_to_invoice_row(db: Session, invoice: Invoice, snapshot: dict[str, Any]) -> None:
    country = _resolve_country_from_snapshot(snapshot)
    fiscal_cols = fiscal_columns_from_order_snapshot(snapshot, country=country)
    order = snapshot.get("order") or {}

    invoice.order_snapshot = snapshot
    invoice.country = country
    invoice.invoice_type = _resolve_invoice_type(country)
    invoice.region = order.get("region") or invoice.region
    invoice.payment_method = order.get("payment_method") or invoice.payment_method
    invoice.currency = order.get("currency") or invoice.currency
    if order.get("amount_cents") is not None:
        invoice.amount_cents = order.get("amount_cents")
    tid = order.get("tenant_id") or (snapshot.get("tenant_fiscal") or {}).get("tenant_id")
    if tid:
        invoice.tenant_id = tid

    for key, val in fiscal_cols.items():
        setattr(invoice, key, val)

    db.add(invoice)
    db.commit()
    db.refresh(invoice)


def refresh_invoice_order_snapshot(db: Session, invoice: Invoice) -> dict[str, Any]:
    """
    Reidrata snapshot fiscal da invoice a partir do order_pickup.
    - Ignora ISSUED e PROCESSING.
    - DEAD_LETTER só se last_error_code=CONSUMER_FISCAL_INCOMPLETE (reabre para PENDING antes).
    """
    oid = str(invoice.order_id or "").strip()
    if not oid:
        return {"order_id": None, "status": "skipped", "reason": "missing_order_id"}

    if invoice.status == InvoiceStatus.ISSUED:
        return {"order_id": oid, "status": "skipped", "reason": "already_issued"}
    if invoice.status == InvoiceStatus.PROCESSING:
        return {"order_id": oid, "status": "skipped", "reason": "processing"}

    if invoice.status == InvoiceStatus.DEAD_LETTER:
        if str(invoice.last_error_code or "") != "CONSUMER_FISCAL_INCOMPLETE":
            return {"order_id": oid, "status": "skipped", "reason": "dead_letter_other"}
        reset_invoice_for_retry(db, invoice, clear_identifiers=False)
        db.refresh(invoice)

    if invoice.status not in {
        InvoiceStatus.PENDING,
        InvoiceStatus.FAILED,
    }:
        return {"order_id": oid, "status": "skipped", "reason": f"status_{getattr(invoice.status, 'value', invoice.status)}"}

    try:
        snapshot = get_order_snapshot_for_invoice(oid)
    except OrderPickupClientError as exc:
        logger.warning("invoice_snapshot_refresh_pickup_failed order_id=%s err=%s", oid, exc)
        return {"order_id": oid, "status": "error", "reason": str(exc)}

    _apply_snapshot_to_invoice_row(db, invoice, snapshot)
    return {"order_id": oid, "status": "updated", "invoice_id": invoice.id}


def rebuild_snapshots_for_order_ids(db: Session, order_ids: list[str]) -> dict[str, Any]:
    """Processa lista idempotente de order_id (máx. 50)."""
    seen: set[str] = set()
    normalized: list[str] = []
    for raw in order_ids:
        o = str(raw or "").strip()
        if not o or o in seen:
            continue
        seen.add(o)
        normalized.append(o)
        if len(normalized) >= 50:
            break

    results: list[dict[str, Any]] = []
    for oid in normalized:
        inv = db.query(Invoice).filter(Invoice.order_id == oid).first()
        if inv is None:
            results.append({"order_id": oid, "status": "skipped", "reason": "no_invoice"})
            continue
        results.append(refresh_invoice_order_snapshot(db, inv))

    return {"ok": True, "count": len(results), "results": results}
