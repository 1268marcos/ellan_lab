from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

PassType = Literal["PIN", "QR", "OTP"]
DepositStatus = Literal["HELD", "RELEASED", "FORFEITED"]
BlockType = Literal["MAINTENANCE", "RESERVED", "QUARANTINE", "DEEP_CLEAN"]
TransferStatus = Literal["REQUESTED", "APPROVED", "COMPLETED", "REJECTED", "CANCELLED"]
DunningStage = Literal["REMINDER_1", "REMINDER_2", "SUSPEND", "COLLECTION", "WRITEOFF"]


class RentalAccessPassIssueIn(BaseModel):
    pass_type: PassType = "PIN"
    valid_hours: int = Field(default=72, ge=1, le=720)
    max_uses: int = Field(default=10, ge=1, le=1000)


class RentalDepositHoldIn(BaseModel):
    contract_id: str
    amount_cents: int = Field(ge=0)
    currency: str = "BRL"
    hold_reason: str = Field(default="SECURITY", max_length=64)
    payment_ref: Optional[str] = Field(None, max_length=64)


class RentalSlotBlockIn(BaseModel):
    locker_id: str
    slot_label: str = Field(min_length=1, max_length=20)
    block_type: BlockType = "MAINTENANCE"
    reason: Optional[str] = Field(None, max_length=255)
    starts_at: datetime
    ends_at: datetime


class RentalPricingRuleIn(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    network_id: Optional[str] = None
    slot_size: Optional[str] = Field(None, max_length=8)
    billing_cycle: Optional[str] = Field(None, max_length=20)
    base_amount_cents: int = Field(ge=0)
    surge_multiplier: Decimal = Field(default=Decimal("1.0"), ge=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    priority: int = 100
    active: bool = True


class RentalTransferRequestIn(BaseModel):
    contract_id: str
    to_locker_id: str
    to_slot_label: str = Field(min_length=1, max_length=20)
    requested_by: str = "ops"


class RentalQuoteIn(BaseModel):
    network_id: Optional[str] = None
    slot_size: Optional[str] = "M"
    billing_cycle: str = "MONTHLY"
    at: Optional[datetime] = None
