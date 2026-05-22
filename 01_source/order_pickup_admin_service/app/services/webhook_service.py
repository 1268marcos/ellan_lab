from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.webhook import PartnerWebhookEndpoint
from app.schemas.webhook import WebhookConfigureIn, WebhookOut
from app.services.crypto_util import hash_secret, new_id
from app.services.partner_service import get_ecommerce_or_404, get_logistics_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_partner(db: Session, partner_id: str, partner_type: str):
    pt = partner_type.upper()
    if pt == "ECOMMERCE":
        get_ecommerce_or_404(db, partner_id)
    else:
        get_logistics_or_404(db, partner_id)
    return pt


def configure_webhook(
    db: Session,
    partner_id: str,
    partner_type: str,
    body: WebhookConfigureIn,
) -> WebhookOut:
    pt = _resolve_partner(db, partner_id, partner_type)
    secret = body.secret or ""
    secret_hash = hash_secret(secret) if secret else hash_secret(partner_id)
    events_json = json.dumps(body.events)
    now = _utcnow()
    row = (
        db.query(PartnerWebhookEndpoint)
        .filter(PartnerWebhookEndpoint.partner_id == partner_id, PartnerWebhookEndpoint.partner_type == pt)
        .first()
    )
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
        row = PartnerWebhookEndpoint(
            id=new_id(),
            partner_id=partner_id,
            partner_type=pt,
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


def get_webhook(db: Session, partner_id: str, partner_type: str) -> WebhookOut | None:
    pt = partner_type.upper()
    row = (
        db.query(PartnerWebhookEndpoint)
        .filter(PartnerWebhookEndpoint.partner_id == partner_id, PartnerWebhookEndpoint.partner_type == pt)
        .first()
    )
    return WebhookOut.model_validate(row) if row else None
