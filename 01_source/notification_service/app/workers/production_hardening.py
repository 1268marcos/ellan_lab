from __future__ import annotations

import json
import time
from typing import Any, Callable

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.notification import Notification
from app.services import email, sms, whatsapp


def push_dlq(r: Redis | None, item: dict[str, Any]) -> None:
    if r is None:
        return
    r.lpush("notification:dlq", json.dumps(item))


def rate_limited(r: Redis | None, key: str) -> bool:
    if r is None:
        return False
    settings = get_settings()
    n = int(r.incr(key))
    if n == 1:
        r.expire(key, 3600)
    return n > settings.rate_limit_per_hour


def deliver_one(db: Session, r: Redis | None, n: Notification, order_id: str) -> bool:
    settings = get_settings()
    rl_key = f"notification:rl:{n.channel}:{n.id}"
    if rate_limited(r, rl_key):
        n.status = "rate_limited"
        n.last_error = "rate limit"
        db.commit()
        return False
    delay = 0.0
    for attempt in range(settings.max_retries):
        if n.channel == "email":
            text = email.render_email(n.payload, order_id)
            ok = email.send_email("x@y.z", "subj", text)
        elif n.channel == "sms":
            text = sms.render_sms(n.payload, order_id)
            ok = sms.send_sms("+10000000000", text)
        elif n.channel == "whatsapp":
            text = whatsapp.render_whatsapp(n.payload, order_id)
            ok = whatsapp.send_whatsapp("+10000000000", text)
        else:
            ok = False
        if ok:
            n.status = "sent"
            n.attempts = attempt + 1
            db.commit()
            return True
        n.attempts = attempt + 1
        n.last_error = "retry"
        db.commit()
        if attempt + 1 < settings.max_retries:
            time.sleep(delay if delay > 0 else 0.001)
            delay = 0.002 * (2**attempt)
    n.status = "failed"
    db.commit()
    push_dlq(r, {"id": n.id, "channel": n.channel, "payload": n.payload})
    return False


def process_queue(
    db: Session,
    r: Redis | None,
    order_id: str,
    sender: Callable[[Session, Redis | None, Notification, str], bool] | None = None,
) -> int:
    fn = sender or deliver_one
    rows = db.query(Notification).filter(Notification.status == "queued").all()
    n = 0
    for row in rows:
        if fn(db, r, row, order_id):
            n += 1
    return n
