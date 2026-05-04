from __future__ import annotations

import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

WEBHOOK_HASH = "catalog:partner_webhooks"


def configure_webhook(redis: Any, *, partner_id: str, url: str, secret: str | None, events: list[str] | None) -> None:
    payload = {"url": url, "secret": secret, "events": events or ["*"]}
    redis.hset(WEBHOOK_HASH, partner_id, json.dumps(payload))


def get_webhook(redis: Any, partner_id: str) -> dict[str, Any] | None:
    raw = redis.hget(WEBHOOK_HASH, partner_id)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode()
    return json.loads(raw)


def deliver_sync(url: str, secret: str | None, event_type: str, body: dict[str, Any]) -> tuple[int, str | None]:
    headers = {"Content-Type": "application/json", "X-Event-Type": event_type}
    if secret:
        headers["X-Webhook-Secret"] = secret
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.post(url, json=body, headers=headers)
            return r.status_code, None if r.is_success else r.text[:300]
    except Exception as exc:
        logger.warning("webhook_delivery_failed %s", exc)
        return 0, str(exc)[:300]


def notify_partner(redis: Any, partner_id: str, event_type: str, body: dict[str, Any]) -> None:
    cfg = get_webhook(redis, partner_id)
    if not cfg:
        return
    url = cfg.get("url")
    if not url:
        return
    events = cfg.get("events") or ["*"]
    if "*" not in events and event_type not in events:
        return
    deliver_sync(url, cfg.get("secret"), event_type, body)
