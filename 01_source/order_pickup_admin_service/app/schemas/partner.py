from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EcommercePartnerCreateIn(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    integration_type: str = "REST"
    api_base_url: Optional[str] = None
    revenue_share_pct: Optional[float] = None
    sla_pickup_hours: int = 72
    active: bool = True
    country: str = "BR"
    status: str = "DRAFT"
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    tier: str = "STANDARD"
    support_email: Optional[str] = None
    support_phone: Optional[str] = None


class EcommercePartnerUpdateIn(BaseModel):
    name: Optional[str] = None
    integration_type: Optional[str] = None
    api_base_url: Optional[str] = None
    revenue_share_pct: Optional[float] = None
    sla_pickup_hours: Optional[int] = None
    active: Optional[bool] = None
    status: Optional[str] = None
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    tier: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None


class EcommercePartnerOut(BaseModel):
    id: str
    name: str
    code: str
    integration_type: str
    api_base_url: Optional[str] = None
    revenue_share_pct: Optional[float] = None
    sla_pickup_hours: int
    active: bool
    country: str
    status: str
    legal_name: Optional[str] = None
    tax_id: Optional[str] = None
    tier: Optional[str] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EcommercePartnerListOut(BaseModel):
    partners: list[EcommercePartnerOut]
    total: int


class LogisticsPartnerCreateIn(BaseModel):
    id: Optional[str] = None
    name: str
    code: str
    integration_type: str = "REST"
    api_base_url: Optional[str] = None
    tracking_url_template: Optional[str] = None
    auth_type: Optional[str] = None
    default_sla_hours: int = 72
    reminder_hours_before: int = 24
    active: bool = True
    country: str = "BR"


class LogisticsPartnerUpdateIn(BaseModel):
    name: Optional[str] = None
    integration_type: Optional[str] = None
    api_base_url: Optional[str] = None
    tracking_url_template: Optional[str] = None
    auth_type: Optional[str] = None
    default_sla_hours: Optional[int] = None
    reminder_hours_before: Optional[int] = None
    active: Optional[bool] = None


class LogisticsPartnerOut(BaseModel):
    id: str
    name: str
    code: str
    integration_type: str
    api_base_url: Optional[str] = None
    tracking_url_template: Optional[str] = None
    auth_type: Optional[str] = None
    default_sla_hours: int
    reminder_hours_before: int
    active: bool
    country: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LogisticsPartnerListOut(BaseModel):
    partners: list[LogisticsPartnerOut]
    total: int


class PartnerContactCreateIn(BaseModel):
    contact_type: str = "PRIMARY"
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool = False


class PartnerContactOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    contact_type: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PartnerContactListOut(BaseModel):
    partner_id: str
    partner_type: str
    contacts: list[PartnerContactOut]
