from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ComplianceDimensionOut(BaseModel):
    key: str
    label: str
    weight_pct: float
    score_pct: float
    status: str
    detail: str


class ComplianceScoreOut(BaseModel):
    regulation_code: str
    regulation_name: str
    score_pct: float
    grade: str
    gaps: list[str]
    dimensions: list[ComplianceDimensionOut]
    snapshot_id: Optional[str] = None
    computed_at: datetime


class ComplianceCompareOut(BaseModel):
    codes: list[str]
    scores: list[ComplianceScoreOut]
    matrix: dict[str, dict[str, float]]


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_id: Optional[str] = None
    actor_role: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    regulation_code: Optional[str] = None
    summary: str
    created_at: datetime


class AuditEventListOut(BaseModel):
    items: list[AuditEventOut]
    total: int


class ConsentAnalyticsDayOut(BaseModel):
    date: str
    granted: int
    revoked: int
    net: int


class ConsentAnalyticsOut(BaseModel):
    regulation_code: Optional[str] = None
    days: int
    total_granted: int
    total_revoked: int
    opt_out_rate_pct: float
    by_channel: dict[str, int]
    by_type: dict[str, int]
    daily: list[ConsentAnalyticsDayOut]


class BreachTimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    breach_id: str
    milestone: str
    status: str
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


class BreachTimelineOut(BaseModel):
    breach_id: str
    regulation_code: str
    items: list[BreachTimelineEventOut]
    regulatory_deadline_hours: int
    hours_elapsed: Optional[float] = None
    on_track: bool


class DsrTaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject_request_id: str
    step_code: str
    step_order: int
    status: str
    assignee: Optional[str] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime


class DsrTaskListOut(BaseModel):
    subject_request_id: str
    request_type: str
    regulation_code: str
    progress_pct: float
    items: list[DsrTaskOut]


class DsrTaskUpdate(BaseModel):
    status: Optional[str] = None
    assignee: Optional[str] = None
    notes: Optional[str] = None


class RopaGraphNodeOut(BaseModel):
    id: str
    label: str
    node_type: str
    regulation_code: Optional[str] = None


class RopaGraphEdgeOut(BaseModel):
    id: str
    source: str
    target: str
    edge_type: str


class RopaGraphOut(BaseModel):
    regulation_code: str
    nodes: list[RopaGraphNodeOut]
    edges: list[RopaGraphEdgeOut]


class IntegrationHealthOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_code: str
    relation_type: Optional[str] = None
    probe_type: str
    status: str
    score_pct: float
    latency_ms: Optional[int] = None
    last_error: Optional[str] = None
    checked_at: datetime


class IntegrationHealthListOut(BaseModel):
    items: list[IntegrationHealthOut]
    total: int
    healthy_count: int
    degraded_count: int
    down_count: int
    avg_score_pct: float


class TransferWizardStartIn(BaseModel):
    regulation_code: str = Field(..., min_length=2, max_length=16)


class TransferWizardStepIn(BaseModel):
    step: str
    destination_country: Optional[str] = Field(default=None, min_length=2, max_length=2)
    mechanism: Optional[str] = None
    processor_id: Optional[str] = None
    processing_activity_id: Optional[str] = None
    document_ref: Optional[str] = None
    adequacy_notes: Optional[str] = None


class TransferWizardSessionOut(BaseModel):
    id: str
    regulation_code: str
    current_step: str
    status: str
    destination_country: Optional[str] = None
    mechanism: Optional[str] = None
    processor_id: Optional[str] = None
    processing_activity_id: Optional[str] = None
    document_ref: Optional[str] = None
    adequacy_notes: Optional[str] = None
    steps_completed: list[str]
    transfer_record_id: Optional[str] = None
    next_step: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WebhookDispatchIn(BaseModel):
    regulation_code: str
    event_name: str
    payload: dict[str, Any] = Field(default_factory=dict)
    aggregate_id: Optional[str] = None
    dispatch_now: bool = True


class WebhookDeliveryOut(BaseModel):
    id: str
    webhook_id: str
    regulation_code: str
    event_name: str
    aggregate_id: Optional[str] = None
    payload: dict[str, Any]
    status: str
    attempt_count: int
    max_attempts: int
    last_status_code: Optional[int] = None
    last_response_body: Optional[str] = None
    last_attempt_at: Optional[datetime] = None
    next_attempt_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime


class WebhookDeliveryListOut(BaseModel):
    items: list[WebhookDeliveryOut]
    total: int


class WebhookProcessOut(BaseModel):
    processed: int
    delivered: int
    failed: int
    pending: int


class PlayerCertificationMirrorOut(BaseModel):
    id: str
    player_code: str
    certification_type: str
    status: str
    source: str
    external_id: Optional[str] = None
    issuer: Optional[str] = None
    evidence_url: Optional[str] = None
    scope_notes: Optional[str] = None
    synced_at: datetime


class PlayerCertificationMirrorListOut(BaseModel):
    items: list[PlayerCertificationMirrorOut]
    total: int


class GlobalOpsBridgeSummaryOut(BaseModel):
    privacy_ecosystem_players: int
    certifications_cached: int
    certifications_valid: int
    partner_readiness_rows: int
    readiness_preview: list[dict[str, Any]]
    bridge_status: str


class GlobalOpsSyncOut(BaseModel):
    synced: int
    source: str
    player_code: Optional[str] = None
