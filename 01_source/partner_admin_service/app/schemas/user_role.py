from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserOut(BaseModel):
    id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserListOut(BaseModel):
    users: list[UserOut]
    total: int


class UserRoleCreateIn(BaseModel):
    user_id: str
    role: str
    scope_type: str = "GLOBAL"
    scope_id: Optional[str] = None


class UserRoleUpdateIn(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    scope_type: Optional[str] = None
    scope_id: Optional[str] = None


class UserRoleOut(BaseModel):
    id: str
    user_id: str
    role: str
    scope_type: str
    scope_id: Optional[str] = None
    is_active: bool
    granted_at: datetime
    revoked_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserRoleListOut(BaseModel):
    roles: list[UserRoleOut]
    total: int
