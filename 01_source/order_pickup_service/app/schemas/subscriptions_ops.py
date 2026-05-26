from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SubscriptionPlanOut(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None
    monthly_fee_cents: int
    yearly_fee_cents: int | None = None
    free_shipping: bool = False
    priority_shelf: bool = False
    exclusive_deals: bool = False
    priority_support: bool = False
    max_orders_per_month: int | None = None
    max_discount_pct: float | None = None
    features_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    created_at: str
    updated_at: str


class SubscriptionPlanIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=20)
    description: str | None = None
    monthly_fee_cents: int = Field(..., ge=0)
    yearly_fee_cents: int | None = Field(default=None, ge=0)
    free_shipping: bool = False
    priority_shelf: bool = False
    exclusive_deals: bool = False
    priority_support: bool = False
    max_orders_per_month: int | None = Field(default=None, ge=0)
    max_discount_pct: float | None = Field(default=None, ge=0, le=100)
    features_json: dict[str, Any] | None = None
    is_active: bool = True


class SubscriptionPlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    monthly_fee_cents: int | None = Field(default=None, ge=0)
    yearly_fee_cents: int | None = Field(default=None, ge=0)
    free_shipping: bool | None = None
    priority_shelf: bool | None = None
    exclusive_deals: bool | None = None
    priority_support: bool | None = None
    max_orders_per_month: int | None = Field(default=None, ge=0)
    max_discount_pct: float | None = Field(default=None, ge=0, le=100)
    features_json: dict[str, Any] | None = None
    is_active: bool | None = None


class CustomerSubscriptionOut(BaseModel):
    id: str
    user_id: str | None = None
    plan_type: str
    status: str
    monthly_fee_cents: int
    free_shipping: bool = False
    priority_shelf: bool = False
    exclusive_deals: bool = False
    billing_cycle: str = "MONTHLY"
    cancel_at_period_end: bool = False
    trial_start: str | None = None
    trial_end: str | None = None
    current_period_start: str | None = None
    current_period_end: str | None = None
    next_billing_at: str | None = None
    cancelled_at: str | None = None
    payment_method_id: str | None = None
    partner_code: str | None = None
    created_at: str
    updated_at: str


class CustomerSubscriptionIn(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=36)
    plan_type: str = Field(..., min_length=1, max_length=30)
    status: str = "ACTIVE"
    billing_cycle: str = "MONTHLY"
    payment_method_id: str | None = None
    partner_code: str | None = None
    trial_days: int | None = Field(default=None, ge=0, le=90)
    promo_code: str | None = Field(default=None, max_length=32)


class CustomerSubscriptionUpdate(BaseModel):
    status: str | None = None
    plan_type: str | None = None
    billing_cycle: str | None = None
    cancel_at_period_end: bool | None = None
    payment_method_id: str | None = None


class SubscriptionWebhookIn(BaseModel):
    url: str = Field(..., min_length=8, max_length=500)
    secret: str | None = Field(default=None, min_length=8, max_length=256)
    events: list[str] | None = None
    active: bool = True


class SubscriptionWebhookUpdate(BaseModel):
    url: str | None = Field(default=None, min_length=8, max_length=500)
    secret: str | None = Field(default=None, min_length=8, max_length=256)
    events: list[str] | None = None
    active: bool | None = None
