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
