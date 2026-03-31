# 01_source/order_pickup_service/app/schemas/user.py

from __future__ import annotations

from pydantic import BaseModel, EmailStr
from typing import Optional

# For Pydantic v1
class ConfigMixin:
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    name: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase, ConfigMixin):
    id: int
    is_active: bool


class UserPublicOut(BaseModel, ConfigMixin):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    is_active: bool
    email_verified: bool
    phone_verified: bool
