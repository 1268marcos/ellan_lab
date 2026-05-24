from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.integration import (
    MoneyCambioApiKey,
    MoneyCambioIntegrationPartner,
    MoneyCambioWebhookEndpoint,
)
from app.schemas.integration import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateOut,
    IntegrationPartnerIn,
    IntegrationPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services.crypto_util import generate_partner_api_key, hash_secret, new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_partners(db: Session, active_only: bool = False) -> list[MoneyCambioIntegrationPartner]:
    q = db.query(MoneyCambioIntegrationPartner)
    if active_only:
        q = q.filter(MoneyCambioIntegrationPartner.active.is_(True))
    return q.order_by(MoneyCambioIntegrationPartner.code).all()


def get_partner_or_404(db: Session, partner_id: str) -> MoneyCambioIntegrationPartner:
    row = db.get(MoneyCambioIntegrationPartner, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="partner_not_found")
    return row


def create_partner(db: Session, body: IntegrationPartnerIn) -> MoneyCambioIntegrationPartner:
    if db.query(MoneyCambioIntegrationPartner).filter(MoneyCambioIntegrationPartner.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="partner_code_exists")
    pid = body.id or new_id()
    data = body.model_dump(exclude={"id"})
    row = MoneyCambioIntegrationPartner(id=pid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_partner(
    db: Session, partner_id: str, body: IntegrationPartnerUpdate
) -> MoneyCambioIntegrationPartner:
    row = get_partner_or_404(db, partner_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_partner(db: Session, partner_id: str) -> None:
    row = get_partner_or_404(db, partner_id)
    db.delete(row)
    db.commit()


def configure_webhook(db: Session, partner_id: str, body: WebhookConfigureIn) -> WebhookOut:
    get_partner_or_404(db, partner_id)
    now = _utcnow()
    secret_raw = body.secret or ""
    secret_hash = hash_secret(secret_raw) if secret_raw else hash_secret("unset")
    events = body.events or ["fx.updated", "money.catalog.changed"]
    events_json = json.dumps(events)
    existing = (
        db.query(MoneyCambioWebhookEndpoint)
        .filter(MoneyCambioWebhookEndpoint.partner_id == partner_id)
        .first()
    )
    if existing:
        existing.url = body.url
        existing.secret_hash = secret_hash
        if secret_raw:
            existing.secret_key = secret_raw
        existing.events_json = events_json
        existing.active = True
        existing.updated_at = now
    else:
        db.add(
            MoneyCambioWebhookEndpoint(
                id=new_id(),
                partner_id=partner_id,
                url=body.url,
                secret_hash=secret_hash,
                secret_key=secret_raw or None,
                events_json=events_json,
            )
        )
    db.commit()
    return WebhookOut(partner_id=partner_id, url=body.url, events=events, active=True)


def get_webhook(db: Session, partner_id: str) -> WebhookOut | None:
    get_partner_or_404(db, partner_id)
    row = (
        db.query(MoneyCambioWebhookEndpoint)
        .filter(MoneyCambioWebhookEndpoint.partner_id == partner_id)
        .first()
    )
    if not row:
        return None
    events = json.loads(row.events_json or "[]")
    return WebhookOut(partner_id=partner_id, url=row.url, events=events, active=row.active)


def rotate_api_key(db: Session, partner_id: str) -> ApiKeyRotateOut:
    partner = get_partner_or_404(db, partner_id)
    api_key, key_prefix, key_hash = generate_partner_api_key(partner_id, partner.code)
    db.add(
        MoneyCambioApiKey(
            id=new_id(),
            partner_id=partner_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            label="rotated",
        )
    )
    db.commit()
    return ApiKeyRotateOut(api_key=api_key, key_prefix=key_prefix, partner_id=partner_id)


def list_api_keys(db: Session, partner_id: str) -> ApiKeyListOut:
    get_partner_or_404(db, partner_id)
    rows = (
        db.query(MoneyCambioApiKey)
        .filter(MoneyCambioApiKey.partner_id == partner_id, MoneyCambioApiKey.revoked_at.is_(None))
        .order_by(MoneyCambioApiKey.created_at.desc())
        .all()
    )
    keys = [
        ApiKeyMetaOut(id=r.id, key_prefix=r.key_prefix, label=r.label, created_at=r.created_at, revoked_at=r.revoked_at)
        for r in rows
    ]
    return ApiKeyListOut(keys=keys)
