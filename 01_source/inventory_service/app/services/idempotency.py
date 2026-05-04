from __future__ import annotations

import json
from typing import Any

from redis import Redis


class IdempotencyStore:
    def __init__(self, r: Redis | None, prefix: str = "idem:inventory:") -> None:
        self._r = r
        self._prefix = prefix
        self._mem: dict[str, str] = {}

    def get(self, key: str) -> dict[str, Any] | None:
        if self._r is None:
            raw = self._mem.get(self._prefix + key)
            return json.loads(raw) if raw else None
        raw = self._r.get(self._prefix + key)
        if raw is None:
            return None
        if isinstance(raw, bytes):
            raw = raw.decode()
        return json.loads(raw)

    def set(self, key: str, payload: dict[str, Any], ttl_sec: int = 86400) -> None:
        raw = json.dumps(payload)
        if self._r is None:
            self._mem[self._prefix + key] = raw
            return
        self._r.setex(self._prefix + key, ttl_sec, raw)
