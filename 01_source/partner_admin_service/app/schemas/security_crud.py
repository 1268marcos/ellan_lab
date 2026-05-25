from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.security import (
    ApiKeyListOut,
    ApiKeyRotateIn,
    ApiKeyRotateOut,
    PermissionGroupCreateIn,
    PermissionGroupListOut,
    PermissionGroupOut,
    PermissionCreateIn,
    PermissionListOut,
    PermissionOut,
    UserCreateIn,
    UserUpdateIn,
    WebhookEndpointListOut,
    WebhookEndpointOut,
)
from app.schemas.user_role import UserListOut, UserOut, UserRoleCreateIn, UserRoleListOut, UserRoleOut, UserRoleUpdateIn

__all__ = [
    "UserCreateIn",
    "UserUpdateIn",
    "UserOut",
    "UserListOut",
    "UserRoleCreateIn",
    "UserRoleUpdateIn",
    "UserRoleOut",
    "UserRoleListOut",
    "PermissionGroupCreateIn",
    "PermissionGroupUpdateIn",
    "PermissionGroupOut",
    "PermissionGroupListOut",
    "PermissionCreateIn",
    "PermissionUpdateIn",
    "PermissionOut",
    "PermissionListOut",
    "ApiKeyRotateIn",
    "ApiKeyRotateOut",
    "ApiKeyListOut",
    "WebhookConfigIn",
    "WebhookConfigOut",
    "PermissionMatrixOut",
    "PermissionMatrixRow",
    "SecuritySeedOut",
]


class PermissionGroupUpdateIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PermissionUpdateIn(BaseModel):
    group_id: Optional[str] = None
    object_key: Optional[str] = None


class WebhookConfigIn(BaseModel):
    id: Optional[str] = None
    url: str
    owner_type: str = "PLATFORM"
    owner_id: Optional[str] = None
    events: list[str] = Field(default_factory=lambda: ["*"])
    signing_algo: str = "HMAC_SHA256"
    active: bool = True


class WebhookConfigOut(BaseModel):
    endpoint: WebhookEndpointOut
    webhook_secret: Optional[str] = None


class PermissionMatrixRow(BaseModel):
    group_id: str
    group_name: str
    permissions: list[PermissionOut]
    member_user_ids: list[str] = Field(default_factory=list)


class PermissionMatrixOut(BaseModel):
    groups: list[PermissionMatrixRow]
    total_permissions: int


class SecuritySeedOut(BaseModel):
    users: int
    user_roles: int
    permission_groups: int
    permissions: int
    memberships: int
    role_catalog: int
