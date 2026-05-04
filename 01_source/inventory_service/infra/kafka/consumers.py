from __future__ import annotations

import json
from typing import Any, Callable

try:
    from kafka import KafkaConsumer
except Exception:  # pragma: no cover
    KafkaConsumer = None  # type: ignore[misc, assignment]

Handler = Callable[[dict[str, Any]], None]


def inventory_consumer(
    bootstrap_servers: str,
    topics: tuple[str, ...],
    group_id: str,
    handler: Handler,
) -> Any:
    if KafkaConsumer is None:
        return None
    try:
        return KafkaConsumer(
            *topics,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            enable_auto_commit=True,
            value_deserializer=lambda b: json.loads(b.decode("utf-8")),
            auto_offset_reset="earliest",
            consumer_timeout_ms=500,
            request_timeout_ms=800,
        )
    except Exception:
        return None


def poll_batch(consumer: Any, max_records: int = 10) -> list[dict[str, Any]]:
    if consumer is None:
        return []
    out: list[dict[str, Any]] = []
    try:
        pack = consumer.poll(timeout_ms=200, max_records=max_records)
    except Exception:
        return []
    for _tp, records in pack.items():
        for rec in records:
            if rec.value:
                out.append(rec.value)
    return out
