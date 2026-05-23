from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, Field

NetworkType = Literal["LOCKER_NETWORK", "COLLECTION_POINT", "MARKETPLACE_HUB", "AGGREGATOR"]
InvoiceStatus = Literal["DRAFT", "ISSUED", "PAID", "OVERDUE", "VOID"]
OperatorStatus = Literal["ACTIVE", "SUSPENDED", "TERMINATED"]


class RentalNetworkIn(BaseModel):
    code: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    network_type: NetworkType = "LOCKER_NETWORK"
    hardware_vendor: Optional[str] = Field(None, max_length=64)
    primary_countries: list[str] = Field(default_factory=list)
    website_url: Optional[str] = Field(None, max_length=255)
    active: bool = True


class RentalNetworkUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    network_type: Optional[NetworkType] = None
    hardware_vendor: Optional[str] = Field(None, max_length=64)
    primary_countries: Optional[list[str]] = None
    website_url: Optional[str] = Field(None, max_length=255)
    active: Optional[bool] = None


class RentalCorridorIn(BaseModel):
    network_id: str = Field(min_length=1, max_length=36)
    origin_country: str = Field(min_length=2, max_length=2)
    destination_country: str = Field(min_length=2, max_length=2)
    sla_hours: int = Field(default=72, ge=1)
    currency: str = Field(default="EUR", max_length=8)
    active: bool = True


class RentalOperatorIn(BaseModel):
    tenant_id: Optional[str] = Field(None, max_length=100)
    network_id: Optional[str] = Field(None, max_length=36)
    legal_name: str = Field(min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=128)
    operator_code: str = Field(min_length=2, max_length=32)
    commission_bps: int = Field(default=0, ge=0, le=10000)
    status: OperatorStatus = "ACTIVE"
    contract_ref: Optional[str] = Field(None, max_length=64)
    contact_email: Optional[str] = Field(None, max_length=128)


class RentalOperatorUpdate(BaseModel):
    tenant_id: Optional[str] = Field(None, max_length=100)
    network_id: Optional[str] = Field(None, max_length=36)
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=128)
    commission_bps: Optional[int] = Field(None, ge=0, le=10000)
    status: Optional[OperatorStatus] = None
    contract_ref: Optional[str] = Field(None, max_length=64)
    contact_email: Optional[str] = Field(None, max_length=128)


class RentalBillingInvoiceIn(BaseModel):
    contract_id: str = Field(min_length=1, max_length=36)
    period_start: datetime
    period_end: datetime
    amount_cents: int = Field(ge=0)
    currency: str = Field(default="BRL", max_length=8)
    status: InvoiceStatus = "DRAFT"
    due_at: Optional[datetime] = None


class RentalBillingInvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    due_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None


class RentalSlaPolicyIn(BaseModel):
    network_id: str = Field(min_length=1, max_length=36)
    metric_code: str = Field(min_length=1, max_length=64)
    target_value: Decimal = Field(gt=0)
    unit: str = Field(min_length=1, max_length=16)
    breach_penalty_bps: int = Field(default=0, ge=0)
    active: bool = True
