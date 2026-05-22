from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.api_key import PartnerApiKey
from app.schemas.api_key import ApiKeyListOut, ApiKeyMetaOut, ApiKeyRotateOut
from app.services.crypto_util import generate_partner_api_key, new_id
from app.services.partner_service import get_ecommerce_or_404, get_logistics_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _resolve_partner(db: Session, partner_id: str, partner_type: str) -> str:
    pt = partner_type.upper()
    if pt == "ECOMMERCE":
        get_ecommerce_or_404(db, partner_id)
    else:
        get_logistics_or_404(db, partner_id)
    return pt


def rotate_api_key(db: Session, partner_id: str, partner_type: str) -> ApiKeyRotateOut:
    pt = _resolve_partner(db, partner_id, partner_type)
    now = _utcnow()
    db.query(PartnerApiKey).filter(
        PartnerApiKey.partner_id == partner_id,
        PartnerApiKey.partner_type == pt,
        PartnerApiKey.revoked_at.is_(None),
    ).update({"revoked_at": now})
    api_key, prefix, key_hash = generate_partner_api_key(partner_id, pt)
    row = PartnerApiKey(
        id=new_id(),
        partner_id=partner_id,
        partner_type=pt,
        key_prefix=prefix,
        key_hash=key_hash,
        label="rotated",
        created_at=now,
    )
    db.add(row)
    db.commit()
    return ApiKeyRotateOut(
        partner_id=partner_id,
        partner_type=pt,
        api_key=api_key,
        key_prefix=prefix,
        created_at=now,
    )


def list_api_keys(db: Session, partner_id: str, partner_type: str) -> ApiKeyListOut:
    pt = _resolve_partner(db, partner_id, partner_type)
    rows = (
        db.query(PartnerApiKey)
        .filter(PartnerApiKey.partner_id == partner_id, PartnerApiKey.partner_type == pt)
        .order_by(PartnerApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListOut(
        partner_id=partner_id,
        partner_type=pt,
        keys=[
            ApiKeyMetaOut(
                id=row.id,
                key_prefix=row.key_prefix,
                label=row.label,
                revoked_at=row.revoked_at,
                created_at=row.created_at,
            )
            for row in rows
        ],
    )
