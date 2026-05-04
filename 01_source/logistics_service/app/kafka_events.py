from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings

try:
    from kafka import KafkaProducer
except Exception:  # pragma: no cover
    KafkaProducer = None  # type: ignore[misc, assignment]


def emit_manifest_created(manifest_id: str, locker_id: str, status: str) -> bool:
    settings = get_settings()
    servers = getattr(settings, "kafka_bootstrap_servers", None) or ""
    if not servers.strip() or KafkaProducer is None:
        return False
    payload: dict[str, Any] = {"manifest_id": manifest_id, "locker_id": locker_id, "status": status}
    p = None
    try:
        p = KafkaProducer(
            bootstrap_servers=servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=800,
        )
        p.send("logistics-stream", {"type": "manifest.created", "payload": payload})
        p.flush(timeout=2)
        return True
    except Exception:
        return False
    finally:
        if p is not None:
            try:
                p.close()
            except Exception:
                pass
