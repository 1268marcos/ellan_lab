from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session


def enqueue_partner_order_paid_event_if_needed(
    db: Session,
    *,
    order_id: str,
    payload: dict,
    partner_id: str = "ptn_fiscal_stub",
) -> tuple[dict, bool]:
    existing = db.execute(
        text(
            """
            SELECT id, partner_id, order_id, event_type, payload_json, status, created_at
            FROM partner_order_events_outbox
            WHERE partner_id = :partner_id
              AND order_id = :order_id
              AND event_type = 'ORDER_PAID'
              AND status IN ('PENDING','FAILED','DELIVERED')
            ORDER BY created_at DESC
            LIMIT 1
            """
        ),
        {"partner_id": partner_id, "order_id": order_id},
    ).mappings().first()
    if existing:
        return dict(existing), True

    row_id = str(uuid4())
    db.execute(
        text(
            """
            INSERT INTO partner_order_events_outbox (
                id, partner_id, order_id, event_type, payload_json, api_version,
                status, attempt_count, max_attempts, next_retry_at, created_at, updated_at
            ) VALUES (
                :id, :partner_id, :order_id, 'ORDER_PAID', CAST(:payload_json AS JSONB), 'v1',
                'PENDING', 0, 5, NOW(), NOW(), NOW()
            )
            """
        ),
        {
            "id": row_id,
            "partner_id": partner_id,
            "order_id": order_id,
            "payload_json": __import__("json").dumps(payload or {}),
        },
    )
    created = db.execute(
        text(
            """
            SELECT id, partner_id, order_id, event_type, payload_json, status, created_at
            FROM partner_order_events_outbox
            WHERE id = :id
            """
        ),
        {"id": row_id},
    ).mappings().first()
    return dict(created or {}), False


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
