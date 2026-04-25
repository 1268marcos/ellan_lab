from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def _resolve_tracking_status(*, event_type: str, outbox_status: str) -> str:
    ev = str(event_type or "").upper()
    st = str(outbox_status or "").upper()
    if ev == "ORDER_PICKED_UP":
        return "PICKED_UP"
    if ev in {"ORDER_CANCELLED", "ORDER_REFUNDED", "ORDER_EXPIRED"}:
        return "CANCELLED"
    if ev == "ORDER_DISPENSED":
        return "DISPENSED"
    if st == "DELIVERED":
        return "ALLOCATED"
    if st == "DEAD_LETTER":
        return "CANCELLED"
    return "PENDING"


def upsert_order_fulfillment_tracking(
    db: Session,
    *,
    order_id: str,
    partner_id: str | None,
    event_type: str,
    outbox_status: str,
    fulfillment_type: str = "ECOMMERCE_PARTNER",
) -> None:
    status = _resolve_tracking_status(event_type=event_type, outbox_status=outbox_status)
    db.execute(
        text(
            """
            INSERT INTO order_fulfillment_tracking (
                id, order_id, fulfillment_type, partner_id, status, last_event_type, last_outbox_status,
                allocated_at, dispensed_at, picked_up_at, returned_at, created_at, updated_at
            ) VALUES (
                gen_random_uuid()::text, :order_id, :fulfillment_type, :partner_id, :status, :event_type, :outbox_status,
                CASE WHEN :status = 'ALLOCATED' THEN NOW() ELSE NULL END,
                CASE WHEN :status = 'DISPENSED' THEN NOW() ELSE NULL END,
                CASE WHEN :status = 'PICKED_UP' THEN NOW() ELSE NULL END,
                CASE WHEN :status = 'RETURNED' THEN NOW() ELSE NULL END,
                NOW(), NOW()
            )
            ON CONFLICT (order_id) DO UPDATE SET
                fulfillment_type = EXCLUDED.fulfillment_type,
                partner_id = EXCLUDED.partner_id,
                status = EXCLUDED.status,
                last_event_type = EXCLUDED.last_event_type,
                last_outbox_status = EXCLUDED.last_outbox_status,
                allocated_at = CASE
                    WHEN EXCLUDED.status = 'ALLOCATED' AND order_fulfillment_tracking.allocated_at IS NULL THEN NOW()
                    ELSE order_fulfillment_tracking.allocated_at
                END,
                dispensed_at = CASE
                    WHEN EXCLUDED.status = 'DISPENSED' AND order_fulfillment_tracking.dispensed_at IS NULL THEN NOW()
                    ELSE order_fulfillment_tracking.dispensed_at
                END,
                picked_up_at = CASE
                    WHEN EXCLUDED.status = 'PICKED_UP' AND order_fulfillment_tracking.picked_up_at IS NULL THEN NOW()
                    ELSE order_fulfillment_tracking.picked_up_at
                END,
                returned_at = CASE
                    WHEN EXCLUDED.status = 'RETURNED' AND order_fulfillment_tracking.returned_at IS NULL THEN NOW()
                    ELSE order_fulfillment_tracking.returned_at
                END,
                updated_at = NOW()
            """
        ),
        {
            "order_id": str(order_id),
            "fulfillment_type": str(fulfillment_type or "ECOMMERCE_PARTNER"),
            "partner_id": (str(partner_id) if partner_id else None),
            "status": status,
            "event_type": str(event_type or ""),
            "outbox_status": str(outbox_status or ""),
        },
    )
