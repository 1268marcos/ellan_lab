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
    id: int
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