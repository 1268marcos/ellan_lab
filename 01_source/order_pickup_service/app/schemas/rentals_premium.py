from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

OnboardingStatus = Literal[
    "DRAFT", "KYC_SUBMITTED", "COMPLIANCE_REVIEW", "APPROVED", "LIVE", "SUSPENDED"
]
BreachStatus = Literal["OPEN", "ACKNOWLEDGED", "RESOLVED", "CREDITED"]
SettlementStatus = Literal["DRAFT", "APPROVED", "PAID", "VOID"]
DisputeStatus = Literal["OPEN", "UNDER_REVIEW", "RESOLVED", "REJECTED"]
RenewalOfferStatus = Literal["PENDING", "ACCEPTED", "DECLINED", "EXPIRED"]


class RentalOnboardingUpdate(BaseModel):
    status: Optional[OnboardingStatus] = None
    kyb_tier: Optional[str] = Field(None, max_length=16)
    compliance_score: Optional[Decimal] = None
    reviewer: Optional[str] = Field(None, max_length=128)
    notes: Optional[str] = None


class RentalSlaBreachIn(BaseModel):
    network_id: str
    sla_policy_id: Optional[str] = None
    contract_id: Optional[str] = None
    metric_code: str = Field(min_length=1, max_length=64)
    target_value: Decimal
    measured_value: Decimal
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "MEDIUM"
    penalty_cents: int = 0
    currency: str = "BRL"


class RentalSlaBreachUpdate(BaseModel):
    status: Optional[BreachStatus] = None
    penalty_cents: Optional[int] = None


class RentalSettlementBatchIn(BaseModel):
    operator_id: str
    period_start: datetime
    period_end: datetime
    gross_cents: int = Field(ge=0)
    commission_cents: int = Field(ge=0)
    adjustments_cents: int = 0
    currency: str = "BRL"


class RentalDisputeIn(BaseModel):
    contract_id: str
    dispute_type: str = Field(min_length=1, max_length=32)
    amount_cents: int = Field(ge=0)
    reason: Optional[str] = Field(None, max_length=255)
    currency: str = "BRL"


class RentalRenewalOfferIn(BaseModel):
    contract_id: str
    offer_amount_cents: int = Field(ge=0)
    valid_until: datetime
    billing_cycle: str = "MONTHLY"
    auto_renew: bool = False
    currency: str = "BRL"
