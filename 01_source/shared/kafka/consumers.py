from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

from shared.kafka.topics import DLQ_SUFFIX

logger = logging.getLogger(__name__)


def dlq_name(stream: str) -> str:
    if stream.endswith(DLQ_SUFFIX):
        return stream
    return f"{stream}{DLQ_SUFFIX}"


def handle_or_dlq(
    *,
    stream: str,
    payload: dict[str, Any],
    handler: Callable[[dict[str, Any]], None],
    publish_dlq: Callable[[str, str], None] | None = None,
) -> bool:
    try:
        handler(payload)
        return True
    except Exception:
        logger.exception("kafka_consumer_handler_failed stream=%s", stream)
        if publish_dlq is not None:
            publish_dlq(dlq_name(stream), json.dumps({"stream": stream, "payload": payload}))
        return False
