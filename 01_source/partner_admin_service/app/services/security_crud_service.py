from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.security import (
    SecurityPermission,
    SecurityPermissionGroup,
    SecurityPermissionMembership,
    SecurityRoleCatalog,
    SecurityWebhookEndpoint,
)
from app.models.user import User, UserRole
from app.schemas.security import (
    PermissionCreateIn,
    PermissionGroupCreateIn,
    PermissionGroupListOut,
    PermissionGroupOut,
    PermissionListOut,
    PermissionOut,
    UserCreateIn,
    UserUpdateIn,
    WebhookEndpointCreateIn,
    WebhookEndpointListOut,
)
from app.schemas.security_crud import (
    PermissionGroupUpdateIn,
    PermissionMatrixOut,
    PermissionMatrixRow,
    PermissionUpdateIn,
    SecuritySeedOut,
    WebhookConfigIn,
    WebhookConfigOut,
)
from app.schemas.user_role import UserListOut, UserOut, UserRoleCreateIn, UserRoleListOut, UserRoleOut, UserRoleUpdateIn
from app.services import security_service, user_crud_service, user_role_service
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_users(db: Session) -> UserListOut:
    return user_role_service.list_users(db)


def get_user(db: Session, user_id: str) -> UserOut:
    row = user_role_service.get_user_or_404(db, user_id)
    return UserOut.model_validate(row)


def create_user(db: Session, body: UserCreateIn) -> UserOut:
    return user_crud_service.create_user(db, body)


def update_user(db: Session, user_id: str, body: UserUpdateIn) -> UserOut:
    return user_crud_service.update_user(db, user_id, body)


def delete_user(db: Session, user_id: str) -> None:
    user_crud_service.delete_user(db, user_id)


def list_roles(db: Session, *, user_id: str | None = None, active_only: bool = False) -> UserRoleListOut:
    roles = user_role_service.list_user_roles(db, user_id=user_id, active_only=active_only)
    return UserRoleListOut(roles=roles, total=len(roles))


def get_role(db: Session, role_id: str) -> UserRoleOut:
    return UserRoleOut.model_validate(user_role_service.get_role_or_404(db, role_id))


def create_role(db: Session, body: UserRoleCreateIn) -> UserRoleOut:
    return user_role_service.create_user_role(db, body)


def update_role(db: Session, role_id: str, body: UserRoleUpdateIn) -> UserRoleOut:
    return user_role_service.update_user_role(db, role_id, body)


def delete_role(db: Session, role_id: str) -> None:
    user_role_service.delete_user_role(db, role_id)


def list_permission_groups(db: Session) -> PermissionGroupListOut:
    return security_service.list_permission_groups(db)


def get_permission_group(db: Session, group_id: str) -> PermissionGroupOut:
    row = db.get(SecurityPermissionGroup, group_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="group_not_found")
    return PermissionGroupOut.model_validate(row)


def create_permission_group(db: Session, body: PermissionGroupCreateIn) -> PermissionGroupOut:
    return security_service.create_permission_group(db, body)


def update_permission_group(db: Session, group_id: str, body: PermissionGroupUpdateIn) -> PermissionGroupOut:
    row = db.get(SecurityPermissionGroup, group_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="group_not_found")
    if row.is_system and body.name is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="system_group_immutable")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return PermissionGroupOut.model_validate(row)


def delete_permission_group(db: Session, group_id: str) -> None:
    row = db.get(SecurityPermissionGroup, group_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="group_not_found")
    if row.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="system_group_immutable")
    db.query(SecurityPermission).filter(SecurityPermission.group_id == group_id).delete()
    db.query(SecurityPermissionMembership).filter(SecurityPermissionMembership.group_id == group_id).delete()
    db.delete(row)
    db.commit()


def list_permissions(db: Session, *, group_id: str | None = None) -> PermissionListOut:
    return security_service.list_permissions(db, group_id)


def get_permission(db: Session, permission_id: str) -> PermissionOut:
    row = db.get(SecurityPermission, permission_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission_not_found")
    return PermissionOut.model_validate(row)


def create_permission(db: Session, body: PermissionCreateIn) -> PermissionOut:
    return security_service.create_permission(db, body)


def update_permission(db: Session, permission_id: str, body: PermissionUpdateIn) -> PermissionOut:
    row = db.get(SecurityPermission, permission_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission_not_found")
    if body.group_id is not None:
        if not db.get(SecurityPermissionGroup, body.group_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="group_not_found")
        row.group_id = body.group_id
    if body.object_key is not None:
        row.object_key = body.object_key
    db.commit()
    db.refresh(row)
    return PermissionOut.model_validate(row)


def delete_permission(db: Session, permission_id: str) -> None:
    row = db.get(SecurityPermission, permission_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission_not_found")
    db.delete(row)
    db.commit()


def permission_matrix(db: Session) -> PermissionMatrixOut:
    groups = db.query(SecurityPermissionGroup).order_by(SecurityPermissionGroup.name).all()
    rows: list[PermissionMatrixRow] = []
    total = 0
    for g in groups:
        perms = (
            db.query(SecurityPermission)
            .filter(SecurityPermission.group_id == g.id)
            .order_by(SecurityPermission.object_key)
            .all()
        )
        members = (
            db.query(SecurityPermissionMembership.user_id)
            .filter(SecurityPermissionMembership.group_id == g.id)
            .distinct()
            .all()
        )
        total += len(perms)
        rows.append(
            PermissionMatrixRow(
                group_id=g.id,
                group_name=g.name,
                permissions=[PermissionOut.model_validate(p) for p in perms],
                member_user_ids=[m[0] for m in members],
            )
        )
    return PermissionMatrixOut(groups=rows, total_permissions=total)


def list_webhooks(db: Session) -> WebhookEndpointListOut:
    return security_service.list_webhooks(db)


def configure_webhook(db: Session, body: WebhookConfigIn) -> WebhookConfigOut:
    if body.id:
        row = db.get(SecurityWebhookEndpoint, body.id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
        row.url = body.url
        row.owner_type = body.owner_type
        row.owner_id = body.owner_id
        row.signing_algo = body.signing_algo
        row.active = body.active
        row.updated_at = _utcnow()
        row.events_json = json.dumps(body.events)
        db.commit()
        db.refresh(row)
        from app.services.security_service import _webhook_out

        return WebhookConfigOut(endpoint=_webhook_out(row))
    create_in = WebhookEndpointCreateIn(
        url=body.url,
        owner_type=body.owner_type,
        owner_id=body.owner_id,
        events=body.events,
        signing_algo=body.signing_algo,
        active=body.active,
    )
    endpoint, secret = security_service.create_webhook(db, create_in)
    return WebhookConfigOut(endpoint=endpoint, webhook_secret=secret)


def seed_security_baseline(db: Session) -> SecuritySeedOut:
    now = _utcnow()
    counts = SecuritySeedOut(
        users=0,
        user_roles=0,
        permission_groups=0,
        permissions=0,
        memberships=0,
        role_catalog=0,
    )

    if not db.get(User, "usr-admin"):
        db.add(
            User(
                id="usr-admin",
                full_name="Admin",
                email="admin@ellanlab.com",
                password_hash="!",
                is_active=True,
                email_verified=True,
                phone_verified=False,
                created_at=now,
                updated_at=now,
            )
        )
        counts.users += 1

    catalog_roles = [
        ("admin", "Administrador", "Acesso total plataforma"),
        ("ops", "Operações", "Lockers runtime e OPS"),
        ("finance", "Financeiro", "Billing settlements e fiscal"),
        ("support", "Suporte", "Atendimento e auditoria leitura"),
        ("partner", "Parceiro", "Integrações B2B e webhooks"),
    ]
    for code, label, desc in catalog_roles:
        if not db.get(SecurityRoleCatalog, code):
            db.add(
                SecurityRoleCatalog(
                    code=code,
                    label=label,
                    description=desc,
                    default_scope_type="GLOBAL",
                    allowed_domains_json='["PARTNER","OPS","PAYMENT"]',
                    is_system=True,
                    sort_order=10,
                    created_at=now,
                )
            )
            counts.role_catalog += 1

    role_bindings = [
        ("usr-admin", "admin"),
        ("usr-admin-ops", "ops"),
        ("usr-suporte", "support"),
        ("usr-auditoria", "finance"),
    ]
    for user_id, role in role_bindings:
        if not db.get(User, user_id):
            continue
        exists = (
            db.query(UserRole)
            .filter(
                UserRole.user_id == user_id,
                UserRole.role == role,
                UserRole.revoked_at.is_(None),
            )
            .first()
        )
        if not exists:
            db.add(
                UserRole(
                    id=new_id(),
                    user_id=user_id,
                    role=role,
                    scope_type="GLOBAL",
                    is_active=True,
                    granted_at=now,
                )
            )
            counts.user_roles += 1

    sec_counts = security_service.seed_security_domain(db)
    counts.permission_groups = sec_counts.get("permission_groups", 0)
    counts.permissions = sec_counts.get("permissions", 0)
    counts.memberships = sec_counts.get("memberships", 0)

    admin_membership = (
        db.query(SecurityPermissionMembership)
        .filter(
            SecurityPermissionMembership.user_id == "usr-admin",
            SecurityPermissionMembership.group_id == "grp-ops-full",
        )
        .first()
    )
    if not admin_membership and db.get(User, "usr-admin"):
        db.add(
            SecurityPermissionMembership(
                id=new_id(),
                user_id="usr-admin",
                group_id="grp-ops-full",
                is_group_manager=True,
                created_at=now,
            )
        )
        counts.memberships += 1

    db.commit()
    return counts
