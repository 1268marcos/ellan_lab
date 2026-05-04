from __future__ import annotations

import json
from typing import Any

from redis import Redis


def enqueue(r: Redis | None, key: str, payload: dict[str, Any]) -> str | None:
    if r is None:
        return None
    return r.lpush(key, json.dumps(payload))  # type: ignore[return-value]


def dequeue(r: Redis | None, key: str) -> dict[str, Any] | None:
    if r is None:
        return None
    raw = r.rpop(key)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode()
    return json.loads(raw)
