from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Optional, TypeVar

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.security import ApiKeyListOut, ApiKeyRotateIn, ApiKeyRotateOut, PermissionCreateIn, PermissionGroupCreateIn
from app.schemas.security_crud import (
    PermissionGroupUpdateIn,
    PermissionMatrixOut,
    PermissionUpdateIn,
    SecuritySeedOut,
    WebhookConfigIn,
    WebhookConfigOut,
)
from app.schemas.security import (
    PermissionGroupListOut,
    PermissionGroupOut,
    PermissionListOut,
    PermissionOut,
    UserCreateIn,
    UserUpdateIn,
    WebhookEndpointListOut,
)
from app.schemas.user_role import UserListOut, UserOut, UserRoleCreateIn, UserRoleListOut, UserRoleOut, UserRoleUpdateIn
from app.services import security_crud_service, security_service

router = APIRouter(prefix="/security", tags=["security"])

T = TypeVar("T")


async def _async_db(fn: Callable[..., T], db: Session, *args, **kwargs) -> T:
    return await asyncio.to_thread(fn, db, *args, **kwargs)


@router.get("/users", response_model=UserListOut)
async def list_users(db: Session = Depends(get_db)) -> UserListOut:
    return await _async_db(security_crud_service.list_users, db)


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(body: UserCreateIn, db: Session = Depends(get_db)) -> UserOut:
    return await _async_db(security_crud_service.create_user, db, body)


@router.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: str, db: Session = Depends(get_db)) -> UserOut:
    return await _async_db(security_crud_service.get_user, db, user_id)


@router.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, body: UserUpdateIn, db: Session = Depends(get_db)) -> UserOut:
    return await _async_db(security_crud_service.update_user, db, user_id, body)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, db: Session = Depends(get_db)) -> None:
    await _async_db(security_crud_service.delete_user, db, user_id)


@router.get("/roles", response_model=UserRoleListOut)
async def list_roles(
    user_id: Optional[str] = Query(None),
    active_only: bool = Query(False),
    db: Session = Depends(get_db),
) -> UserRoleListOut:
    return await _async_db(security_crud_service.list_roles, db, user_id=user_id, active_only=active_only)


@router.post("/roles", response_model=UserRoleOut, status_code=status.HTTP_201_CREATED)
async def create_role(body: UserRoleCreateIn, db: Session = Depends(get_db)) -> UserRoleOut:
    return await _async_db(security_crud_service.create_role, db, body)


@router.get("/roles/{role_id}", response_model=UserRoleOut)
async def get_role(role_id: str, db: Session = Depends(get_db)) -> UserRoleOut:
    return await _async_db(security_crud_service.get_role, db, role_id)


@router.patch("/roles/{role_id}", response_model=UserRoleOut)
async def update_role(role_id: str, body: UserRoleUpdateIn, db: Session = Depends(get_db)) -> UserRoleOut:
    return await _async_db(security_crud_service.update_role, db, role_id, body)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(role_id: str, db: Session = Depends(get_db)) -> None:
    await _async_db(security_crud_service.delete_role, db, role_id)


@router.get("/permissions/matrix", response_model=PermissionMatrixOut)
async def permissions_matrix(db: Session = Depends(get_db)) -> PermissionMatrixOut:
    return await _async_db(security_crud_service.permission_matrix, db)


@router.get("/permissions", response_model=PermissionListOut)
async def list_permissions(
    group_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> PermissionListOut:
    return await _async_db(security_crud_service.list_permissions, db, group_id=group_id)


@router.post("/permissions", response_model=PermissionOut, status_code=status.HTTP_201_CREATED)
async def create_permission(body: PermissionCreateIn, db: Session = Depends(get_db)) -> PermissionOut:
    return await _async_db(security_crud_service.create_permission, db, body)


@router.get("/permissions/{permission_id}", response_model=PermissionOut)
async def get_permission(permission_id: str, db: Session = Depends(get_db)) -> PermissionOut:
    return await _async_db(security_crud_service.get_permission, db, permission_id)


@router.patch("/permissions/{permission_id}", response_model=PermissionOut)
async def update_permission(
    permission_id: str,
    body: PermissionUpdateIn,
    db: Session = Depends(get_db),
) -> PermissionOut:
    return await _async_db(security_crud_service.update_permission, db, permission_id, body)


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_permission(permission_id: str, db: Session = Depends(get_db)) -> None:
    await _async_db(security_crud_service.delete_permission, db, permission_id)


@router.get("/groups", response_model=PermissionGroupListOut)
async def list_groups(db: Session = Depends(get_db)) -> PermissionGroupListOut:
    return await _async_db(security_crud_service.list_permission_groups, db)


@router.post("/groups", response_model=PermissionGroupOut, status_code=status.HTTP_201_CREATED)
async def create_group(body: PermissionGroupCreateIn, db: Session = Depends(get_db)) -> PermissionGroupOut:
    return await _async_db(security_crud_service.create_permission_group, db, body)


@router.get("/groups/{group_id}", response_model=PermissionGroupOut)
async def get_group(group_id: str, db: Session = Depends(get_db)) -> PermissionGroupOut:
    return await _async_db(security_crud_service.get_permission_group, db, group_id)


@router.patch("/groups/{group_id}", response_model=PermissionGroupOut)
async def update_group(
    group_id: str,
    body: PermissionGroupUpdateIn,
    db: Session = Depends(get_db),
) -> PermissionGroupOut:
    return await _async_db(security_crud_service.update_permission_group, db, group_id, body)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: str, db: Session = Depends(get_db)) -> None:
    await _async_db(security_crud_service.delete_permission_group, db, group_id)


@router.get("/api-keys", response_model=ApiKeyListOut)
async def list_api_keys(
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
) -> ApiKeyListOut:
    return await _async_db(security_service.list_api_keys, db, user_id)


@router.post("/api-keys/rotate", response_model=ApiKeyRotateOut)
async def rotate_api_key(body: ApiKeyRotateIn, db: Session = Depends(get_db)) -> ApiKeyRotateOut:
    return await _async_db(security_service.rotate_api_key, db, body, created_by=body.user_id)


@router.get("/webhooks", response_model=WebhookEndpointListOut)
async def list_webhooks(db: Session = Depends(get_db)) -> WebhookEndpointListOut:
    return await _async_db(security_crud_service.list_webhooks, db)


@router.post("/webhook-config", response_model=WebhookConfigOut)
async def webhook_config(body: WebhookConfigIn, db: Session = Depends(get_db)) -> WebhookConfigOut:
    return await _async_db(security_crud_service.configure_webhook, db, body)


@router.post("/seed", response_model=SecuritySeedOut)
async def seed_security(db: Session = Depends(get_db)) -> SecuritySeedOut:
    return await _async_db(security_crud_service.seed_security_baseline, db)
