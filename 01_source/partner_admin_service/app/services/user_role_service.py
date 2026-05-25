from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.schemas.user_role import UserListOut, UserOut, UserRoleCreateIn, UserRoleOut, UserRoleUpdateIn
from app.services.critical_table_security_service import enforce
from app.services.crypto_util import new_id
from shared.security.critical_table_guard import ActorContext


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_users(db: Session, *, actor: ActorContext | None = None) -> UserListOut:
    ctx = actor or ActorContext(roles=["admin_operacao"])
    enforce(db, table_name="users", operation="SELECT", actor=ctx)
    rows = db.query(User).order_by(User.full_name).all()
    return UserListOut(users=[UserOut.model_validate(r) for r in rows], total=len(rows))


def get_user_or_404(db: Session, user_id: str, *, actor: ActorContext | None = None) -> User:
    ctx = actor or ActorContext(actor_id=user_id, roles=["admin_operacao"])
    enforce(
        db,
        table_name="users",
        operation="SELECT",
        actor=ctx,
        target_user_id=user_id,
        row_id=user_id,
    )
    row = db.get(User, user_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_not_found")
    return row


def list_user_roles(db: Session, *, user_id: str | None = None, active_only: bool = True) -> list[UserRoleOut]:
    q = db.query(UserRole)
    if user_id:
        q = q.filter(UserRole.user_id == user_id)
    if active_only:
        q = q.filter(UserRole.is_active.is_(True), UserRole.revoked_at.is_(None))
    rows = q.order_by(UserRole.granted_at.desc()).all()
    return [UserRoleOut.model_validate(r) for r in rows]


def get_role_or_404(db: Session, role_id: str) -> UserRole:
    row = db.get(UserRole, role_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user_role_not_found")
    return row


def create_user_role(db: Session, body: UserRoleCreateIn) -> UserRoleOut:
    get_user_or_404(db, body.user_id)
    existing = (
        db.query(UserRole)
        .filter(
            UserRole.user_id == body.user_id,
            UserRole.role == body.role,
            UserRole.scope_type == body.scope_type,
            UserRole.scope_id == body.scope_id,
            UserRole.revoked_at.is_(None),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="active_role_exists")
    now = _utcnow()
    row = UserRole(
        id=new_id(),
        user_id=body.user_id,
        role=body.role,
        scope_type=body.scope_type,
        scope_id=body.scope_id,
        is_active=True,
        granted_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return UserRoleOut.model_validate(row)


def update_user_role(db: Session, role_id: str, body: UserRoleUpdateIn) -> UserRoleOut:
    row = get_role_or_404(db, role_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return UserRoleOut.model_validate(row)


def revoke_user_role(db: Session, role_id: str) -> UserRoleOut:
    row = get_role_or_404(db, role_id)
    now = _utcnow()
    row.is_active = False
    row.revoked_at = now
    db.commit()
    db.refresh(row)
    return UserRoleOut.model_validate(row)


def delete_user_role(db: Session, role_id: str) -> None:
    row = get_role_or_404(db, role_id)
    db.delete(row)
    db.commit()
