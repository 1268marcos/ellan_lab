from __future__ import annotations

import json
import logging
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _decode_entry(raw_fields: dict[Any, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in raw_fields.items():
        key = k.decode() if isinstance(k, bytes) else str(k)
        val = v.decode() if isinstance(v, bytes) else str(v)
        out[key] = val
    return out


def replay_range(
    redis: Any,
    db: Session,
    *,
    handler: Callable[[Session, str, dict[str, Any]], None],
    start_id: str = "0",
    count: int = 100,
) -> int:
    key = get_settings().catalog_stream_key
    try:
        entries = redis.xrange(key, min=start_id, max="+", count=count)
    except Exception as exc:
        logger.warning("replay_xrange_failed %s", exc)
        return 0
    n = 0
    if not entries:
        return 0
    for _eid, raw in entries:
        fields = _decode_entry(raw)
        et = fields.get("event_type") or ""
        try:
            payload = json.loads(fields.get("payload") or "{}")
        except json.JSONDecodeError:
            continue
        handler(db, et, payload)
        n += 1
    return n
