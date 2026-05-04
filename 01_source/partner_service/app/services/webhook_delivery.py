from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.webhook import PartnerWebhookDelivery, PartnerWebhookSubscription
from app.schemas.webhook import WebhookConfigureIn

logger = logging.getLogger(__name__)


def configure_webhook(db: Session, partner_id: str, body: WebhookConfigureIn) -> PartnerWebhookSubscription:
    sub = PartnerWebhookSubscription(
        id=str(uuid.uuid4()),
        partner_id=partner_id,
        url=str(body.url),
        events=json.dumps(body.events),
        secret=body.secret,
        is_active=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def list_deliveries(db: Session, partner_id: str) -> list[PartnerWebhookDelivery]:
    return (
        db.query(PartnerWebhookDelivery)
        .join(PartnerWebhookSubscription)
        .filter(PartnerWebhookSubscription.partner_id == partner_id)
        .order_by(PartnerWebhookDelivery.created_at.desc())
        .all()
    )


def enqueue_test_event(
    redis_client: Any,
    *,
    stream_key: str,
    subscription_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> str:
    fields = {
        "subscription_id": subscription_id,
        "event_type": event_type,
        "payload": json.dumps(payload),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    return str(redis_client.xadd(stream_key, fields))


def create_pending_delivery(db: Session, subscription_id: str, event_type: str, payload: dict[str, Any]) -> PartnerWebhookDelivery:
    d = PartnerWebhookDelivery(
        id=str(uuid.uuid4()),
        subscription_id=subscription_id,
        event_type=event_type,
        payload_json=json.dumps(payload),
        status="PENDING",
        attempts=0,
    )
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


async def deliver_http(subscription: PartnerWebhookSubscription, payload: dict[str, Any]) -> tuple[int, str | None]:
    headers = {"Content-Type": "application/json"}
    if subscription.secret:
        headers["X-Webhook-Secret"] = subscription.secret
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(subscription.url, json=payload, headers=headers)
            return r.status_code, None if r.is_success else r.text[:500]
    except Exception as exc:
        return 0, str(exc)[:500]


def deliver_http_sync(subscription: PartnerWebhookSubscription, payload: dict[str, Any]) -> tuple[int, str | None]:
    headers = {"Content-Type": "application/json"}
    if subscription.secret:
        headers["X-Webhook-Secret"] = subscription.secret
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.post(subscription.url, json=payload, headers=headers)
            return r.status_code, None if r.is_success else r.text[:500]
    except Exception as exc:
        return 0, str(exc)[:500]


def publish_to_stream(db: Session, redis_client: Any, subscription: PartnerWebhookSubscription, event_type: str, payload: dict[str, Any]) -> PartnerWebhookDelivery:
    settings = get_settings()
    delivery = create_pending_delivery(db, subscription.id, event_type, payload)
    enqueue_test_event(
        redis_client,
        stream_key=settings.webhook_stream_key,
        subscription_id=subscription.id,
        event_type=event_type,
        payload={"delivery_id": delivery.id, **payload},
    )
    return delivery
