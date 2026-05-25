from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.vendor import HardwareVendorApiKey, HardwareVendorPartner, HardwareVendorWebhookEndpoint
from app.schemas.vendor import (
    ApiKeyListOut,
    ApiKeyMetaOut,
    ApiKeyRotateOut,
    HardwareVendorPartnerIn,
    HardwareVendorPartnerUpdate,
    WebhookConfigureIn,
    WebhookOut,
)
from app.services.crypto_util import generate_vendor_api_key, hash_secret, new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_vendors(db: Session, active_only: bool = False) -> list[HardwareVendorPartner]:
    q = db.query(HardwareVendorPartner)
    if active_only:
        q = q.filter(HardwareVendorPartner.active.is_(True))
    return q.order_by(HardwareVendorPartner.code).all()


def get_vendor_or_404(db: Session, vendor_id: str) -> HardwareVendorPartner:
    row = db.get(HardwareVendorPartner, vendor_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="vendor_not_found")
    return row


def create_vendor(db: Session, body: HardwareVendorPartnerIn) -> HardwareVendorPartner:
    if db.query(HardwareVendorPartner).filter(HardwareVendorPartner.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="vendor_code_exists")
    vid = body.id or new_id()
    data = body.model_dump(exclude={"id"})
    row = HardwareVendorPartner(id=vid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_vendor(db: Session, vendor_id: str, body: HardwareVendorPartnerUpdate) -> HardwareVendorPartner:
    row = get_vendor_or_404(db, vendor_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_vendor(db: Session, vendor_id: str) -> None:
    row = get_vendor_or_404(db, vendor_id)
    db.delete(row)
    db.commit()


def configure_webhook(db: Session, vendor_id: str, body: WebhookConfigureIn) -> WebhookOut:
    get_vendor_or_404(db, vendor_id)
    now = _utcnow()
    secret_raw = body.secret or ""
    secret_hash = hash_secret(secret_raw) if secret_raw else hash_secret("unset")
    events = body.events or ["locker.*", "telemetry.*"]
    events_json = json.dumps(events)
    existing = (
        db.query(HardwareVendorWebhookEndpoint)
        .filter(HardwareVendorWebhookEndpoint.vendor_id == vendor_id)
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
        row = HardwareVendorWebhookEndpoint(
            id=new_id(),
            vendor_id=vendor_id,
            url=body.url,
            secret_hash=secret_hash,
            secret_key=secret_raw or None,
            events_json=events_json,
            retry_policy="{}",
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    db.commit()
    db.refresh(row)
    return WebhookOut.model_validate(row)


def get_webhook(db: Session, vendor_id: str) -> WebhookOut | None:
    row = (
        db.query(HardwareVendorWebhookEndpoint)
        .filter(HardwareVendorWebhookEndpoint.vendor_id == vendor_id)
        .first()
    )
    return WebhookOut.model_validate(row) if row else None


def rotate_api_key(db: Session, vendor_id: str) -> ApiKeyRotateOut:
    vendor = get_vendor_or_404(db, vendor_id)
    now = _utcnow()
    db.query(HardwareVendorApiKey).filter(
        HardwareVendorApiKey.vendor_id == vendor_id,
        HardwareVendorApiKey.revoked_at.is_(None),
    ).update({"revoked_at": now})
    api_key, prefix, key_hash = generate_vendor_api_key(vendor_id, vendor.code)
    db.add(
        HardwareVendorApiKey(
            id=new_id(),
            vendor_id=vendor_id,
            key_prefix=prefix,
            key_hash=key_hash,
            label="rotated",
            created_at=now,
        )
    )
    db.commit()
    return ApiKeyRotateOut(vendor_id=vendor_id, api_key=api_key, key_prefix=prefix, created_at=now)


def list_api_keys(db: Session, vendor_id: str) -> ApiKeyListOut:
    get_vendor_or_404(db, vendor_id)
    rows = (
        db.query(HardwareVendorApiKey)
        .filter(HardwareVendorApiKey.vendor_id == vendor_id)
        .order_by(HardwareVendorApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListOut(
        vendor_id=vendor_id,
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
