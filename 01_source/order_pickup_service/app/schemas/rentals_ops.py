from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

RentalContractStatus = Literal[
    "PENDING",
    "ACTIVE",
    "EXPIRED",
    "CANCELLED",
    "SUSPENDED",
    "OVERDUE",
    "ENDED",
]
BillingCycle = Literal["DAILY", "WEEKLY", "MONTHLY", "QUARTERLY", "YEARLY"]


class RentalPlanIn(BaseModel):
    locker_id: Optional[str] = Field(None, max_length=36)
    slot_size: Optional[str] = Field(None, max_length=8)
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = None
    billing_cycle: BillingCycle = "MONTHLY"
    amount_cents: int = Field(ge=0)
    currency: str = Field(default="BRL", max_length=8)
    max_duration_days: Optional[int] = Field(None, ge=1)
    grace_period_hours: int = Field(default=24, ge=0)
    active: bool = True


class RentalPlanUpdate(BaseModel):
    locker_id: Optional[str] = Field(None, max_length=36)
    slot_size: Optional[str] = Field(None, max_length=8)
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = None
    billing_cycle: Optional[BillingCycle] = None
    amount_cents: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=8)
    max_duration_days: Optional[int] = Field(None, ge=1)
    grace_period_hours: Optional[int] = Field(None, ge=0)
    active: Optional[bool] = None


class RentalContractIn(BaseModel):
    locker_id: str = Field(min_length=1, max_length=36)
    slot_label: str = Field(min_length=1, max_length=20)
    plan_id: Optional[str] = Field(None, max_length=36)
    tenant_id: Optional[str] = Field(None, max_length=100)
    renter_user_id: Optional[str] = Field(None, max_length=36)
    renter_name: Optional[str] = Field(None, max_length=255)
    renter_document: Optional[str] = Field(None, max_length=32)
    renter_phone: Optional[str] = Field(None, max_length=32)
    renter_email: Optional[str] = Field(None, max_length=128)
    amount_cents: Optional[int] = Field(None, ge=0)
    currency: str = Field(default="BRL", max_length=8)
    billing_cycle: Optional[BillingCycle] = None
    next_billing_at: Optional[datetime] = None
    auto_renew: bool = False
    status: RentalContractStatus = "PENDING"


class RentalContractUpdate(BaseModel):
    renter_name: Optional[str] = Field(None, max_length=255)
    renter_document: Optional[str] = Field(None, max_length=32)
    renter_phone: Optional[str] = Field(None, max_length=32)
    renter_email: Optional[str] = Field(None, max_length=128)
    amount_cents: Optional[int] = Field(None, ge=0)
    billing_cycle: Optional[BillingCycle] = None
    next_billing_at: Optional[datetime] = None
    auto_renew: Optional[bool] = None
    status: Optional[RentalContractStatus] = None
    cancel_reason: Optional[str] = Field(None, max_length=255)


class RentalContractCancelIn(BaseModel):
    cancel_reason: Optional[str] = Field(None, max_length=255)


class RentalWebhookIn(BaseModel):
    tenant_id: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=8, max_length=500)
    secret: Optional[str] = Field(None, max_length=256)
    events: list[str] = Field(default_factory=lambda: ["rental.contract.created", "rental.contract.ended"])
    active: bool = True


class RentalWebhookUpdate(BaseModel):
    url: Optional[str] = Field(None, min_length=8, max_length=500)
    secret: Optional[str] = Field(None, max_length=256)
    events: Optional[list[str]] = None
    active: Optional[bool] = None
