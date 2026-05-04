from __future__ import annotations

import json
from typing import Any, Callable

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.events import stream_keys
from app.services import reservation_service
from metrics.inventory_metrics import inc_stream, inc_stream_error


Handler = Callable[[Session, dict[str, Any]], None]


def _decode_map(fields: dict) -> dict:
    out: dict[str, Any] = {}
    for k, v in fields.items():
        kk = k.decode() if isinstance(k, bytes) else str(k)
        vv = v.decode() if isinstance(v, bytes) else v
        out[kk] = vv
    return out


def _parse(raw: dict) -> dict[str, Any] | None:
    fields = _decode_map(raw)
    data = fields.get("data")
    if not data:
        return None
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        return None


def process_message(db: Session, obj: dict[str, Any], store: Any, handlers: dict[str, Handler] | None = None) -> None:
    et_raw = obj.get("type")
    payload = obj.get("payload") or {}
    if handlers and et_raw in handlers:
        handlers[et_raw](db, payload)
    elif et_raw == stream_keys.PAYMENT_CONFIRMED:
        reservation_service.on_payment_confirmed(db, str(payload.get("order_id", "")), store)
    elif et_raw == stream_keys.ORDER_EXPIRED:
        reservation_service.expire_reservation(db, str(payload.get("order_id", "")))
    else:
        raise ValueError("unsupported_event")
    inc_stream(str(et_raw or "unknown"))


def push_dlq(r: Redis | None, message_id: str, raw: dict, err: str) -> None:
    if r is None:
        return
    settings = get_settings()
    safe = _decode_map(raw)
    body = json.dumps({"message_id": message_id, "raw": safe, "error": err})
    r.xadd(settings.dlq_stream, {"data": body})


def read_dlq(r: Redis | None, count: int = 50) -> list[dict[str, Any]]:
    if r is None:
        return []
    settings = get_settings()
    entries = r.xrevrange(settings.dlq_stream, count=count)
    out: list[dict[str, Any]] = []
    for _mid, fields in entries:
        parsed = _parse(fields)
        if parsed:
            out.append(parsed)
    return out


def consume_once(
    r: Redis,
    db_factory: Callable[[], Session] | None = None,
    store: Any = None,
    consumer_name: str = "worker-1",
) -> int:
    settings = get_settings()
    factory = db_factory or SessionLocal
    try:
        r.xgroup_create(settings.events_stream, settings.consumer_group, id="0", mkstream=True)
    except Exception:
        pass
    msgs = r.xreadgroup(settings.consumer_group, consumer_name, {settings.events_stream: ">"}, count=10, block=100)
    processed = 0
    for _stream, items in msgs or []:
        for msg_id, fields in items:
            obj = _parse(fields)
            mid = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
            if not obj:
                r.xack(settings.events_stream, settings.consumer_group, msg_id)
                continue
            db = factory()
            try:
                process_message(db, obj, store)
                db.commit()
                r.xack(settings.events_stream, settings.consumer_group, msg_id)
                processed += 1
            except Exception as e:
                db.rollback()
                inc_stream_error()
                push_dlq(r, mid, dict(fields), str(e))
                r.xack(settings.events_stream, settings.consumer_group, msg_id)
            finally:
                db.close()
    return processed
