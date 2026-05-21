from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.api_key import LockerApiKey
from app.schemas.api_key import ApiKeyListOut, ApiKeyMetaOut, ApiKeyRotateOut
from app.services.crypto_util import generate_api_key
from app.services.locker_service import get_locker_or_404


def rotate_api_key(db: Session, locker_id: str) -> ApiKeyRotateOut:
    get_locker_or_404(db, locker_id)
    now = datetime.now(timezone.utc)
    db.query(LockerApiKey).filter(LockerApiKey.locker_id == locker_id, LockerApiKey.active.is_(True)).update(
        {"active": False, "rotated_at": now}
    )
    api_key, prefix, key_hash = generate_api_key(locker_id)
    row = LockerApiKey(
        locker_id=locker_id,
        key_prefix=prefix,
        key_hash=key_hash,
        active=True,
        created_at=now,
        rotated_at=now,
    )
    db.add(row)
    db.commit()
    return ApiKeyRotateOut(locker_id=locker_id, api_key=api_key, key_prefix=prefix, rotated_at=now)


def list_api_keys(db: Session, locker_id: str) -> ApiKeyListOut:
    get_locker_or_404(db, locker_id)
    rows = (
        db.query(LockerApiKey)
        .filter(LockerApiKey.locker_id == locker_id)
        .order_by(LockerApiKey.created_at.desc())
        .all()
    )
    return ApiKeyListOut(
        locker_id=locker_id,
        keys=[
            ApiKeyMetaOut(
                id=row.id,
                key_prefix=row.key_prefix,
                active=row.active,
                created_at=row.created_at,
                rotated_at=row.rotated_at,
            )
            for row in rows
        ],
    )
