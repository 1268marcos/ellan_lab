"""Schemas da API pública B2C e parceiros (assinaturas)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PublicBenefitFlagsOut(BaseModel):
    free_shipping: bool = False
    priority_shelf: bool = False
    exclusive_deals: bool = False


class PublicPlanSummaryOut(BaseModel):
    code: str
    name: str
    monthly_fee_cents: int
    yearly_fee_cents: int | None = None
    benefits: PublicBenefitFlagsOut
    max_orders_per_month: int | None = None
    max_discount_pct: float | None = None


class PublicSubscriptionOut(BaseModel):
    id: str
    plan_type: str
    status: str
    monthly_fee_cents: int
    billing_cycle: str
    benefits: PublicBenefitFlagsOut
    cancel_at_period_end: bool = False
    trial_start: str | None = None
    trial_end: str | None = None
    current_period_start: str | None = None
    current_period_end: str | None = None
    next_billing_at: str | None = None
    partner_code: str | None = None


class PublicUsageMonthOut(BaseModel):
    usage_month: str | None = None
    orders_count: int = 0
    free_shipping_used: int = 0
    savings_cents: int = 0


class PublicBenefitUsageOut(BaseModel):
    benefit_type: str
    usage_count: int = 0
    usage_limit: int | None = None


class PublicLoyaltyOut(BaseModel):
    balance: int = 0


class PublicPromoRedemptionOut(BaseModel):
    promo_code: str
    discount_cents: int
    discount_pct: float = 0
    bonus_months: int = 0


class PublicMySubscriptionOut(BaseModel):
    ok: bool = True
    has_subscription: bool
    subscription: PublicSubscriptionOut | None = None
    plan: PublicPlanSummaryOut | None = None
    usage: PublicUsageMonthOut | None = None
    benefits_usage: list[PublicBenefitUsageOut] = Field(default_factory=list)
    loyalty: PublicLoyaltyOut | None = None
    entitled_players_count: int = 0
    promo_applied: PublicPromoRedemptionOut | None = None


class PublicBenefitCheckIn(BaseModel):
    benefit_type: str = Field(..., pattern="^(FREE_SHIPPING|PRIORITY_SHELF|EXCLUSIVE_DEAL)$")


class PublicBenefitCheckOut(BaseModel):
    ok: bool = True
    eligible: bool
    benefit_type: str
    reason: str | None = None
    subscription_id: str | None = None
    plan_type: str | None = None
    usage_count: int | None = None
    usage_limit: int | None = None


class PublicCancelIn(BaseModel):
    immediate: bool = False
    reason: str | None = Field(default=None, max_length=256)


class PublicSubscribeIn(BaseModel):
    plan_code: str = Field(..., min_length=1, max_length=20)
    billing_cycle: str = "MONTHLY"
    partner_code: str | None = None
    trial_days: int | None = Field(default=None, ge=0, le=90)
    promo_code: str | None = Field(default=None, max_length=32)


class PublicReferralOut(BaseModel):
    ok: bool = True
    referral_code: str
    reward_cents: int
    status: str


class PublicInvoiceItemOut(BaseModel):
    id: str
    period_start: str | None = None
    period_end: str | None = None
    amount_cents: int
    currency: str = "BRL"
    status: str
    paid_at: str | None = None


class PublicInvoicesOut(BaseModel):
    ok: bool = True
    items: list[PublicInvoiceItemOut]
    total: int


class PublicPlansCatalogOut(BaseModel):
    ok: bool = True
    items: list[PublicPlanSummaryOut]
    total: int


class PublicEntitlementItemOut(BaseModel):
    player_code: str
    player_name: str
    player_type: str | None = None
    priority_level: int = 0


class PublicEntitlementsOut(BaseModel):
    ok: bool = True
    plan_code: str
    items: list[PublicEntitlementItemOut]
    total: int


# --- Parceiros ---


class PartnerBenefitCheckIn(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    benefit_type: str = Field(..., pattern="^(FREE_SHIPPING|PRIORITY_SHELF|EXCLUSIVE_DEAL)$")
    partner_order_ref: str | None = Field(default=None, max_length=128)


class PartnerSubscriberOut(BaseModel):
    ok: bool = True
    found: bool
    user_id: str
    subscription: PublicSubscriptionOut | None = None
    plan: PublicPlanSummaryOut | None = None
    benefits: PublicBenefitFlagsOut | None = None


class PartnerWebhookEventIn(BaseModel):
    event_type: str = Field(..., min_length=3, max_length=64)
    subscription_id: str | None = None
    user_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class PartnerWebhookAckOut(BaseModel):
    ok: bool = True
    accepted: bool
    event_type: str
    note: str | None = None
