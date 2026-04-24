"""Sincroniza snapshots de invoice no billing após alteração do perfil fiscal do utilizador."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.models.order import Order, OrderStatus, PaymentStatus

logger = logging.getLogger(__name__)


def list_order_ids_for_billing_snapshot_sync(db: Session, *, user_id: str, limit: int = 50) -> list[str]:
    """
    Só pedidos com pagamento aprovado (evita ruído em rascunhos / não pagos).
    Exclui cancelados; não exige invoice local — o billing ignora order_id sem invoice.
    """
    rows = (
        db.query(Order.id)
        .filter(Order.user_id == user_id)
        .filter(Order.payment_status == PaymentStatus.APPROVED)
        .filter(Order.status != OrderStatus.CANCELLED)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    return [str(r[0]) for r in rows if r[0]]


def _summarize_billing_rebuild(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results") or []
    summary: dict[str, Any] = {
        "billing_ok": bool(payload.get("ok")),
        "orders_sent": len(results),
        "invoice_rows_updated": 0,
        "skipped_no_invoice": 0,
        "skipped_already_issued": 0,
        "skipped_processing": 0,
        "skipped_dead_letter_other": 0,
        "skipped_other": 0,
        "errors": 0,
    }
    for r in results:
        if not isinstance(r, dict):
            summary["skipped_other"] += 1
            continue
        st = r.get("status")
        if st == "updated":
            summary["invoice_rows_updated"] += 1
        elif st == "error":
            summary["errors"] += 1
        elif st == "skipped":
            reason = str(r.get("reason") or "")
            if reason == "no_invoice":
                summary["skipped_no_invoice"] += 1
            elif reason == "already_issued":
                summary["skipped_already_issued"] += 1
            elif reason == "processing":
                summary["skipped_processing"] += 1
            elif reason == "dead_letter_other":
                summary["skipped_dead_letter_other"] += 1
            elif reason.startswith("status_"):
                summary["skipped_other"] += 1
            else:
                summary["skipped_other"] += 1
        else:
            summary["skipped_other"] += 1
    return summary


def sync_billing_invoice_snapshots_after_fiscal_profile(db: Session, *, user_id: str) -> dict[str, Any]:
    from app.integrations import billing_fiscal_client

    order_ids = list_order_ids_for_billing_snapshot_sync(db, user_id=user_id)
    base: dict[str, Any] = {
        "skipped": False,
        "eligible_paid_orders": len(order_ids),
        "orders_sent_to_billing": len(order_ids),
        "invoice_rows_updated": 0,
        "skipped_no_invoice": 0,
        "skipped_already_issued": 0,
        "skipped_processing": 0,
        "skipped_dead_letter_other": 0,
        "skipped_other": 0,
        "errors": 0,
        "billing_ok": False,
        "billing_unreachable": False,
        "error": None,
    }
    if not order_ids:
        base["skipped"] = True
        base["reason"] = "no_eligible_paid_orders"
        base["eligible_paid_orders"] = 0
        base["orders_sent_to_billing"] = 0
        return base

    try:
        raw = billing_fiscal_client.rebuild_invoice_snapshots_for_orders(order_ids)
        summary = _summarize_billing_rebuild(raw if isinstance(raw, dict) else {})
        base.update(summary)
        base.pop("orders_sent", None)
        base["eligible_paid_orders"] = len(order_ids)
        base["orders_sent_to_billing"] = len(order_ids)
        return base
    except Exception as exc:
        logger.warning(
            "fiscal_invoice_snapshot_sync_failed user_id=%s orders=%s err=%s",
            user_id,
            len(order_ids),
            exc,
        )
        base["billing_unreachable"] = True
        base["error"] = str(exc)
        base["eligible_paid_orders"] = len(order_ids)
        base["orders_sent_to_billing"] = len(order_ids)
        return base
