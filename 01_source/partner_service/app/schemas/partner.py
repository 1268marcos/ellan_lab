from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


class PartnerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    partner_type: str = Field(default="ECOMMERCE", max_length=64)
    legal_name: str | None = Field(default=None, max_length=255)
    contact_email: EmailStr | None = None
    status: str = Field(default="ACTIVE", max_length=32)


class PartnerOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    partner_type: str
    legal_name: str | None
    contact_email: str | None
    status: str
    created_at: datetime
    updated_at: datetime


class PartnerCreateResponse(PartnerOut):
    api_key: str | None = Field(default=None, description="Returned only on create/rotate")


class ApiKeyRotateResponse(BaseModel):
    api_key: str
    key_prefix: str


class PartnerPublicDict(BaseModel):
    """Schema used by shadow mode comparator for GET /partners/{id}."""

    id: str
    name: str
    partner_type: str
    legal_name: str | None = None
    contact_email: str | None = None
    status: str
    created_at: Any = None
    updated_at: Any = None
