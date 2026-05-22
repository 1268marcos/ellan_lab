from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.api_key import SellerApiKey
from app.schemas.api_key import ApiKeyListOut, ApiKeyMetaOut, ApiKeyRotateOut
from app.services.crypto_util import generate_seller_api_key, new_id
from app.services.seller_service import get_seller_or_404


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def rotate_api_key(db: Session, seller_id: str) -> ApiKeyRotateOut:
    get_seller_or_404(db, seller_id)
    now = _utcnow()
    db.query(SellerApiKey).filter(
        SellerApiKey.seller_id == seller_id,
        SellerApiKey.revoked_at.is_(None),
    ).update({"revoked_at": now})
    api_key, prefix, key_hash = generate_seller_api_key(seller_id)
    row = SellerApiKey(
        id=new_id(),
        seller_id=seller_id,
        key_prefix=prefix,
        key_hash=key_hash,
        label="rotated",
        created_at=now,
    )
    db.add(row)
    db.commit()
    return ApiKeyRotateOut(seller_id=seller_id, api_key=api_key, key_prefix=prefix, created_at=now)


def list_api_keys(db: Session, seller_id: str) -> ApiKeyListOut:
    get_seller_or_404(db, seller_id)
    rows = (
        db.query(SellerApiKey)
        .filter(SellerApiKey.seller_id == seller_id)
        .order_by(SellerApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListOut(
        seller_id=seller_id,
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
