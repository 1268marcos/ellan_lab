from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ml_alerts_webhooks import MlCapabilityWebhook, MlCapabilityWebhookDelivery
from app.models.ml_network import MlLockerNetworkPlayer
from app.services.crypto_util import hash_secret, new_id
from app.services.ml_webhook_dispatch import dispatch_webhook

EVENT_READINESS_SCORE_DROP = "readiness.score_drop"
EVENT_TEST_PING = "webhook.test"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def configure_ml_capability_webhook(
    db: Session,
    *,
    network_player_id: str,
    capability_code: str,
    url: str,
    secret: str | None = None,
    events: list[str] | None = None,
) -> MlCapabilityWebhook:
    player = db.get(MlLockerNetworkPlayer, network_player_id)
    if not player:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="network_player_not_found")
    secret_val = secret or ""
    secret_hash = hash_secret(secret_val) if secret_val else hash_secret(f"{network_player_id}:{capability_code}")
    now = _utcnow()
    row = (
        db.query(MlCapabilityWebhook)
        .filter(
            MlCapabilityWebhook.network_player_id == network_player_id,
            MlCapabilityWebhook.capability_code == capability_code,
        )
        .first()
    )
    if row:
        row.url = url
        row.secret_hash = secret_hash
        if secret_val:
            row.secret_key = secret_val[:256]
        row.event_types_json = json.dumps(events or [EVENT_READINESS_SCORE_DROP])
        row.active = True
        row.updated_at = now
    else:
        row = MlCapabilityWebhook(
            id=new_id(),
            network_player_id=network_player_id,
            network_player_code=player.code,
            capability_code=capability_code,
            url=url,
            secret_hash=secret_hash,
            secret_key=secret_val[:256] if secret_val else None,
            event_types_json=json.dumps(events or [EVENT_READINESS_SCORE_DROP]),
            active=True,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def dispatch_ml_player_event(db: Session, network_player_id: str, event_type: str, payload: dict[str, Any]) -> int:
    hooks = (
        db.query(MlCapabilityWebhook)
        .filter(MlCapabilityWebhook.network_player_id == network_player_id, MlCapabilityWebhook.active.is_(True))
        .all()
    )
    sent = 0
    for hook in hooks:
        try:
            events = json.loads(hook.event_types_json or "[]")
        except json.JSONDecodeError:
            events = []
        if event_type not in events:
            continue
        ok, http_status, snippet = dispatch_webhook(hook.url, event_type, payload, secret=hook.secret_key)
        now = _utcnow()
        hook.last_http_status = http_status
        hook.last_delivered_at = now if ok else hook.last_delivered_at
        hook.last_error = None if ok else snippet
        db.add(
            MlCapabilityWebhookDelivery(
                id=new_id(),
                webhook_id=hook.id,
                event_type=event_type,
                payload_json=json.dumps(payload),
                http_status=http_status,
                success=ok,
                response_snippet=snippet,
                created_at=now,
            )
        )
        sent += 1
    return sent


def list_ml_capability_webhooks(db: Session, network_player_id: str | None = None) -> list[MlCapabilityWebhook]:
    q = db.query(MlCapabilityWebhook)
    if network_player_id:
        q = q.filter(MlCapabilityWebhook.network_player_id == network_player_id)
    return q.order_by(MlCapabilityWebhook.network_player_code).all()
