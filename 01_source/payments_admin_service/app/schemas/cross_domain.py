from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Orm(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PaymentEcosystemPlayerIn(BaseModel):
    id: str | None = None
    code: str
    name: str
    segment: str
    countries_json: list[str] = Field(default_factory=list)
    parent_player_code: str | None = None
    integration_status: str = "SANDBOX"
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PaymentEcosystemPlayerUpdate(BaseModel):
    name: str | None = None
    integration_status: str | None = None
    countries_json: list[str] | None = None
    is_active: bool | None = None
    metadata_json: dict[str, Any] | None = None


class PaymentEcosystemPlayerOut(_Orm):
    id: str
    code: str
    name: str
    segment: str
    countries_json: list[str] | dict
    integration_status: str
    is_active: bool


class PaymentEcosystemPlayerListOut(BaseModel):
    items: list[PaymentEcosystemPlayerOut]
    total: int


class PaymentOrderContextIn(BaseModel):
    id: str | None = None
    order_id: str
    tenant_id: str | None = None
    primary_transaction_id: str | None = None
    locker_id: str | None = None
    region_code: str | None = None
    sales_channel: str | None = None
    marketplace_partner_id: str | None = None
    carrier_partner_id: str | None = None
    locker_network_code: str | None = None
    status: str = "OPEN"
    total_amount_cents: int = 0
    currency: str = "BRL"
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    player_links: list["PaymentContextPlayerLinkIn"] = Field(default_factory=list)


class PaymentContextPlayerLinkIn(BaseModel):
    player_code: str
    role: str
    amount_cents: int | None = None
    share_pct: Decimal | None = None


class PaymentOrderContextOut(_Orm):
    id: str
    order_id: str
    tenant_id: str | None
    primary_transaction_id: str | None
    locker_id: str | None
    region_code: str | None
    locker_network_code: str | None
    status: str
    total_amount_cents: int
    currency: str
    player_links: list["PaymentContextPlayerLinkOut"] = Field(default_factory=list)


class PaymentContextPlayerLinkOut(_Orm):
    id: str
    player_code: str
    role: str
    amount_cents: int | None
    share_pct: Decimal | None


class PaymentOrderContextListOut(BaseModel):
    items: list[PaymentOrderContextOut]
    total: int


class PaymentReconciliationBatchIn(BaseModel):
    id: str | None = None
    batch_code: str
    region_code: str | None = None
    gateway: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    currency: str = "BRL"
    notes: str | None = None


class PaymentReconciliationBatchUpdate(BaseModel):
    status: str | None = None
    matched_count: int | None = None
    mismatch_count: int | None = None
    expected_count: int | None = None
    total_amount_cents: int | None = None
    notes: str | None = None


class PaymentReconciliationBatchOut(_Orm):
    id: str
    batch_code: str
    region_code: str | None
    gateway: str | None
    status: str
    expected_count: int
    matched_count: int
    mismatch_count: int
    total_amount_cents: int
    currency: str
    created_at: datetime


class PaymentReconciliationBatchListOut(BaseModel):
    items: list[PaymentReconciliationBatchOut]
    total: int


class WebhookDeliveryOut(_Orm):
    id: str
    endpoint_id: str
    event_name: str
    status: str
    attempt_count: int
    aggregate_type: str | None
    aggregate_id: str | None
    created_at: datetime


class WebhookDeliveryListOut(BaseModel):
    items: list[WebhookDeliveryOut]
    total: int


class PartnerPaymentHoldIn(BaseModel):
    id: str | None = None
    partner_id: str
    invoice_id: str
    order_id: str | None = None
    hold_amount_cents: int
    release_schedule: str = "AFTER_15_DAYS"
    status: str = "HELD"


class PartnerPaymentHoldUpdate(BaseModel):
    status: str | None = None
    released_amount_cents: int | None = None
    dispute_result: str | None = None


class PartnerPaymentHoldOut(_Orm):
    id: str
    partner_id: str
    invoice_id: str
    order_id: str | None
    hold_amount_cents: int
    status: str
    release_schedule: str
    created_at: datetime


class PartnerPaymentHoldListOut(BaseModel):
    items: list[PartnerPaymentHoldOut]
    total: int


class SavedPaymentMethodIn(BaseModel):
    id: str | None = None
    user_id: str
    method_code: str
    gateway_token: str
    last4: str | None = None
    card_brand: str | None = None
    is_default: bool = False


class SavedPaymentMethodOut(_Orm):
    id: str
    user_id: str
    method_code: str
    last4: str | None
    card_brand: str | None
    is_default: bool
    is_active: bool


class SavedPaymentMethodListOut(BaseModel):
    items: list[SavedPaymentMethodOut]
    total: int


class PaymentIntelligenceSummary(BaseModel):
    transactions_total: int
    transactions_approved: int
    reconciliation_pending: int
    open_batches: int
    webhook_pending: int
    holds_active_cents: int
    ecosystem_players_live: int
    ecosystem_players_total: int
    player_relations_total: int
    priority_players_live: int
    orders_with_context: int
    segments: dict[str, int]
    priority_player_codes: list[str]
    ecosystem_segments_defined: int = 0
    country_coverage_rows: int = 0
    integrations_production_ready: int = 0
    integrations_avg_readiness: float = 0.0
    open_integration_incidents: int = 0
    active_settlement_corridors: int = 0
    routing_rules_active: int = 0
    milestones_in_progress: int = 0
    external_references_total: int = 0
    pending_domain_obligations: int = 0
    blocking_domain_obligations: int = 0
    cross_domain_gaps_detected: int = 0
    cross_domain_events_pending: int = 0


class PaymentOrderGraphOut(BaseModel):
    order_id: str
    context: PaymentOrderContextOut | None
    transactions: list[dict[str, Any]]
    instructions: list[dict[str, Any]]
    splits: list[dict[str, Any]]
    payments: list[dict[str, Any]]
    holds: list[dict[str, Any]]
    gateway_events: list[dict[str, Any]]
