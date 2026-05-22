from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.provider import (
    PaymentProviderApiKey,
    PaymentProviderPartner,
    PaymentProviderWebhookEndpoint,
)
from app.schemas.provider import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateOut,
    PaymentProviderPartnerIn,
    PaymentProviderPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services.crypto_util import (
    generate_provider_api_key,
    hash_secret,
    new_id,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_providers(db: Session, active_only: bool = False) -> list[PaymentProviderPartner]:
    q = db.query(PaymentProviderPartner)
    if active_only:
        q = q.filter(PaymentProviderPartner.active.is_(True))
    return q.order_by(PaymentProviderPartner.code).all()


def get_provider_or_404(db: Session, provider_id: str) -> PaymentProviderPartner:
    row = db.get(PaymentProviderPartner, provider_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="provider_not_found")
    return row


def create_provider(db: Session, body: PaymentProviderPartnerIn) -> PaymentProviderPartner:
    if db.query(PaymentProviderPartner).filter(PaymentProviderPartner.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="provider_code_exists")
    pid = body.id or new_id()
    data = body.model_dump(exclude={"id"})
    row = PaymentProviderPartner(id=pid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_provider(
    db: Session, provider_id: str, body: PaymentProviderPartnerUpdate
) -> PaymentProviderPartner:
    row = get_provider_or_404(db, provider_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_provider(db: Session, provider_id: str) -> None:
    row = get_provider_or_404(db, provider_id)
    db.delete(row)
    db.commit()


def configure_webhook(db: Session, provider_id: str, body: WebhookConfigureIn) -> WebhookOut:
    get_provider_or_404(db, provider_id)
    now = _utcnow()
    secret_raw = body.secret or ""
    secret_hash = hash_secret(secret_raw) if secret_raw else hash_secret("unset")
    events = body.events or ["payment.*"]
    events_json = json.dumps(events)
    existing = (
        db.query(PaymentProviderWebhookEndpoint)
        .filter(PaymentProviderWebhookEndpoint.provider_id == provider_id)
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
        row = existing
    else:
        row = PaymentProviderWebhookEndpoint(
            id=new_id(),
            provider_id=provider_id,
            url=body.url,
            secret_hash=secret_hash,
            secret_key=secret_raw or None,
            events_json=events_json,
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return WebhookOut.model_validate(row)


def get_webhook(db: Session, provider_id: str) -> WebhookOut | None:
    row = (
        db.query(PaymentProviderWebhookEndpoint)
        .filter(PaymentProviderWebhookEndpoint.provider_id == provider_id)
        .first()
    )
    return WebhookOut.model_validate(row) if row else None


def rotate_api_key(db: Session, provider_id: str) -> ApiKeyRotateOut:
    provider = get_provider_or_404(db, provider_id)
    now = _utcnow()
    db.query(PaymentProviderApiKey).filter(
        PaymentProviderApiKey.provider_id == provider_id,
        PaymentProviderApiKey.revoked_at.is_(None),
    ).update({"revoked_at": now})
    api_key, prefix, key_hash = generate_provider_api_key(provider_id, provider.code)
    db.add(
        PaymentProviderApiKey(
            id=new_id(),
            provider_id=provider_id,
            key_prefix=prefix,
            key_hash=key_hash,
            label="rotated",
            created_at=now,
        )
    )
    db.commit()
    return ApiKeyRotateOut(provider_id=provider_id, api_key=api_key, key_prefix=prefix, created_at=now)


def list_api_keys(db: Session, provider_id: str) -> ApiKeyListOut:
    get_provider_or_404(db, provider_id)
    rows = (
        db.query(PaymentProviderApiKey)
        .filter(PaymentProviderApiKey.provider_id == provider_id)
        .order_by(PaymentProviderApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListOut(
        provider_id=provider_id,
        keys=[
            ApiKeyMetaOut(
                id=r.id,
                key_prefix=r.key_prefix,
                label=r.label,
                revoked_at=r.revoked_at,
                created_at=r.created_at,
            )
            for r in rows
        ],
    )
