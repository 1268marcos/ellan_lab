from __future__ import annotations

import hashlib
import hmac
import json
from datetime import timedelta

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.privacy import PrivacyWebhookEndpoint
from app.models.privacy_pro import PrivacyWebhookDelivery
from app.services.crypto_util import new_id, utcnow
from app.services.privacy_pro_service import log_audit


def _delivery_out(row: PrivacyWebhookDelivery) -> dict:
    return {
        "id": row.id,
        "webhook_id": row.webhook_id,
        "regulation_code": row.regulation_code,
        "event_name": row.event_name,
        "aggregate_id": row.aggregate_id,
        "payload": json.loads(row.payload_json or "{}"),
        "status": row.status,
        "attempt_count": row.attempt_count,
        "max_attempts": row.max_attempts,
        "last_status_code": row.last_status_code,
        "last_response_body": row.last_response_body,
        "last_attempt_at": row.last_attempt_at,
        "next_attempt_at": row.next_attempt_at,
        "delivered_at": row.delivered_at,
        "created_at": row.created_at,
    }


def _sign_payload(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def enqueue_webhook_event(
    db: Session,
    *,
    regulation_code: str,
    event_name: str,
    payload: dict,
    aggregate_id: str | None = None,
) -> PrivacyWebhookDelivery:
    code = regulation_code.upper()
    endpoint = (
        db.query(PrivacyWebhookEndpoint)
        .filter(PrivacyWebhookEndpoint.regulation_code == code, PrivacyWebhookEndpoint.active.is_(True))
        .first()
    )
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_configured")

    events = json.loads(endpoint.events_json or "[]")
    if events and event_name not in events:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="event_not_subscribed")

    now = utcnow()
    row = PrivacyWebhookDelivery(
        id=new_id(),
        webhook_id=endpoint.id,
        regulation_code=code,
        event_name=event_name,
        aggregate_id=aggregate_id,
        payload_json=json.dumps(payload),
        status="PENDING",
        attempt_count=0,
        max_attempts=5,
        next_attempt_at=now,
        created_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_webhook_deliveries(
    db: Session,
    *,
    regulation_code: str | None = None,
    webhook_id: str | None = None,
    status_filter: str | None = None,
    limit: int = 100,
) -> list[dict]:
    q = db.query(PrivacyWebhookDelivery)
    if regulation_code:
        q = q.filter(PrivacyWebhookDelivery.regulation_code == regulation_code.upper())
    if webhook_id:
        q = q.filter(PrivacyWebhookDelivery.webhook_id == webhook_id)
    if status_filter:
        q = q.filter(PrivacyWebhookDelivery.status == status_filter.upper())
    rows = q.order_by(PrivacyWebhookDelivery.created_at.desc()).limit(limit).all()
    return [_delivery_out(r) for r in rows]


def _attempt_delivery(db: Session, row: PrivacyWebhookDelivery, endpoint: PrivacyWebhookEndpoint) -> PrivacyWebhookDelivery:
    settings = get_settings()
    body = row.payload_json.encode()
    headers = {"Content-Type": "application/json", "X-Privacy-Event": row.event_name}
    if endpoint.secret_ref:
        headers["X-Privacy-Signature"] = _sign_payload(endpoint.secret_ref, body)

    now = utcnow()
    row.attempt_count += 1
    row.last_attempt_at = now

    simulate = "example" in endpoint.url or endpoint.url.startswith("https://hooks.ellanlab.example")
    try:
        if simulate:
            row.last_status_code = 202
            row.last_response_body = "simulated_accepted"
            row.status = "DELIVERED"
            row.delivered_at = now
        else:
            with httpx.Client(timeout=settings.webhook_dispatch_timeout_sec) as client:
                resp = client.post(endpoint.url, content=body, headers=headers)
            row.last_status_code = resp.status_code
            row.last_response_body = (resp.text or "")[:2000]
            if 200 <= resp.status_code < 300:
                row.status = "DELIVERED"
                row.delivered_at = now
            elif row.attempt_count >= row.max_attempts:
                row.status = "FAILED"
                row.next_attempt_at = now + timedelta(minutes=15 * row.attempt_count)
            else:
                row.status = "PENDING"
                row.next_attempt_at = now + timedelta(minutes=2 ** row.attempt_count)
    except Exception as exc:
        row.last_status_code = None
        row.last_response_body = str(exc)[:2000]
        if row.attempt_count >= row.max_attempts:
            row.status = "FAILED"
        else:
            row.status = "PENDING"
            row.next_attempt_at = now + timedelta(minutes=2 ** row.attempt_count)

    db.commit()
    db.refresh(row)
    return row


def dispatch_delivery(db: Session, delivery_id: str) -> dict:
    row = db.get(PrivacyWebhookDelivery, delivery_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="delivery_not_found")
    endpoint = db.get(PrivacyWebhookEndpoint, row.webhook_id)
    if not endpoint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    _attempt_delivery(db, row, endpoint)
    log_audit(
        db,
        action="WEBHOOK_DISPATCH",
        resource_type="privacy_webhook_delivery",
        resource_id=row.id,
        regulation_code=row.regulation_code,
        summary=f"Webhook {row.event_name} → {row.status}",
    )
    return _delivery_out(row)


def process_pending_deliveries(db: Session, *, limit: int = 20) -> dict:
    now = utcnow()
    rows = (
        db.query(PrivacyWebhookDelivery)
        .filter(
            PrivacyWebhookDelivery.status == "PENDING",
            PrivacyWebhookDelivery.next_attempt_at <= now,
        )
        .order_by(PrivacyWebhookDelivery.next_attempt_at)
        .limit(limit)
        .all()
    )
    processed = 0
    delivered = 0
    failed = 0
    for row in rows:
        endpoint = db.get(PrivacyWebhookEndpoint, row.webhook_id)
        if not endpoint:
            row.status = "FAILED"
            row.last_response_body = "endpoint_missing"
            db.commit()
            failed += 1
            continue
        _attempt_delivery(db, row, endpoint)
        processed += 1
        if row.status == "DELIVERED":
            delivered += 1
        elif row.status == "FAILED":
            failed += 1
    return {"processed": processed, "delivered": delivered, "failed": failed, "pending": len(rows) - delivered - failed}
