from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LockerOperatorIn(BaseModel):
    id: str | None = None
    name: str
    document: str | None = None
    email: str | None = None
    phone: str | None = None
    operator_type: str = "LOGISTICS"
    country: str = "BR"
    active: bool = True
    commission_rate: float | None = None
    currency: str = "BRL"
    contract_ref: str | None = None
    sla_pickup_hours: int = 72
    sla_return_hours: int = 24
    status: str = "DRAFT"
    legal_name: str | None = None
    tier: str = "STANDARD"


class LockerOperatorUpdate(BaseModel):
    name: str | None = None
    document: str | None = None
    email: str | None = None
    phone: str | None = None
    operator_type: str | None = None
    active: bool | None = None
    commission_rate: float | None = None
    contract_ref: str | None = None
    sla_pickup_hours: int | None = None
    sla_return_hours: int | None = None
    status: str | None = None
    legal_name: str | None = None
    tier: str | None = None


class LockerOperatorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    document: str | None
    email: str | None
    phone: str | None
    operator_type: str
    country: str
    active: bool
    commission_rate: float | None
    currency: str
    contract_ref: str | None
    sla_pickup_hours: int
    sla_return_hours: int
    status: str
    legal_name: str | None
    tier: str
    created_at: datetime
    updated_at: datetime


class LockerOperatorListOut(BaseModel):
    items: list[LockerOperatorOut]
    total: int
