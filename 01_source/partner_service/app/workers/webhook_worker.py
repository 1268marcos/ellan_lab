from __future__ import annotations

import json
import logging
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.models.webhook import PartnerWebhookDelivery, PartnerWebhookSubscription
from app.services.webhook_delivery import deliver_http_sync

logger = logging.getLogger(__name__)


def _decode_fields(raw: dict[Any, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in raw.items():
        key = k.decode() if isinstance(k, bytes) else str(k)
        val = v.decode() if isinstance(v, bytes) else str(v)
        out[key] = val
    return out


def process_stream_batch(
    *,
    db: Session,
    redis_client: Any,
    stream_key: str,
    group: str,
    consumer: str,
    handler: Callable[[Session, dict[str, str]], None] | None = None,
    count: int = 10,
    block_ms: int = 1,
) -> int:
    try:
        redis_client.xgroup_create(stream_key, group, id="0", mkstream=True)
    except Exception:
        pass
    streams = {stream_key: ">"}
    items = redis_client.xreadgroup(group, consumer, streams, count=count, block=block_ms)
    n = 0
    if not items:
        return 0
    for _stream_name, messages in items:
        for msg_id, raw_fields in messages:
            fields = _decode_fields(raw_fields)
            if handler:
                handler(db, fields)
            else:
                _default_handle_message(db, fields)
            redis_client.xack(stream_key, group, msg_id)
            n += 1
    return n


def _default_handle_message(db: Session, fields: dict[str, str]) -> None:
    payload_raw = fields.get("payload") or "{}"
    try:
        outer = json.loads(payload_raw)
    except json.JSONDecodeError:
        logger.warning("webhook_worker_invalid_json")
        return
    delivery_id = outer.get("delivery_id")
    if not delivery_id:
        return
    delivery = db.query(PartnerWebhookDelivery).filter(PartnerWebhookDelivery.id == delivery_id).first()
    if not delivery:
        return
    sub = (
        db.query(PartnerWebhookSubscription)
        .filter(PartnerWebhookSubscription.id == delivery.subscription_id)
        .first()
    )
    if not sub:
        return
    inner = {k: v for k, v in outer.items() if k != "delivery_id"}
    code, err = deliver_http_sync(sub, inner)
    delivery.attempts += 1
    if code and 200 <= code < 300:
        delivery.status = "DELIVERED"
        delivery.last_error = None
    else:
        delivery.status = "FAILED"
        delivery.last_error = err or f"http_{code}"
    db.add(delivery)
    db.commit()
