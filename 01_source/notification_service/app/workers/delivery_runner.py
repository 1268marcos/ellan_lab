from __future__ import annotations

import logging
import time

import redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal, init_db
from app.models.notification import Notification
from app.services.queue_consumer import dequeue
from app.workers.delivery_worker import deliver_one

logger = logging.getLogger("notification_delivery_worker")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [notification_delivery_worker] %(message)s",
)


def _poll_interval_sec() -> float:
    raw = "1.0"
    try:
        import os

        raw = os.getenv("NOTIFICATION_DELIVERY_POLL_SEC", "1.0")
        return max(0.1, float(raw))
    except Exception:
        logger.warning("invalid NOTIFICATION_DELIVERY_POLL_SEC=%s, using 1.0", raw)
        return 1.0


def _process_one(db: Session, redis_client: redis.Redis | None, item: dict) -> bool:
    notification_id = item.get("id")
    order_id = str(item.get("order_id") or "unknown")
    if not notification_id:
        logger.warning("queue item without id: %s", item)
        return False

    n = db.get(Notification, str(notification_id))
    if n is None:
        logger.warning("notification not found for id=%s", notification_id)
        return False

    if n.status != "queued":
        return False

    sent = deliver_one(db, redis_client, n, order_id)
    logger.info("processed id=%s channel=%s sent=%s", n.id, n.channel, sent)
    return sent


def main() -> None:
    init_db()
    settings = get_settings()
    poll = _poll_interval_sec()

    try:
        redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=False)
        redis_client.ping()
        logger.info("redis connected")
    except Exception:
        redis_client = None
        logger.warning("redis unavailable; worker will idle")

    logger.info("delivery worker started; poll=%s", poll)
    while True:
        try:
            item = dequeue(redis_client, "notification:queue")
            if item is None:
                time.sleep(poll)
                continue

            with SessionLocal() as db:
                _process_one(db, redis_client, item)
        except KeyboardInterrupt:
            logger.info("delivery worker stopping by signal")
            break
        except Exception:
            logger.exception("worker cycle failed")
            time.sleep(poll)


if __name__ == "__main__":
    main()
