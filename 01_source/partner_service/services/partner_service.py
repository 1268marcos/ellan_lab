from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models import Partner, PartnerApiKey
from schemas import PartnerCreateIn, PartnerUpdateIn, PartnerWebhookPatchIn


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _hash_secret(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_partner(db: Session, payload: PartnerCreateIn) -> Partner:
    now = _utcnow()
    partner = Partner(
        id=str(uuid.uuid4()),
        partner_type=payload.partner_type,
        name=payload.name,
        legal_name=payload.legal_name,
        status=payload.status,
        contact_email=str(payload.contact_email) if payload.contact_email else None,
        created_at=now,
        updated_at=now,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def get_partner(db: Session, partner_id: str) -> Partner:
    row = db.query(Partner).filter(Partner.id == partner_id).first()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Partner not found")
    return row


def list_partners(db: Session, skip: int = 0, limit: int = 50) -> list[Partner]:
    return (
        db.query(Partner)
        .order_by(Partner.created_at.desc())
        .offset(skip)
        .limit(min(limit, 200))
        .all()
    )


def update_partner(db: Session, partner_id: str, payload: PartnerUpdateIn) -> Partner:
    partner = get_partner(db, partner_id)
    if payload.name is not None:
        partner.name = payload.name
    if payload.legal_name is not None:
        partner.legal_name = payload.legal_name
    if payload.contact_email is not None:
        partner.contact_email = str(payload.contact_email)
    if payload.status is not None:
        partner.status = payload.status
    partner.updated_at = _utcnow()
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def delete_partner(db: Session, partner_id: str) -> None:
    partner = get_partner(db, partner_id)
    db.delete(partner)
    db.commit()


def update_webhook(db: Session, partner_id: str, payload: PartnerWebhookPatchIn) -> Partner:
    partner = get_partner(db, partner_id)
    if payload.webhook_url is not None:
        partner.webhook_url = payload.webhook_url
    if payload.webhook_secret is not None:
        partner.webhook_secret_hash = _hash_secret(payload.webhook_secret)
    if payload.webhook_events_json is not None:
        try:
            json.loads(payload.webhook_events_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail="webhook_events_json must be valid JSON") from exc
        partner.webhook_events_json = payload.webhook_events_json
    if payload.webhook_api_version is not None:
        partner.webhook_api_version = payload.webhook_api_version
    partner.updated_at = _utcnow()
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def rotate_api_key(db: Session, partner_id: str, label: str | None) -> tuple[str, PartnerApiKey]:
    partner = get_partner(db, partner_id)
    now = _utcnow()
    for key in (
        db.query(PartnerApiKey)
        .filter(PartnerApiKey.partner_id == partner.id, PartnerApiKey.revoked_at.is_(None))
        .all()
    ):
        key.revoked_at = now
        db.add(key)
    raw = secrets.token_urlsafe(32)
    prefix = raw[:8]
    row = PartnerApiKey(
        id=str(uuid.uuid4()),
        partner_id=partner.id,
        partner_type=partner.partner_type,
        key_prefix=prefix,
        key_hash=_hash_secret(raw),
        label=label,
        scopes_json="[]",
        created_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return raw, row
