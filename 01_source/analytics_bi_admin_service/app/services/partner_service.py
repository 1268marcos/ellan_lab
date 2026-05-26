from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.bi_partners import BiApiKeyRotationLog, BiDataPartner, BiPartnerApiKey, BiPartnerWebhookEndpoint
from app.schemas.partner import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateOut,
    BiDataPartnerIn,
    BiDataPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services.crypto_util import generate_bi_api_key, hash_secret, new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_partners(db: Session, active_only: bool = False) -> list[BiDataPartner]:
    q = db.query(BiDataPartner)
    if active_only:
        q = q.filter(BiDataPartner.active.is_(True))
    return q.order_by(BiDataPartner.code).all()


def get_partner_or_404(db: Session, partner_id: str) -> BiDataPartner:
    row = db.get(BiDataPartner, partner_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="partner_not_found")
    return row


def create_partner(db: Session, body: BiDataPartnerIn) -> BiDataPartner:
    if db.query(BiDataPartner).filter(BiDataPartner.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="partner_code_exists")
    pid = body.id or new_id()
    row = BiDataPartner(id=pid, **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_partner(db: Session, partner_id: str, body: BiDataPartnerUpdate) -> BiDataPartner:
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
    events_json = json.dumps(body.events or ["fact.ingested", "mart.refreshed"])
    existing = (
        db.query(BiPartnerWebhookEndpoint).filter(BiPartnerWebhookEndpoint.partner_id == partner_id).first()
    )
    if existing:
        existing.url = body.url
        existing.secret_hash = secret_hash
        if secret_raw:
            existing.secret_key = secret_raw
        existing.events_json = events_json
        existing.active = True
        existing.updated_at = now
        row = existing
    else:
        row = BiPartnerWebhookEndpoint(
            id=new_id(),
            partner_id=partner_id,
            url=body.url,
            secret_hash=secret_hash,
            secret_key=secret_raw or None,
            events_json=events_json,
        )
        db.add(row)
    db.commit()
    return WebhookOut(
        partner_id=partner_id,
        url=row.url,
        events=json.loads(row.events_json),
        active=row.active,
    )


def get_webhook(db: Session, partner_id: str) -> WebhookOut | None:
    row = db.query(BiPartnerWebhookEndpoint).filter(BiPartnerWebhookEndpoint.partner_id == partner_id).first()
    if not row:
        return None
    return WebhookOut(
        partner_id=partner_id,
        url=row.url,
        events=json.loads(row.events_json),
        active=row.active,
    )


def rotate_api_key(db: Session, partner_id: str, rotated_by: str | None = None) -> ApiKeyRotateOut:
    partner = get_partner_or_404(db, partner_id)
    now = _utcnow()
    old = (
        db.query(BiPartnerApiKey)
        .filter(BiPartnerApiKey.partner_id == partner_id, BiPartnerApiKey.revoked_at.is_(None))
        .order_by(BiPartnerApiKey.created_at.desc())
        .first()
    )
    old_prefix = old.key_prefix if old else None
    if old:
        old.revoked_at = now
    api_key, key_prefix, key_hash = generate_bi_api_key(partner_id, partner.code)
    db.add(
        BiPartnerApiKey(
            id=new_id(),
            partner_id=partner_id,
            key_prefix=key_prefix,
            key_hash=key_hash,
            label="rotated",
            created_by=rotated_by,
        )
    )
    db.add(
        BiApiKeyRotationLog(
            id=new_id(),
            partner_id=partner_id,
            old_key_prefix=old_prefix,
            new_key_prefix=key_prefix,
            rotated_by=rotated_by,
        )
    )
    db.commit()
    return ApiKeyRotateOut(api_key=api_key, key_prefix=key_prefix, partner_id=partner_id)


def list_api_keys(db: Session, partner_id: str) -> ApiKeyListOut:
    get_partner_or_404(db, partner_id)
    rows = (
        db.query(BiPartnerApiKey)
        .filter(BiPartnerApiKey.partner_id == partner_id)
        .order_by(BiPartnerApiKey.created_at.desc())
        .all()
    )
    keys = [
        ApiKeyMetaOut(
            id=r.id,
            key_prefix=r.key_prefix,
            label=r.label,
            scopes=json.loads(r.scopes_json),
            created_at=r.created_at,
            revoked_at=r.revoked_at,
        )
        for r in rows
    ]
    return ApiKeyListOut(keys=keys)
