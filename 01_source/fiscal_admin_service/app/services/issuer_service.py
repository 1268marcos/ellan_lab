from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.fiscal_admin import FiscalIssuerApiKey, FiscalIssuerPartner, FiscalIssuerWebhookEndpoint
from app.schemas.fiscal import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateOut,
    IssuerIn,
    IssuerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services.crypto_util import generate_issuer_api_key, hash_secret, new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_issuers(db: Session, active_only: bool = False) -> list[FiscalIssuerPartner]:
    q = db.query(FiscalIssuerPartner)
    if active_only:
        q = q.filter(FiscalIssuerPartner.active.is_(True))
    return q.order_by(FiscalIssuerPartner.code).all()


def get_issuer_or_404(db: Session, issuer_id: str) -> FiscalIssuerPartner:
    row = db.get(FiscalIssuerPartner, issuer_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="issuer_not_found")
    return row


def create_issuer(db: Session, body: IssuerIn) -> FiscalIssuerPartner:
    if db.query(FiscalIssuerPartner).filter(FiscalIssuerPartner.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="issuer_code_exists")
    row = FiscalIssuerPartner(id=body.id or new_id(), **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_issuer(db: Session, issuer_id: str, body: IssuerUpdate) -> FiscalIssuerPartner:
    row = get_issuer_or_404(db, issuer_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_issuer(db: Session, issuer_id: str) -> None:
    row = get_issuer_or_404(db, issuer_id)
    db.delete(row)
    db.commit()


def configure_webhook(db: Session, issuer_id: str, body: WebhookConfigureIn) -> WebhookOut:
    get_issuer_or_404(db, issuer_id)
    now = _utcnow()
    secret_raw = body.secret or ""
    secret_hash = hash_secret(secret_raw) if secret_raw else hash_secret("unset")
    events_json = json.dumps(body.events or ["fiscal.document.*", "fiscal.callback.*"])
    existing = (
        db.query(FiscalIssuerWebhookEndpoint).filter(FiscalIssuerWebhookEndpoint.issuer_id == issuer_id).first()
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
        row = FiscalIssuerWebhookEndpoint(
            id=new_id(),
            issuer_id=issuer_id,
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


def get_webhook(db: Session, issuer_id: str) -> WebhookOut | None:
    row = db.query(FiscalIssuerWebhookEndpoint).filter(FiscalIssuerWebhookEndpoint.issuer_id == issuer_id).first()
    return WebhookOut.model_validate(row) if row else None


def rotate_api_key(db: Session, issuer_id: str) -> ApiKeyRotateOut:
    issuer = get_issuer_or_404(db, issuer_id)
    now = _utcnow()
    db.query(FiscalIssuerApiKey).filter(
        FiscalIssuerApiKey.issuer_id == issuer_id,
        FiscalIssuerApiKey.revoked_at.is_(None),
    ).update({"revoked_at": now})
    api_key, prefix, key_hash = generate_issuer_api_key(issuer_id, issuer.code)
    db.add(
        FiscalIssuerApiKey(
            id=new_id(),
            issuer_id=issuer_id,
            key_prefix=prefix,
            key_hash=key_hash,
            label="rotated",
            created_at=now,
        )
    )
    db.commit()
    return ApiKeyRotateOut(issuer_id=issuer_id, api_key=api_key, key_prefix=prefix, created_at=now)


def list_api_keys(db: Session, issuer_id: str) -> ApiKeyListOut:
    get_issuer_or_404(db, issuer_id)
    rows = (
        db.query(FiscalIssuerApiKey)
        .filter(FiscalIssuerApiKey.issuer_id == issuer_id)
        .order_by(FiscalIssuerApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListOut(
        issuer_id=issuer_id,
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
