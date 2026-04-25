from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session

from app.core.db import SessionLocal, init_db
from app.models.partner_webhook_delivery import PartnerWebhookDelivery
from app.models.partner_webhook_endpoint import PartnerWebhookEndpoint

MAX_ATTEMPTS_DEFAULT = int(os.getenv("PARTNER_WEBHOOK_MAX_ATTEMPTS", "5"))
POLL_SEC = int(os.getenv("PARTNER_WEBHOOK_DELIVERY_POLL_SEC", "5"))
BATCH_SIZE = int(os.getenv("PARTNER_WEBHOOK_DELIVERY_BATCH_SIZE", "50"))
PROCESSING_STALE_TIMEOUT_SEC = int(os.getenv("PARTNER_WEBHOOK_PROCESSING_STALE_TIMEOUT_SEC", "180"))
HTTP_TIMEOUT_SEC = float(os.getenv("PARTNER_WEBHOOK_HTTP_TIMEOUT_SEC", "8"))


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_retry_policy(raw_value: str | None) -> tuple[int, int]:
    max_attempts = MAX_ATTEMPTS_DEFAULT
    base_backoff_sec = 30
    try:
        payload = json.loads(str(raw_value or "{}"))
        if isinstance(payload, dict):
            max_attempts = int(payload.get("max_attempts", max_attempts) or max_attempts)
            base_backoff_sec = int(payload.get("backoff_sec", base_backoff_sec) or base_backoff_sec)
    except Exception:
        pass
    max_attempts = max(1, min(max_attempts, 20))
    base_backoff_sec = max(5, min(base_backoff_sec, 3600))
    return max_attempts, base_backoff_sec


def _next_retry_at(attempt_count: int, base_backoff_sec: int) -> datetime:
    multiplier = max(1, 2 ** max(0, attempt_count - 1))
    delay = min(base_backoff_sec * multiplier, 3600)
    return _utcnow() + timedelta(seconds=delay)


def _recover_stale_processing(db: Session) -> None:
    now = _utcnow()
    stale_before = now - timedelta(seconds=PROCESSING_STALE_TIMEOUT_SEC)
    stale_rows = (
        db.query(PartnerWebhookDelivery)
        .filter(
            PartnerWebhookDelivery.status == "PROCESSING",
            PartnerWebhookDelivery.processing_started_at.is_not(None),
            PartnerWebhookDelivery.processing_started_at <= stale_before,
        )
        .order_by(PartnerWebhookDelivery.processing_started_at.asc(), PartnerWebhookDelivery.id.asc())
        .limit(BATCH_SIZE)
        .all()
    )
    for row in stale_rows:
        row.status = "FAILED"
        row.last_error = "PROCESSING_STALE_TIMEOUT"
        row.processing_started_at = None
        row.next_retry_at = now
    if stale_rows:
        db.commit()


def _find_candidate_ids(db: Session) -> list[str]:
    now = _utcnow()
    rows = (
        db.query(PartnerWebhookDelivery.id)
        .filter(
            or_(
                PartnerWebhookDelivery.status == "PENDING",
                and_(
                    PartnerWebhookDelivery.status == "FAILED",
                    PartnerWebhookDelivery.next_retry_at.is_not(None),
                    PartnerWebhookDelivery.next_retry_at <= now,
                ),
            )
        )
        .order_by(PartnerWebhookDelivery.created_at.asc(), PartnerWebhookDelivery.id.asc())
        .limit(BATCH_SIZE)
        .all()
    )
    return [str(row[0]) for row in rows]


def _claim_item(db: Session, delivery_id: str) -> PartnerWebhookDelivery | None:
    now = _utcnow()
    result = db.execute(
        update(PartnerWebhookDelivery)
        .where(
            PartnerWebhookDelivery.id == delivery_id,
            PartnerWebhookDelivery.status.in_(["PENDING", "FAILED"]),
        )
        .values(
            status="PROCESSING",
            processing_started_at=now,
            last_error=None,
        )
    )
    if (result.rowcount or 0) != 1:
        db.rollback()
        return None
    db.commit()
    return db.get(PartnerWebhookDelivery, delivery_id)


def _mark_dead(db: Session, item: PartnerWebhookDelivery, message: str | None = None) -> None:
    item.status = "DEAD_LETTER"
    item.last_error = message
    item.processing_started_at = None
    item.next_retry_at = None
    db.commit()


def _mark_failed(db: Session, item: PartnerWebhookDelivery, error_message: str, *, max_attempts: int, base_backoff_sec: int) -> None:
    if (item.attempt_count or 0) >= max_attempts:
        _mark_dead(db, item, error_message)
        return
    item.status = "FAILED"
    item.last_error = error_message[:4000]
    item.processing_started_at = None
    item.next_retry_at = _next_retry_at(int(item.attempt_count or 0), base_backoff_sec)
    db.commit()


def _mark_delivered(db: Session, item: PartnerWebhookDelivery, *, http_status: int) -> None:
    item.status = "DELIVERED"
    item.http_status = int(http_status)
    item.last_error = None
    item.delivered_at = _utcnow()
    item.processing_started_at = None
    item.next_retry_at = None
    db.commit()


def _build_signature(secret_key: str, payload_bytes: bytes) -> str:
    digest = hmac.new(secret_key.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def _deliver_one(item: PartnerWebhookDelivery, endpoint: PartnerWebhookEndpoint) -> int:
    payload_bytes = str(item.payload_json or "{}").encode("utf-8")
    request = urllib.request.Request(
        endpoint.url,
        data=payload_bytes,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    secret = str(getattr(endpoint, "secret_key", "") or "").strip()
    if secret:
        request.add_header("X-Ellan-Signature", _build_signature(secret, payload_bytes))
    request.add_header("X-Ellan-Event", str(item.event_type or "unknown"))
    request.add_header("X-Ellan-Event-Id", str(item.event_id or item.id))
    request.add_header("X-Ellan-Api-Version", str(endpoint.api_version or "v1"))

    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SEC) as response:
        return int(response.status)


def run_partner_webhook_delivery_once(db: Session) -> None:
    _recover_stale_processing(db)
    ids = _find_candidate_ids(db)
    for delivery_id in ids:
        item = _claim_item(db, delivery_id)
        if item is None:
            continue

        endpoint = db.get(PartnerWebhookEndpoint, item.endpoint_id)
        if endpoint is None:
            _mark_dead(db, item, "WEBHOOK_ENDPOINT_NOT_FOUND")
            continue
        if not endpoint.active:
            item.status = "SKIPPED"
            item.last_error = "WEBHOOK_ENDPOINT_INACTIVE"
            item.processing_started_at = None
            item.next_retry_at = None
            db.commit()
            continue

        max_attempts, base_backoff_sec = _parse_retry_policy(endpoint.retry_policy)

        try:
            item.attempt_count = int(item.attempt_count or 0) + 1
            db.commit()
            http_status = _deliver_one(item, endpoint)
            if 200 <= http_status < 300:
                _mark_delivered(db, item, http_status=http_status)
            else:
                _mark_failed(
                    db,
                    item,
                    f"HTTP_{http_status}",
                    max_attempts=max_attempts,
                    base_backoff_sec=base_backoff_sec,
                )
        except urllib.error.HTTPError as exc:
            _mark_failed(
                db,
                item,
                f"HTTP_ERROR_{int(getattr(exc, 'code', 0) or 0)}",
                max_attempts=max_attempts,
                base_backoff_sec=base_backoff_sec,
            )
        except Exception as exc:
            _mark_failed(
                db,
                item,
                str(exc),
                max_attempts=max_attempts,
                base_backoff_sec=base_backoff_sec,
            )


def main() -> None:
    init_db()
    while True:
        db = SessionLocal()
        try:
            run_partner_webhook_delivery_once(db)
        finally:
            db.close()
        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
