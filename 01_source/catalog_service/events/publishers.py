from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis

from config import settings

logger = logging.getLogger(__name__)
_client: redis.Redis | None = None


def set_redis_client(client: redis.Redis | None) -> None:
    global _client
    _client = client


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def publish_catalog_event(event_type: str, payload: dict[str, Any]) -> str | None:
    fields = {
        "event_type": event_type,
        "payload": json.dumps(payload, default=str),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        rid = get_redis().xadd(settings.catalog_stream_key, fields)
        return str(rid)
    except Exception as exc:
        logger.warning("catalog stream publish failed: %s", exc)
        return None


def publish_product_created(payload: dict[str, Any]) -> str | None:
    return publish_catalog_event("product.created", payload)


def publish_product_price_changed(payload: dict[str, Any]) -> str | None:
    return publish_catalog_event("product.price_changed", payload)


def publish_product_deprecated(payload: dict[str, Any]) -> str | None:
    return publish_catalog_event("product.deprecated", payload)
