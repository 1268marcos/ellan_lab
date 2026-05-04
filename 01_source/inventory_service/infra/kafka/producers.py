from __future__ import annotations

import json
from typing import Any

try:
    from kafka import KafkaProducer
except Exception:  # pragma: no cover
    KafkaProducer = None  # type: ignore[misc, assignment]


def _producer(bootstrap_servers: str) -> Any:
    if KafkaProducer is None:
        return None
    try:
        return KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            request_timeout_ms=800,
        )
    except Exception:
        return None


def _emit(topic: str, bootstrap_servers: str, event_type: str, payload: dict[str, Any]) -> bool:
    p = _producer(bootstrap_servers)
    if p is None:
        return False
    ok = False
    try:
        p.send(topic, {"type": event_type, "payload": payload})
        p.flush(timeout=2)
        ok = True
    except Exception:
        ok = False
    finally:
        try:
            p.close()
        except Exception:
            ok = False
    return ok


def emit_product_event(bootstrap_servers: str, event_type: str, payload: dict[str, Any]) -> bool:
    return _emit("catalog-stream", bootstrap_servers, event_type, payload)


def emit_payment_event(bootstrap_servers: str, event_type: str, payload: dict[str, Any]) -> bool:
    return _emit("payment-stream", bootstrap_servers, event_type, payload)


def emit_order_event(bootstrap_servers: str, event_type: str, payload: dict[str, Any]) -> bool:
    return _emit("order-stream", bootstrap_servers, event_type, payload)


def emit_wallet_event(bootstrap_servers: str, event_type: str, payload: dict[str, Any]) -> bool:
    return _emit("wallet-stream", bootstrap_servers, event_type, payload)


def emit_notification_event(bootstrap_servers: str, event_type: str, payload: dict[str, Any]) -> bool:
    return _emit("notification-stream", bootstrap_servers, event_type, payload)


def emit_manifest_created(bootstrap_servers: str, payload: dict[str, Any]) -> bool:
    return _emit("logistics-stream", bootstrap_servers, "manifest.created", payload)
