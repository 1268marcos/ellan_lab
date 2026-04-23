# 01_source/order_pickup_service/app/schemas/public_auth.py

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class PublicRegisterIn(BaseModel):
    full_name: str = Field(min_length=3, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class PublicLoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class PublicUserOut(BaseModel):
    id: str  # 🔥 ALTERADO
    full_name: str
    email: EmailStr
    phone: str | None
    is_active: bool
    email_verified: bool
    phone_verified: bool

    class Config:
        from_attributes = True


class PublicAuthTokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: PublicUserOut


class PublicAuthMeOut(BaseModel):
    authenticated: bool
    user: PublicUserOut | None


class PublicChangePasswordIn(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class PublicChangePasswordOut(BaseModel):
    ok: bool = True
    message: str = "password_updated"


class PublicEmailVerificationSendOut(BaseModel):
    ok: bool = True
    already_verified: bool = False
    delivery: str
    verification_link: str | None = None


class PublicEmailVerificationConfirmOut(BaseModel):
    ok: bool = True
    message: str = "email_verified"
    user: PublicUserOut


class PublicUserRoleOut(BaseModel):
    id: str | int | None = None
    user_id: str
    role: str
    scope_type: str | None = None
    scope_id: str | None = None
    is_active: bool = True
    granted_at: str | None = None
    revoked_at: str | None = None


class PublicAuthRolesOut(BaseModel):
    user_id: str
    roles: list[PublicUserRoleOut]