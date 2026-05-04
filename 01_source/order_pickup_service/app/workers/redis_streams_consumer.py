from __future__ import annotations

import json
import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def _decode_fields(fields: dict[Any, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in fields.items():
        key = k.decode() if isinstance(k, (bytes, bytearray)) else str(k)
        val = v.decode() if isinstance(v, (bytes, bytearray)) else str(v)
        out[key] = val
    return out


def process_stream_batch(
    *,
    redis_client: Any,
    stream_key: str,
    group: str,
    consumer_name: str,
    handler: Callable[[str, dict[str, Any]], None],
    count: int = 10,
    block_ms: int = 1,
) -> int:
    """
    Lê um lote via XREADGROUP e entrega payloads decodificados ao handler.
    Retorna número de mensagens processadas.
    """
    try:
        redis_client.xgroup_create(stream_key, group, id="0", mkstream=True)
    except Exception:
        pass
    entries = redis_client.xreadgroup(
        group,
        consumer_name,
        {stream_key: ">"},
        count=count,
        block=block_ms,
    )
    processed = 0
    if not entries:
        return 0
    for _stream, messages in entries:
        for msg_id, raw_fields in messages:
            fields = _decode_fields(dict(raw_fields))
            event_type = fields.get("event_type", "")
            try:
                payload = json.loads(fields.get("payload") or "{}")
            except json.JSONDecodeError:
                payload = {}
            if not isinstance(payload, dict):
                payload = {}
            try:
                handler(event_type, payload)
                redis_client.xack(stream_key, group, msg_id)
                processed += 1
            except Exception:
                logger.exception("stream handler failed msg_id=%s", msg_id)
    return processed
