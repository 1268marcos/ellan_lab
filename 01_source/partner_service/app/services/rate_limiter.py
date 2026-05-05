from __future__ import annotations

import time
from typing import Any

DEFAULT_LIMIT_PER_MINUTE = 100


def _window_key(partner_id: str, minute_epoch: int) -> str:
    return f"ratelimit:partner:{partner_id}:{minute_epoch}"


def sync_check_and_increment(redis: Any, *, partner_id: str, limit_per_minute: int) -> tuple[bool, int]:
    """Sync variant for tests with fakeredis without await."""
    now = int(time.time())
    window = now // 60
    key = _window_key(partner_id, window)
    try:
        count = int(redis.incr(key))
        if count == 1:
            redis.expire(key, 120)
    except Exception:
        # Fail-open when Redis is unavailable (common in local dev).
        return True, 0
    allowed = count <= limit_per_minute
    return allowed, count
