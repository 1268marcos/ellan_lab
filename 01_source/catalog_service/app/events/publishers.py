from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.events import streams


def _fields(event_type: str, payload: dict[str, Any]) -> dict[str, str]:
    return {
        "event_type": event_type,
        "payload": json.dumps(payload, default=str),
        "occurred_at": datetime.now(timezone.utc).isoformat(),
    }


def publish(redis: Any, event_type: str, payload: dict[str, Any]) -> str:
    key = get_settings().catalog_stream_key
    return str(redis.xadd(key, _fields(event_type, payload)))


def publish_product_created(redis: Any, payload: dict[str, Any]) -> str:
    return publish(redis, streams.PRODUCT_CREATED, payload)


def publish_price_changed(redis: Any, payload: dict[str, Any]) -> str:
    return publish(redis, streams.PRODUCT_PRICE_CHANGED, payload)


def publish_deprecated(redis: Any, payload: dict[str, Any]) -> str:
    return publish(redis, streams.PRODUCT_DEPRECATED, payload)


def publish_synced(redis: Any, payload: dict[str, Any]) -> str:
    return publish(redis, streams.PRODUCT_SYNCED, payload)
