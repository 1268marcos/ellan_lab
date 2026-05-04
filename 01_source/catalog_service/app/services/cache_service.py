from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings


def cache_key_product(sku_id: str) -> str:
    return f"catalog:product:{sku_id}"


def get_json(redis: Any, key: str) -> dict[str, Any] | None:
    raw = redis.get(key)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def set_json(redis: Any, key: str, value: dict[str, Any], ttl_seconds: int | None = None) -> None:
    s = json.dumps(value, default=str)
    if ttl_seconds is None:
        ttl_seconds = get_settings().product_cache_ttl_seconds
    redis.setex(key, ttl_seconds, s)


def delete(redis: Any, key: str) -> None:
    redis.delete(key)


def invalidate_product(redis: Any, sku_id: str) -> None:
    delete(redis, cache_key_product(sku_id))
