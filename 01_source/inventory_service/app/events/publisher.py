from __future__ import annotations

import json
from typing import Any

from redis import Redis

from app.core.config import get_settings


def publish_event(r: Redis | None, event_type: str, payload: dict[str, Any]) -> str | None:
    if r is None:
        return None
    settings = get_settings()
    body = json.dumps({"type": event_type, "payload": payload})
    return r.xadd(settings.events_stream, {"data": body})
