from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.professional_ops import HardwareCapabilityWebhook, HardwareCapabilityWebhookDelivery
from app.services import webhook_dlq
from app.services.crypto_util import hash_secret, new_id
from app.services.webhook_dispatch import dispatch_webhook

EVENT_READINESS_SCORE_DROP = "readiness.score_drop"
EVENT_CAPABILITY_HEALTH = "capability.health"
EVENT_TEST_PING = "webhook.test"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_events(raw: list | str | None) -> list[str]:
    if isinstance(raw, list):
        return raw
    try:
        data = json.loads(raw or "[]")
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def list_deliveries(
    db: Session,
    *,
    status: str | None = None,
    webhook_id: str | None = None,
    limit: int = 100,
) -> list[HardwareCapabilityWebhookDelivery]:
    q = db.query(HardwareCapabilityWebhookDelivery)
    if status:
        q = q.filter(HardwareCapabilityWebhookDelivery.status == status.upper())
    if webhook_id:
        q = q.filter(HardwareCapabilityWebhookDelivery.webhook_id == webhook_id)
    return q.order_by(HardwareCapabilityWebhookDelivery.created_at.desc()).limit(limit).all()


def deliver_event(
    db: Session,
    webhook: HardwareCapabilityWebhook,
    event_type: str,
    payload: dict[str, Any],
    *,
    force: bool = False,
) -> HardwareCapabilityWebhookDelivery:
    subscribed = _parse_events(webhook.event_types_json)
    if not force and event_type not in subscribed:
        delivery = HardwareCapabilityWebhookDelivery(
            id=new_id(),
            webhook_id=webhook.id,
            event_type=event_type,
            payload_json={"skipped": True, **payload},
            success=False,
            response_snippet="event_not_subscribed",
            status=webhook_dlq.STATUS_SKIPPED,
            attempt_count=1,
        )
        db.add(delivery)
        db.commit()
        return delivery

    if not get_settings().webhook_dispatch_enabled and not force:
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

    st = webhook_dlq.apply_delivery_status(db, webhook_id=webhook.id, success=ok, response_snippet=snippet)
    delivery = HardwareCapabilityWebhookDelivery(
        id=new_id(),
        webhook_id=webhook.id,
        event_type=event_type,
        payload_json=payload,
        http_status=http_status,
        success=ok,
        response_snippet=snippet,
        status=st,
        attempt_count=1,
        dead_lettered_at=webhook_dlq.dead_lettered_at_for_status(st),
        created_at=now,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


def test_webhook(db: Session, webhook_id: str) -> HardwareCapabilityWebhookDelivery:
    webhook = db.get(HardwareCapabilityWebhook, webhook_id)
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    return deliver_event(db, webhook, EVENT_TEST_PING, {"ping": True}, force=True)


def replay_delivery(db: Session, delivery_id: str) -> HardwareCapabilityWebhookDelivery:
    original = db.get(HardwareCapabilityWebhookDelivery, delivery_id)
    if not original:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="delivery_not_found")
    if original.status not in (webhook_dlq.STATUS_DEAD_LETTER, webhook_dlq.STATUS_FAILED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="delivery_not_replayable")
    webhook = db.get(HardwareCapabilityWebhook, original.webhook_id)
    if not webhook:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    payload = dict(original.payload_json or {})
    payload["replay"] = True
    payload["replay_of_delivery_id"] = original.id
    return _replay_deliver(
        db,
        webhook,
        original.event_type,
        payload,
        replay_of=original.id,
        attempt_count=original.attempt_count + 1,
    )


def replay_dead_letter_batch(db: Session, *, limit: int = 25) -> dict[str, int]:
    rows = list_deliveries(db, status=webhook_dlq.STATUS_DEAD_LETTER, limit=limit)
    replayed = succeeded = 0
    for row in rows:
        try:
            d = replay_delivery(db, row.id)
            replayed += 1
            if d.success:
                succeeded += 1
        except HTTPException:
            continue
    return {"requested": len(rows), "replayed": replayed, "succeeded": succeeded}


def _replay_deliver(
    db: Session,
    webhook: HardwareCapabilityWebhook,
    event_type: str,
    payload: dict[str, Any],
    *,
    replay_of: str,
    attempt_count: int,
) -> HardwareCapabilityWebhookDelivery:
    if not get_settings().webhook_dispatch_enabled:
        ok, http_status, snippet = True, 200, "dispatch_disabled_simulated_replay"
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
    st = webhook_dlq.apply_delivery_status(db, webhook_id=webhook.id, success=ok, response_snippet=snippet)
    delivery = HardwareCapabilityWebhookDelivery(
        id=new_id(),
        webhook_id=webhook.id,
        event_type=event_type,
        payload_json=payload,
        http_status=http_status,
        success=ok,
        response_snippet=snippet,
        status=st,
        attempt_count=attempt_count,
        dead_lettered_at=webhook_dlq.dead_lettered_at_for_status(st),
        replay_of_delivery_id=replay_of,
        created_at=now,
    )
    db.add(delivery)
    db.commit()
    db.refresh(delivery)
    return delivery


def seed_demo_deliveries_to_dlq(db: Session) -> dict[str, int]:
    """Força 3 falhas → DEAD_LETTER no primeiro webhook ativo (dev/demo)."""
    from unittest.mock import patch

    webhook = db.query(HardwareCapabilityWebhook).filter(HardwareCapabilityWebhook.active.is_(True)).first()
    if not webhook:
        return {"dead_letter": 0}
    with patch("app.services.capability_webhook_service.dispatch_webhook", return_value=(False, 500, "fail")):
        for _ in range(3):
            deliver_event(db, webhook, EVENT_TEST_PING, {"demo": True}, force=True)
    dlq_count = len(list_deliveries(db, status=webhook_dlq.STATUS_DEAD_LETTER, webhook_id=webhook.id))
    return {"dead_letter": dlq_count}
