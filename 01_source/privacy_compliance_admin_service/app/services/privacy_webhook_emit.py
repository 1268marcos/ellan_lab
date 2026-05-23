from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session


def emit_privacy_webhook(
    db: Session,
    *,
    regulation_code: str,
    event_name: str,
    payload: dict,
    aggregate_id: str | None = None,
    dispatch: bool = True,
) -> dict | None:
    """Enfileira (e opcionalmente despacha) evento privacy se webhook configurado."""
    try:
        from app.services.webhook_dispatcher_service import dispatch_delivery, enqueue_webhook_event

        delivery = enqueue_webhook_event(
            db,
            regulation_code=regulation_code,
            event_name=event_name,
            payload=payload,
            aggregate_id=aggregate_id,
        )
        if dispatch:
            dispatch_delivery(db, delivery.id)
        return delivery if isinstance(delivery, dict) else None
    except HTTPException:
        return None
    except Exception:
        return None
