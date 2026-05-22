from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.marketplace_alerts_webhooks import (
    MarketplaceCapabilityWebhook,
    MarketplaceCapabilityWebhookDelivery,
)
from app.models.marketplace_extended import MarketplaceChannelPartner
from app.services.crypto_util import hash_secret, new_id
from app.services.webhook_dispatch import dispatch_webhook

EVENT_READINESS_SCORE_DROP = "readiness.score_drop"
EVENT_CAPABILITY_HEALTH = "capability.health"
EVENT_TEST_PING = "webhook.test"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_events(raw: str) -> list[str]:
    try:
        data = json.loads(raw or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def configure_capability_webhook(
    db: Session,
    *,
    channel_partner_id: str,
    capability_code: str,
    url: str,
    secret: str | None = None,
    events: list[str] | None = None,
    active: bool = True,
) -> MarketplaceCapabilityWebhook:
    partner = db.get(MarketplaceChannelPartner, channel_partner_id)
    if not partner:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="channel_partner_not_found")
    secret_val = secret or ""
    secret_hash = hash_secret(secret_val) if secret_val else hash_secret(f"{channel_partner_id}:{capability_code}")
    events_json = json.dumps(events or [EVENT_READINESS_SCORE_DROP, EVENT_CAPABILITY_HEALTH])
    now = _utcnow()
    row = (
        db.query(MarketplaceCapabilityWebhook)
        .filter(
            MarketplaceCapabilityWebhook.channel_partner_id == channel_partner_id,
            MarketplaceCapabilityWebhook.capability_code == capability_code,
        )
        .first()
    )
    if row:
        row.url = url
        row.secret_hash = secret_hash
        if secret_val:
            row.secret_key = secret_val[:256]
        row.event_types_json = events_json
        row.active = active
        row.partner_code = partner.code
        row.updated_at = now
    else:
        row = MarketplaceCapabilityWebhook(
            id=new_id(),
            channel_partner_id=channel_partner_id,
            partner_code=partner.code,
            capability_code=capability_code,
            url=url,
            secret_hash=secret_hash,
            secret_key=secret_val[:256] if secret_val else None,
            event_types_json=events_json,
            active=active,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_capability_webhooks(db: Session, channel_partner_id: str | None = None) -> list[MarketplaceCapabilityWebhook]:
    q = db.query(MarketplaceCapabilityWebhook)
    if channel_partner_id:
        q = q.filter(MarketplaceCapabilityWebhook.channel_partner_id == channel_partner_id)
    return q.order_by(MarketplaceCapabilityWebhook.partner_code, MarketplaceCapabilityWebhook.capability_code).all()


def deliver_event(
    db: Session,
    webhook: MarketplaceCapabilityWebhook,
    event_type: str,
    payload: dict[str, Any],
    *,
    force: bool = False,
) -> MarketplaceCapabilityWebhookDelivery:
    subscribed = _parse_events(webhook.event_types_json)
    if not force and event_type not in subscribed:
        delivery = MarketplaceCapabilityWebhookDelivery(
            id=new_id(),
            webhook_id=webhook.id,
            event_type=event_type,
            payload_json=json.dumps(payload),
            success=False,
            response_snippet="event_not_subscribed",
        )
        db.add(delivery)
        return delivery

    if not get_settings().webhook_dispatch_enabled:
        ok, http_status, snippet = True, 202, "dispatch_disabled_simulated"
    else:
        ok, http_status, snippet = dispatch_webhook(
            webhook.url,
            event_type,
            payload,
            secret=webhook.secret_key,
        )

    now = _utcnow()
    webhook.last_http_status = http_status
    webhook.last_delivered_at = now if ok else webhook.last_delivered_at
    webhook.last_error = None if ok else snippet
    webhook.updated_at = now

    delivery = MarketplaceCapabilityWebhookDelivery(
        id=new_id(),
        webhook_id=webhook.id,
        event_type=event_type,
        payload_json=json.dumps(payload),
        http_status=http_status,
        success=ok,
        response_snippet=snippet,
        created_at=now,
    )
    db.add(delivery)
    return delivery


def dispatch_partner_event(
    db: Session,
    channel_partner_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> int:
    """Dispara para todos webhooks ativos do player que assinam o evento."""
    hooks = (
        db.query(MarketplaceCapabilityWebhook)
        .filter(
            MarketplaceCapabilityWebhook.channel_partner_id == channel_partner_id,
            MarketplaceCapabilityWebhook.active.is_(True),
        )
        .all()
    )
    sent = 0
    for hook in hooks:
        if event_type in _parse_events(hook.event_types_json):
            deliver_event(db, hook, event_type, payload)
            sent += 1
    return sent


def test_capability_webhook(db: Session, webhook_id: str) -> dict:
    row = db.get(MarketplaceCapabilityWebhook, webhook_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    delivery = deliver_event(
        db,
        row,
        EVENT_TEST_PING,
        {
            "partner_code": row.partner_code,
            "capability_code": row.capability_code,
            "ping": True,
        },
        force=True,
    )
    db.commit()
    return {
        "success": delivery.success,
        "http_status": delivery.http_status,
        "response_snippet": delivery.response_snippet,
    }
