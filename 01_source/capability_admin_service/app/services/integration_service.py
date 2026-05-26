from __future__ import annotations

import json

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.capability import CapabilityProfile
from app.models.integration import CapabilityProfileApiKey, CapabilityProfileWebhook
from app.schemas.common import ApiKeyRotateOut, WebhookIn
from app.services.audit_service import log_audit
from app.services.crypto_util import generate_api_key, hash_secret, new_id


def configure_webhook(db: Session, body: WebhookIn) -> CapabilityProfileWebhook:
    profile = db.get(CapabilityProfile, body.profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
    secret = body.secret or f"whsec_{profile.profile_code}"
    pepper = get_settings().api_key_pepper
    events = json.dumps(body.events or ["capability.profile.changed", "capability.health"])
    row = db.query(CapabilityProfileWebhook).filter(CapabilityProfileWebhook.profile_id == body.profile_id).first()
    if row:
        row.url = body.url
        row.secret_hash = hash_secret(secret, pepper)
        row.secret_preview = secret[:8] + "…"
        row.event_types_json = events
        row.active = body.active
        row.profile_code = profile.profile_code
    else:
        row = CapabilityProfileWebhook(
            id=new_id(),
            profile_id=body.profile_id,
            profile_code=profile.profile_code,
            url=body.url,
            secret_hash=hash_secret(secret, pepper),
            secret_preview=secret[:8] + "…",
            event_types_json=events,
            active=body.active,
        )
        db.add(row)
    log_audit(
        db,
        entity_type="webhook",
        entity_id=row.id,
        action="UPSERT",
        profile_id=body.profile_id,
        payload={"url": body.url},
    )
    db.commit()
    db.refresh(row)
    return row


def rotate_api_key(db: Session, profile_id: int, label: str | None = None) -> ApiKeyRotateOut:
    profile = db.get(CapabilityProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="profile_not_found")
    prefix, raw = generate_api_key("cap")
    pepper = get_settings().api_key_pepper
    for old in db.query(CapabilityProfileApiKey).filter(
        CapabilityProfileApiKey.profile_id == profile_id, CapabilityProfileApiKey.active.is_(True)
    ):
        old.active = False
    row = CapabilityProfileApiKey(
        id=new_id(),
        profile_id=profile_id,
        profile_code=profile.profile_code,
        key_prefix=prefix,
        key_hash=hash_secret(raw, pepper),
        label=label,
        active=True,
    )
    db.add(row)
    log_audit(
        db,
        entity_type="api_key",
        entity_id=row.id,
        action="ROTATE",
        profile_id=profile_id,
        payload={"key_prefix": prefix},
    )
    db.commit()
    return ApiKeyRotateOut(api_key=raw, key_prefix=prefix, profile_id=profile_id, profile_code=profile.profile_code)


async def test_webhook(db: Session, webhook_id: str) -> dict:
    import json

    import httpx

    from app.models.ecosystem import CapabilityProfileWebhookDelivery

    row = db.get(CapabilityProfileWebhook, webhook_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    payload = {"event": "webhook.test", "profile_code": row.profile_code}
    delivery = CapabilityProfileWebhookDelivery(
        id=new_id(),
        webhook_id=row.id,
        event_type="webhook.test",
        payload_json=json.dumps(payload),
        status="PENDING",
    )
    db.add(delivery)
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(row.url, json=payload)
        row.last_http_status = resp.status_code
        delivery.http_status = resp.status_code
        delivery.success = 200 <= resp.status_code < 300
        delivery.status = "DELIVERED" if delivery.success else "FAILED"
        if not delivery.success:
            delivery.dead_lettered_at = _utcnow()
        db.commit()
        return {"http_status": resp.status_code, "ok": delivery.success, "delivery_id": delivery.id}
    except Exception as exc:
        row.last_http_status = 0
        delivery.http_status = 0
        delivery.success = False
        delivery.status = "FAILED"
        delivery.dead_lettered_at = _utcnow()
        db.commit()
        return {"http_status": 0, "ok": False, "error": str(exc), "delivery_id": delivery.id}
