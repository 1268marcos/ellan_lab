from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.webhook import SellerWebhookEndpoint
from app.schemas.webhook import WebhookConfigureIn, WebhookOut
from app.services.crypto_util import hash_secret, new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def configure_webhook(db: Session, seller_id: str, body: WebhookConfigureIn) -> WebhookOut:
    get_seller_or_404(db, seller_id)
    secret = body.secret or ""
    secret_hash = hash_secret(secret) if secret else hash_secret(seller_id)
    events_json = json.dumps(body.events)
    now = _utcnow()
    row = db.query(SellerWebhookEndpoint).filter(SellerWebhookEndpoint.seller_id == seller_id).first()
    if row:
        row.url = body.url
        row.secret_hash = secret_hash
        if secret:
            row.secret_key = secret[:256]
        row.events_json = events_json
        row.active = body.active
        row.api_version = body.api_version
        row.updated_at = now
    else:
        row = SellerWebhookEndpoint(
            id=new_id(),
            seller_id=seller_id,
            url=body.url,
            secret_hash=secret_hash,
            secret_key=secret[:256] if secret else None,
            events_json=events_json,
            api_version=body.api_version,
            active=body.active,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return WebhookOut.model_validate(row)


def get_webhook(db: Session, seller_id: str) -> WebhookOut | None:
    row = db.query(SellerWebhookEndpoint).filter(SellerWebhookEndpoint.seller_id == seller_id).first()
    return WebhookOut.model_validate(row) if row else None
