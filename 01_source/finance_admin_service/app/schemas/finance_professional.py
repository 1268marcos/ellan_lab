from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CommercialContractIn(BaseModel):
    partner_id: str
    catalog_code: str | None = None
    contract_type: str = "MSA"
    title: str
    effective_from: date
    effective_until: date | None = None
    currency: str = "BRL"
    status: str = "ACTIVE"
    billing_plan_id: str | None = None
    metadata_json: str = "{}"


class CommercialContractOut(CommercialContractIn):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


class CommercialContractListOut(BaseModel):
    items: list[CommercialContractOut]
    total: int


class IntegrationMilestoneIn(BaseModel):
    catalog_code: str
    phase: str
    title: str
    target_date: date | None = None
    status: str = "PENDING"
    owner: str | None = None
    blocker_notes: str | None = None
    sort_order: int = 100


class IntegrationMilestoneUpdate(BaseModel):
    phase: str | None = None
    title: str | None = None
    target_date: date | None = None
    completed_at: datetime | None = None
    status: str | None = None
    owner: str | None = None
    blocker_notes: str | None = None
    sort_order: int | None = None


class IntegrationMilestoneOut(IntegrationMilestoneIn):
    model_config = ConfigDict(from_attributes=True)

    id: str
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class IntegrationMilestoneListOut(BaseModel):
    items: list[IntegrationMilestoneOut]
    total: int


class PartnerReadinessOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    catalog_code: str
    readiness_score: int
    integration_score: int
    billing_score: int
    compliance_score: int
    blueprint_score: int = 0
    integration_blueprint_code: str | None = None
    grade: str
    blockers_json: str
    computed_at: datetime


class ReadinessListOut(BaseModel):
    items: list[PartnerReadinessOut]
    total: int
    average_score: float


class ReadinessRecomputeOut(BaseModel):
    recomputed: int
    average_score: float


class SlaDefinitionIn(BaseModel):
    partner_id: str
    catalog_code: str | None = None
    metric_code: str
    metric_name: str
    target_value: Decimal
    target_unit: str
    window_days: int = 30
    penalty_credit_pct: Decimal | None = None
    active: bool = True


class SlaDefinitionOut(SlaDefinitionIn):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class SlaDefinitionListOut(BaseModel):
    items: list[SlaDefinitionOut]
    total: int


class SlaBreachIn(BaseModel):
    sla_id: str
    partner_id: str
    observed_value: Decimal
    breach_at: datetime | None = None
    notes: str | None = None
    auto_credit_note: bool = True


class SlaBreachOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sla_id: str
    partner_id: str
    observed_value: Decimal
    breach_at: datetime
    status: str
    credit_note_id: str | None
    notes: str | None
    created_at: datetime


class SlaBreachListOut(BaseModel):
    items: list[SlaBreachOut]
    total: int


class EcosystemSummaryOut(BaseModel):
    total_players: int
    live_count: int
    pilot_count: int
    planned_count: int
    linked_partners: int
    total_relations: int
    total_capabilities: int
    by_segment: dict[str, int]
    by_integration_status: dict[str, int]
    readiness_average: float
    top_ready: list[PartnerReadinessOut] = Field(default_factory=list)


class CycleCloseOut(BaseModel):
    cycle_id: str
    status: str
    total_amount_cents: int
    tax_cents: int = 0
    due_date: str | None = None
    invoice_id: str | None = None
    line_items_summed: int


class WebhookReplayOut(BaseModel):
    delivery_id: str
    status: str
    attempt_count: int
    http_status: int | None
