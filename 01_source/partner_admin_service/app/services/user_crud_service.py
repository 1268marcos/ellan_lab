from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.security import UserCreateIn, UserUpdateIn
from app.schemas.user_role import UserOut
from app.services.crypto_util import new_id
from app.services.security_service import write_audit


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_user(db: Session, body: UserCreateIn, *, actor_id: str | None = None) -> UserOut:
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email_exists")
    now = _utcnow()
    row = User(
        id=new_id(),
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        password_hash="!",
        is_active=body.is_active,
        email_verified=body.email_verified,
        phone_verified=False,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=actor_id,
        action="USER_CREATED",
        target_type="User",
        target_id=row.id,
        new_state={"email": row.email, "full_name": row.full_name},
    )
    return UserOut.model_validate(row)


def update_user(db: Session, user_id: str, body: UserUpdateIn, *, actor_id: str | None = None) -> UserOut:
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    old = {"email": row.email, "is_active": row.is_active}
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    write_audit(
        db,
        actor_id=actor_id,
        action="USER_UPDATED",
        target_type="User",
        target_id=row.id,
        old_state=old,
        new_state={"email": row.email, "is_active": row.is_active},
    )
    return UserOut.model_validate(row)


def deactivate_user(db: Session, user_id: str, *, actor_id: str | None = None) -> UserOut:
    return update_user(db, user_id, UserUpdateIn(is_active=False), actor_id=actor_id)


def delete_user(db: Session, user_id: str, *, actor_id: str | None = None) -> None:
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    db.delete(row)
    db.commit()
    write_audit(
        db,
        actor_id=actor_id,
        action="USER_DELETED",
        target_type="User",
        target_id=user_id,
    )
