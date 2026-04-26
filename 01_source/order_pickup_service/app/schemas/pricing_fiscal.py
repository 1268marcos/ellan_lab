from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProductBundleCreateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    code: str = Field(..., min_length=1, max_length=32)
    description: str | None = Field(default=None, max_length=4000)
    amount_cents: int = Field(..., ge=0)
    currency: str = Field(default="BRL", min_length=3, max_length=8)
    bundle_type: str = Field(default="FIXED", max_length=20)
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class ProductBundleItemCreateIn(BaseModel):
    product_id: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(default=1, ge=1)
    unit_price_cents: int | None = Field(default=None, ge=0)
    sort_order: int = Field(default=0, ge=0)


class PromotionCreateIn(BaseModel):
    code: str | None = Field(default=None, max_length=32)
    name: str = Field(..., min_length=1, max_length=128)
    type: str = Field(..., min_length=1, max_length=30)
    discount_pct: float | None = Field(default=None, ge=0, le=100)
    discount_cents: int | None = Field(default=None, ge=0)
    min_order_cents: int = Field(default=0, ge=0)
    max_discount_cents: int | None = Field(default=None, ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    per_user_limit: int | None = Field(default=1, ge=1)
    conditions_json: dict = Field(default_factory=dict)
    valid_from: datetime
    valid_until: datetime | None = None


class PromotionStatusPatchIn(BaseModel):
    is_active: bool
    reason: str | None = Field(default=None, max_length=4000)


class PromotionValidateIn(BaseModel):
    order_id: str = Field(..., min_length=1, max_length=64)
    user_id: str | None = Field(default=None, max_length=36)
    promotion_code: str | None = Field(default=None, max_length=32)
    items: list[dict] = Field(default_factory=list)
    total_amount_cents: int = Field(default=0, ge=0)


class ProductFiscalConfigUpsertIn(BaseModel):
    ncm_code: str | None = Field(default=None, max_length=10)
    cest: str | None = Field(default=None, max_length=9)
    icms_cst: str | None = Field(default=None, max_length=3)
    pis_cst: str | None = Field(default=None, max_length=2)
    cofins_cst: str | None = Field(default=None, max_length=2)
    iva_category: str | None = Field(default=None, max_length=20)
    is_active: bool = True
    unit_of_measure: str = Field(default="UN", max_length=6)
    origin_type: str = Field(default="0", max_length=1)
    cfop: str | None = Field(default=None, max_length=5)
    tax_rate_pct: float | None = Field(default=None, ge=0)
    is_service: bool = False


class Pr3ContractOut(BaseModel):
    ok: bool = True
    implemented: bool = False
    contract: str
    message: str
    next_step: str


class ProductBundleOut(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None
    amount_cents: int
    currency: str
    bundle_type: str
    is_active: bool
    valid_from: str | None = None
    valid_until: str | None = None
    created_at: str
    updated_at: str


class ProductBundleListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[ProductBundleOut]


class ProductBundleItemOut(BaseModel):
    id: int
    bundle_id: str
    product_id: str
    quantity: int
    unit_price_cents: int | None = None
    sort_order: int


class PromotionOut(BaseModel):
    id: str
    code: str | None = None
    name: str
    type: str
    discount_pct: float | None = None
    discount_cents: int | None = None
    min_order_cents: int
    max_discount_cents: int | None = None
    max_uses: int | None = None
    uses_count: int
    per_user_limit: int | None = None
    conditions_json: dict
    is_active: bool
    valid_from: str
    valid_until: str | None = None
    created_by: str | None = None
    created_at: str


class PromotionListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[PromotionOut]


class PromotionStatusOut(BaseModel):
    ok: bool
    promotion_id: str
    is_active: bool
    changed_at: str


class PromotionValidateOut(BaseModel):
    ok: bool
    valid: bool
    idempotent: bool = False
    promotion_id: str | None = None
    promotion_code: str | None = None
    discount_cents: int
    reason: str | None = None


class ProductFiscalConfigOut(BaseModel):
    sku_id: str
    ncm_code: str | None = None
    cest: str | None = None
    icms_cst: str | None = None
    pis_cst: str | None = None
    cofins_cst: str | None = None
    iva_category: str | None = None
    is_active: bool
    unit_of_measure: str
    origin_type: str
    cfop: str | None = None
    tax_rate_pct: float | None = None
    is_service: bool
    updated_at: str | None = None


class ProductFiscalConfigUpsertOut(BaseModel):
    ok: bool
    config: ProductFiscalConfigOut


class FiscalAutoClassificationLogItemOut(BaseModel):
    id: int
    order_id: str
    invoice_id: str | None = None
    sku_id: str
    ncm_applied: str | None = None
    icms_cst_applied: str | None = None
    pis_cst_applied: str | None = None
    cofins_cst_applied: str | None = None
    cfop_applied: str | None = None
    source: str
    classified_at: str


class FiscalAutoClassificationLogListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[FiscalAutoClassificationLogItemOut]


class FiscalAutoClassificationReprocessOut(BaseModel):
    ok: bool
    order_id: str
    rebuilt: bool
    total_items: int
    total_log_rows: int
    sources: list[str]


class PricingFiscalBadgeOut(BaseModel):
    key: str
    label: str
    color: str
    icon: str | None = None


class PricingFiscalOverviewKpiOut(BaseModel):
    key: str
    label: str
    current: int
    previous: int
    delta_pct: float
    trend: str


class PricingFiscalOverviewTopItemOut(BaseModel):
    key: str
    label: str
    current: int
    previous: int
    delta_pct: float
    trend: str


class PricingFiscalOverviewOut(BaseModel):
    ok: bool
    period_from: str
    period_to: str
    previous_from: str
    previous_to: str
    comparison: PricingFiscalOverviewKpiOut
    confidence_level: str
    confidence_note: str
    confidence_badge: PricingFiscalBadgeOut
    kpis: list[PricingFiscalOverviewKpiOut]
    tops_promotion_codes: list[PricingFiscalOverviewTopItemOut]
    tops_default_skus: list[PricingFiscalOverviewTopItemOut]
    tops_fiscal_source: list[PricingFiscalOverviewTopItemOut]


class PricingFiscalSourceSummaryItemOut(BaseModel):
    source: str
    current: int
    previous: int
    delta_pct: float
    trend: str


class PricingFiscalSourceSummaryOut(BaseModel):
    ok: bool
    period_from: str
    period_to: str
    previous_from: str
    previous_to: str
    total_current: int
    total_previous: int
    confidence_level: str
    confidence_note: str
    confidence_badge: PricingFiscalBadgeOut
    items: list[PricingFiscalSourceSummaryItemOut]


class PricingFiscalDefaultAlertItemOut(BaseModel):
    created_at: str
    order_id: str | None = None
    sku_id: str | None = None
    source: str | None = None
    message: str | None = None
    correlation_id: str


class PricingFiscalDefaultAlertsOut(BaseModel):
    ok: bool
    period_from: str
    period_to: str
    previous_from: str
    previous_to: str
    total_current: int
    total_previous: int
    delta_pct: float
    trend: str
    confidence_level: str
    confidence_note: str
    confidence_badge: PricingFiscalBadgeOut
    limit: int
    offset: int
    items: list[PricingFiscalDefaultAlertItemOut]

