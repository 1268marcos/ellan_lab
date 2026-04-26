from __future__ import annotations

from pydantic import BaseModel, Field


class PartnerStatusTransitionIn(BaseModel):
    to_status: str = Field(..., description="Novo status do parceiro")
    reason: str | None = Field(default=None, description="Motivo da transição")


class PartnerStatusOut(BaseModel):
    ok: bool
    partner_id: str
    partner_type: str
    from_status: str | None = None
    to_status: str
    changed_by: str | None = None
    changed_at: str


class PartnerStatusHistoryItemOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    from_status: str | None = None
    to_status: str
    reason: str | None = None
    changed_by: str | None = None
    changed_at: str


class PartnerStatusHistoryListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerStatusHistoryItemOut]


class PartnerContactIn(BaseModel):
    contact_type: str = Field(..., description="COMMERCIAL|TECHNICAL|BILLING|EMERGENCY")
    name: str = Field(..., min_length=1, max_length=128)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_primary: bool = Field(default=False)


class PartnerContactPatchIn(BaseModel):
    contact_type: str | None = Field(default=None, description="COMMERCIAL|TECHNICAL|BILLING|EMERGENCY")
    name: str | None = Field(default=None, min_length=1, max_length=128)
    email: str | None = Field(default=None, max_length=128)
    phone: str | None = Field(default=None, max_length=32)
    is_primary: bool | None = Field(default=None)


class PartnerContactOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    contact_type: str
    name: str
    email: str | None = None
    phone: str | None = None
    is_primary: bool
    created_at: str
    updated_at: str


class PartnerContactListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerContactOut]


class PartnerSlaAgreementIn(BaseModel):
    country: str = Field(default="BR", min_length=2, max_length=2)
    product_category: str | None = Field(default=None, max_length=64)
    sla_pickup_hours: int = Field(default=72, ge=1, le=720)
    sla_return_hours: int = Field(default=24, ge=1, le=720)
    penalty_pct: float = Field(default=0, ge=0, le=100)
    valid_from: str = Field(..., description="Data YYYY-MM-DD")
    valid_until: str | None = Field(default=None, description="Data YYYY-MM-DD")
    is_active: bool = Field(default=True)


class PartnerSlaAgreementPatchIn(BaseModel):
    country: str | None = Field(default=None, min_length=2, max_length=2)
    product_category: str | None = Field(default=None, max_length=64)
    sla_pickup_hours: int | None = Field(default=None, ge=1, le=720)
    sla_return_hours: int | None = Field(default=None, ge=1, le=720)
    penalty_pct: float | None = Field(default=None, ge=0, le=100)
    valid_from: str | None = Field(default=None, description="Data YYYY-MM-DD")
    valid_until: str | None = Field(default=None, description="Data YYYY-MM-DD")
    is_active: bool | None = Field(default=None)


class PartnerSlaAgreementOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    country: str
    product_category: str | None = None
    sla_pickup_hours: int
    sla_return_hours: int
    penalty_pct: float
    valid_from: str
    valid_until: str | None = None
    is_active: bool
    created_at: str


class PartnerSlaAgreementListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerSlaAgreementOut]


class PartnerDeleteOut(BaseModel):
    ok: bool
    id: str
    message: str


class PartnerApiKeyIn(BaseModel):
    label: str | None = Field(default=None, max_length=64)
    scopes: list[str] = Field(default_factory=list)
    expires_at: str | None = Field(default=None, description="ISO-8601 UTC")


class PartnerApiKeyOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    key_prefix: str
    label: str | None = None
    scopes: list[str]
    expires_at: str | None = None
    last_used_at: str | None = None
    revoked_at: str | None = None
    created_at: str


class PartnerApiKeyCreateOut(BaseModel):
    ok: bool
    message: str
    api_key: str
    item: PartnerApiKeyOut


class PartnerApiKeyListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerApiKeyOut]


class PartnerWebhookEndpointIn(BaseModel):
    url: str = Field(..., max_length=500)
    secret: str = Field(..., min_length=8, max_length=256)
    events: list[str] = Field(default_factory=lambda: ["*"])
    api_version: str = Field(default="v1", max_length=10)
    active: bool = Field(default=True)


class PartnerWebhookEndpointOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    url: str
    events: list[str]
    api_version: str
    active: bool
    created_at: str
    updated_at: str


class PartnerWebhookEndpointListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerWebhookEndpointOut]


class PartnerWebhookDeliveryTestIn(BaseModel):
    event_type: str = Field(..., max_length=80)
    payload: dict = Field(default_factory=dict)


class PartnerWebhookDeliveryOut(BaseModel):
    id: str
    endpoint_id: str
    event_id: str
    event_type: str
    http_status: int | None = None
    attempt_count: int
    status: str
    last_error: str | None = None
    next_retry_at: str | None = None
    delivered_at: str | None = None
    created_at: str


class PartnerWebhookDeliveryListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerWebhookDeliveryOut]


class PartnerIntegrationHealthIn(BaseModel):
    endpoint_url: str | None = Field(default=None, max_length=500)
    status: str = Field(..., description="UP|DOWN|DEGRADED|TIMEOUT")
    latency_ms: int | None = Field(default=None, ge=0, le=600000)
    http_status: int | None = Field(default=None, ge=100, le=599)
    error_message: str | None = Field(default=None, max_length=500)


class PartnerIntegrationHealthOut(BaseModel):
    id: int
    partner_id: str
    partner_type: str
    endpoint_url: str | None = None
    checked_at: str
    status: str
    latency_ms: int | None = None
    http_status: int | None = None
    error_message: str | None = None


class PartnerIntegrationHealthListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerIntegrationHealthOut]


class PartnerSettlementGenerateIn(BaseModel):
    period_start: str = Field(..., description="Data YYYY-MM-DD")
    period_end: str = Field(..., description="Data YYYY-MM-DD")
    revenue_share_pct: float = Field(..., ge=0, le=1)
    fees_cents: int = Field(default=0, ge=0)
    currency: str = Field(default="BRL", min_length=3, max_length=8)
    notes: str | None = Field(default=None, max_length=2000)


class PartnerSettlementApproveIn(BaseModel):
    settlement_ref: str | None = Field(default=None, max_length=128)
    notes: str | None = Field(default=None, max_length=2000)


class PartnerSettlementOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    period_start: str
    period_end: str
    currency: str
    total_orders: int
    gross_revenue_cents: int
    revenue_share_pct: float
    revenue_share_cents: int
    fees_cents: int
    net_amount_cents: int
    status: str
    settled_at: str | None = None
    settlement_ref: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str


class PartnerSettlementListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerSettlementOut]


class PartnerPerformanceOut(BaseModel):
    id: str
    partner_id: str
    period_month: str
    total_orders: int
    on_time_pickup_pct: float | None = None
    return_rate_pct: float | None = None
    avg_pickup_hours: float | None = None
    sla_compliance_pct: float | None = None
    webhook_success_rate: float | None = None
    generated_at: str


class PartnerPerformanceListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerPerformanceOut]


class PartnerServiceAreaIn(BaseModel):
    locker_id: str = Field(..., max_length=36)
    priority: int = Field(default=100, ge=0, le=9999)
    exclusive: bool = Field(default=False)
    valid_from: str = Field(..., description="Data YYYY-MM-DD")
    valid_until: str | None = Field(default=None, description="Data YYYY-MM-DD")
    is_active: bool = Field(default=True)


class PartnerServiceAreaOut(BaseModel):
    id: str
    partner_id: str
    partner_type: str
    locker_id: str
    priority: int
    exclusive: bool
    valid_from: str
    valid_until: str | None = None
    is_active: bool
    created_at: str


class PartnerServiceAreaListOut(BaseModel):
    ok: bool
    total: int
    items: list[PartnerServiceAreaOut]


class PartnerOpsAuditItemOut(BaseModel):
    id: str
    action: str
    result: str
    correlation_id: str
    user_id: str | None = None
    role: str | None = None
    partner_id: str | None = None
    error_message: str | None = None
    details: dict = Field(default_factory=dict)
    created_at: str


class PartnerOpsAuditListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[PartnerOpsAuditItemOut]


class PartnerOpsActionsOut(BaseModel):
    ok: bool
    total: int
    actions: list[str]


class PartnerOpsKpiCountOut(BaseModel):
    key: str
    count: int


class PartnerOpsKpiErrorDailyOut(BaseModel):
    day: str
    count: int


class PartnerOpsKpiTopPartnerOut(BaseModel):
    partner_id: str
    count: int


class PartnerOpsKpisOut(BaseModel):
    ok: bool
    from_: str = Field(..., alias="from")
    to: str
    total_events: int
    total_errors: int
    error_rate_pct: float
    counts_by_action: list[PartnerOpsKpiCountOut]
    counts_by_result: list[PartnerOpsKpiCountOut]
    errors_by_day: list[PartnerOpsKpiErrorDailyOut]
    top_partners: list[PartnerOpsKpiTopPartnerOut]


class PartnerOpsChangeDailyOut(BaseModel):
    day: str
    total: int
    status: int
    contact: int
    sla: int
    other: int


class PartnerOpsChangeDistributionItemOut(BaseModel):
    change_type: str
    count: int
    pct: float


class PartnerOpsBadgeLegendItemOut(BaseModel):
    key: str
    label: str
    color: str
    icon: str


class PartnerOpsChangesSeriesOut(BaseModel):
    ok: bool
    from_: str = Field(..., alias="from")
    to: str
    total_changes: int
    daily_series: list[PartnerOpsChangeDailyOut]
    distribution: list[PartnerOpsChangeDistributionItemOut]
    badges: list[PartnerOpsBadgeLegendItemOut]


class PartnerOpsCompareCardOut(BaseModel):
    change_type: str
    label: str
    current_count: int
    previous_count: int
    delta_count: int
    delta_pct: float
    trend: str
    badge_bg_color: str
    badge_text_color: str


class PartnerOpsCompareOut(BaseModel):
    ok: bool
    from_: str = Field(..., alias="from")
    to: str
    previous_from: str
    previous_to: str
    total_current: int
    total_previous: int
    total_delta_count: int
    total_delta_pct: float
    confidence_level: str
    volume_note: str
    confidence_badge: PartnerOpsBadgeLegendItemOut
    data_quality_flags: list[str]
    cards: list[PartnerOpsCompareCardOut]
    badges: list[PartnerOpsBadgeLegendItemOut]


class PartnerOpsDashboardOut(BaseModel):
    ok: bool
    from_: str = Field(..., alias="from")
    to: str
    timezone_ref: str
    partner_id: str | None = None
    included_sections: list[str]
    kpis: PartnerOpsKpisOut | None = None
    compare: PartnerOpsCompareOut | None = None
    changes_series: PartnerOpsChangesSeriesOut | None = None


class PartnerWebhookOpsDailyOut(BaseModel):
    day: str
    total: int
    delivered: int
    failed: int
    dead_letter: int
    pending: int
    error_rate_pct: float


class PartnerWebhookOpsTopPartnerOut(BaseModel):
    partner_id: str
    total: int
    failed: int
    dead_letter: int
    pending: int
    error_rate_pct: float
    avg_latency_ms: float
    p95_latency_ms: float


class PartnerWebhookOpsTopEndpointOut(BaseModel):
    endpoint_id: str
    partner_id: str
    endpoint_url: str
    total: int
    failed: int
    dead_letter: int
    pending: int
    error_rate_pct: float
    avg_latency_ms: float
    p95_latency_ms: float


class PartnerWebhookOpsAlertOut(BaseModel):
    code: str
    severity: str
    title: str
    message: str
    value: float
    threshold: float
    partner_id: str | None = None
    endpoint_id: str | None = None
    endpoint_url: str | None = None


class PartnerWebhookOpsMetricsOut(BaseModel):
    ok: bool
    from_: str = Field(..., alias="from")
    to: str
    timezone_ref: str
    partner_id: str | None = None
    total_deliveries: int
    total_delivered: int
    total_failed: int
    total_dead_letter: int
    backlog_pending_failed: int
    error_rate_pct: float
    avg_latency_ms: float
    p95_latency_ms: float
    daily: list[PartnerWebhookOpsDailyOut]
    top_partners: list[PartnerWebhookOpsTopPartnerOut]
    top_endpoints: list[PartnerWebhookOpsTopEndpointOut]
    alerts: list[PartnerWebhookOpsAlertOut]
