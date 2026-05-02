from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class LockerOperatorOut(BaseModel):
    id: str
    name: str
    document: str | None = None
    email: str | None = None
    phone: str | None = None
    operator_type: str
    country: str
    active: bool
    commission_rate: float | None = None
    currency: str
    status: str
    contract_start_at: str | None = None
    contract_end_at: str | None = None
    created_at: str
    updated_at: str


class LockerOperatorListOut(BaseModel):
    ok: bool
    items: list[LockerOperatorOut]


class LockerOperatorCreateIn(BaseModel):
    id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=128)
    document: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    operator_type: str = Field(default="LOGISTICS", max_length=32)
    country: str = Field(default="BR", max_length=2)
    commission_rate: float | None = Field(default=None, ge=0)
    currency: str = Field(default="BRL", max_length=8)
    contract_start_at: datetime | None = None
    contract_end_at: datetime | None = None
    status: str = Field(default="DRAFT", max_length=30)


class LockerOperatorUpdateIn(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    document: str | None = Field(default=None, max_length=32)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    operator_type: str | None = Field(default=None, max_length=32)
    country: str | None = Field(default=None, max_length=2)
    active: bool | None = None
    commission_rate: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    contract_start_at: datetime | None = None
    contract_end_at: datetime | None = None
    status: str | None = Field(default=None, max_length=30)


class LockerOperatorDeleteOut(BaseModel):
    ok: bool
    id: str
