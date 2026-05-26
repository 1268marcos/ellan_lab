from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.models.bi_webhooks import BiCapabilityWebhook
from app.schemas.bi_webhooks import BiCapabilityWebhookIn
from app.services.crypto_util import hash_secret, new_id


def list_webhooks(db: Session) -> list[BiCapabilityWebhook]:
    return db.query(BiCapabilityWebhook).order_by(BiCapabilityWebhook.network_player_code).all()


def create_webhook(db: Session, body: BiCapabilityWebhookIn) -> BiCapabilityWebhook:
    secret_raw = body.secret or "unset"
    row = BiCapabilityWebhook(
        id=new_id(),
        network_player_code=body.network_player_code,
        capability_code=body.capability_code,
        url=body.url,
        secret_hash=hash_secret(secret_raw),
        secret_key=body.secret,
        event_types_json=json.dumps(body.event_types),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def webhook_out(row: BiCapabilityWebhook) -> dict:
    return {
        "id": row.id,
        "network_player_code": row.network_player_code,
        "capability_code": row.capability_code,
        "url": row.url,
        "event_types": json.loads(row.event_types_json),
        "active": row.active,
        "last_http_status": row.last_http_status,
        "last_delivered_at": row.last_delivered_at,
        "last_error": row.last_error,
        "created_at": row.created_at,
    }
