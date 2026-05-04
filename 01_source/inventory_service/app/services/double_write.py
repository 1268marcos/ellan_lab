"""Double-write: persist DB mutation and mirror to Redis stream for reconciliation."""

from __future__ import annotations

import json
from typing import Any

from redis import Redis

from app.core.config import get_settings


def mirror_inventory_state(r: Redis | None, sku_id: str, quantity_on_hand: int, version: int) -> str | None:
    if r is None:
        return None
    settings = get_settings()
    body = json.dumps({"sku_id": sku_id, "quantity_on_hand": quantity_on_hand, "version": version})
    return r.xadd(f"{settings.events_stream}:mirror", {"data": body})


def replay_mirror_count(r: Redis | None) -> int:
    if r is None:
        return 0
    settings = get_settings()
    key = f"{settings.events_stream}:mirror"
    try:
        return int(r.xlen(key))
    except Exception:
        return 0
