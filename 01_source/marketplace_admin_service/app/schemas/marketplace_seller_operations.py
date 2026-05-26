from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OnboardingTaskOut(BaseModel):
    id: str
    seller_id: str
    task_code: str
    title: str
    category: str
    status: str
    required: bool
    sort_order: int
    completed_at: datetime | None = None
    completed_by: str | None = None
    notes: str | None = None

    model_config = {"from_attributes": True}


class OnboardingTaskListOut(BaseModel):
    tasks: list[OnboardingTaskOut]
    total: int
    completed_count: int
    progress_pct: float


class OnboardingTaskCompleteIn(BaseModel):
    completed_by: str = "ops_admin"
    notes: str | None = None


class ChannelSkuMapCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str
    internal_sku: str
    channel_sku: str
    seller_product_id: str | None = None
    active: bool = True


class ChannelSkuMapOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str
    partner_code: str | None = None
    internal_sku: str
    channel_sku: str
    seller_product_id: str | None = None
    active: bool
    last_synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChannelSkuMapListOut(BaseModel):
    maps: list[ChannelSkuMapOut]
    total: int


class PricingRuleCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str | None = None
    rule_type: str
    name: str
    min_price_cents: int | None = None
    max_discount_pct: float | None = None
    markup_pct: float | None = None
    currency: str = "BRL"
    priority: int = 100
    active: bool = True


class PricingRuleOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str | None = None
    partner_code: str | None = None
    rule_type: str
    name: str
    min_price_cents: int | None = None
    max_discount_pct: Decimal | None = None
    markup_pct: Decimal | None = None
    currency: str
    priority: int
    active: bool

    model_config = {"from_attributes": True}


class PricingRuleListOut(BaseModel):
    rules: list[PricingRuleOut]
    total: int


class ReturnPolicyCreateIn(BaseModel):
    seller_id: str
    channel_partner_id: str | None = None
    policy_code: str
    return_window_days: int = 7
    restocking_fee_pct: float = 0
    accepts_locker_return: bool = True
    rma_required: bool = True
    status: str = "ACTIVE"
    notes: str | None = None


class ReturnPolicyOut(BaseModel):
    id: str
    seller_id: str
    channel_partner_id: str | None = None
    policy_code: str
    return_window_days: int
    restocking_fee_pct: Decimal
    accepts_locker_return: bool
    rma_required: bool
    status: str
    notes: str | None = None

    model_config = {"from_attributes": True}


class ReturnPolicyListOut(BaseModel):
    policies: list[ReturnPolicyOut]
    total: int


class NotificationSubCreateIn(BaseModel):
    seller_id: str
    event_type: str
    channel: str
    destination: str
    active: bool = True
    locale: str = "pt-BR"


class NotificationSubOut(BaseModel):
    id: str
    seller_id: str
    event_type: str
    channel: str
    destination: str
    active: bool
    locale: str

    model_config = {"from_attributes": True}


class NotificationSubListOut(BaseModel):
    subscriptions: list[NotificationSubOut]
    total: int


class InventoryAllocationOut(BaseModel):
    id: str
    seller_id: str
    seller_product_id: str
    channel_partner_id: str
    partner_code: str | None = None
    locker_id: str | None = None
    allocated_qty: int
    reserved_qty: int
    available_qty: int

    model_config = {"from_attributes": True}


class InventoryAllocationListOut(BaseModel):
    allocations: list[InventoryAllocationOut]
    total: int


class InventoryAllocationUpsertIn(BaseModel):
    seller_id: str
    seller_product_id: str
    channel_partner_id: str
    locker_id: str | None = None
    allocated_qty: int
    reserved_qty: int = 0


class FulfillmentPreferenceOut(BaseModel):
    id: str
    seller_id: str
    default_locker_id: str | None = None
    split_shipments_allowed: bool
    max_packages_per_order: int
    prefer_nearest_locker: bool
    handoff_mode: str
    packaging_notes: str | None = None

    model_config = {"from_attributes": True}


class FulfillmentPreferenceUpsertIn(BaseModel):
    seller_id: str
    default_locker_id: str | None = None
    split_shipments_allowed: bool = False
    max_packages_per_order: int = 1
    prefer_nearest_locker: bool = True
    handoff_mode: str = "LOCKER_FIRST"
    packaging_notes: str | None = None


class SellerOperationsSummaryOut(BaseModel):
    seller_id: str
    onboarding_progress_pct: float
    onboarding_pending: int
    sku_maps: int
    pricing_rules: int
    return_policies: int
    notification_subs: int
    inventory_allocations: int
    has_fulfillment_prefs: bool
