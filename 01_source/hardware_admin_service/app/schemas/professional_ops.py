from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HardwareProfessionalOpsSummaryOut(BaseModel):
    readiness_rows: int
    avg_score: float
    bands: dict[str, int]
    open_incidents: int
    open_readiness_alerts: int
    partners_with_blockers: int
    certifications: int
    corridors: int
    corridor_sla_compliant: int
    onboarding_runs_active: int
    capability_webhooks: int
    webhook_deliveries_24h: int
    audit_log_entries: int


class HardwareIntegrationReadinessPersistedOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    player_id: str
    player_code: str
    score_total: float
    score_capabilities: float
    score_api: float
    score_operations: float
    readiness_band: str
    blockers_json: list[Any]
    marketplace_partner_code: str | None
    computed_at: datetime


class HardwareIntegrationReadinessListOut(BaseModel):
    items: list[HardwareIntegrationReadinessPersistedOut]
    total: int


class HardwareReadinessAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_id: str
    player_code: str
    alert_type: str
    severity: str
    previous_score: float | None
    new_score: float
    score_delta: float
    previous_band: str | None
    new_band: str
    status: str
    webhook_dispatched: bool
    created_at: datetime


class HardwareReadinessAlertListOut(BaseModel):
    items: list[HardwareReadinessAlertOut]
    total: int


class HardwareIntegrationIncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_id: str | None
    player_code: str | None
    locker_id: str | None
    severity: str
    incident_type: str
    title: str
    status: str
    details_json: dict[str, Any]
    opened_at: datetime
    resolved_at: datetime | None


class HardwareIntegrationIncidentListOut(BaseModel):
    items: list[HardwareIntegrationIncidentOut]
    total: int


class HardwareSyncAuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    event_type: str
    entity_type: str
    entity_id: str | None
    actor_id: str | None
    summary: str
    payload_json: dict[str, Any]
    created_at: datetime


class HardwareSyncAuditLogListOut(BaseModel):
    items: list[HardwareSyncAuditLogOut]
    total: int


class HardwarePlayerCertificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_id: str
    player_code: str
    certification_type: str
    status: str
    source: str = "SEED"
    marketplace_cert_id: str | None = None
    issuer: str | None
    issued_at: Any
    expires_at: Any
    evidence_url: str | None
    scope_notes: str | None


class HardwarePlayerCertificationListOut(BaseModel):
    items: list[HardwarePlayerCertificationOut]
    total: int


class HardwareLockerCorridorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corridor_code: str
    name: str
    origin_country: str
    dest_country: str
    handoff_type: str
    primary_player_code: str
    fallback_player_code: str | None
    transit_hours_min: int
    transit_hours_max: int
    supports_returns: bool
    active: bool
    priority: int
    notes: str | None


class HardwareCorridorHandoffStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corridor_id: str
    step_order: int
    player_code: str
    step_role: str
    locker_id: str | None
    notes: str | None


class HardwareCorridorSlaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    corridor_id: str
    corridor_code: str
    uptime_target_pct: float
    door_open_p95_ms: int
    sync_lag_max_sec: int
    webhook_p95_latency_ms: int
    compliance_status: str
    breach_count: int
    last_breach_at: datetime | None


class HardwareOnboardingPlaybookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    segment_code: str
    version: str
    steps_json: list[Any]
    required_capabilities_json: list[Any]
    is_active: bool


class HardwareOnboardingRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    subject_type: str
    subject_id: str
    playbook_code: str
    status: str
    current_step_order: int
    blockers_json: list[Any]
    started_at: datetime
    completed_at: datetime | None


class HardwareOnboardingMilestoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    run_id: str
    step_code: str
    step_order: int
    status: str
    evidence_json: dict[str, Any]
    completed_at: datetime | None


class HardwareCapabilityWebhookOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    player_id: str
    player_code: str
    capability_code: str
    url: str
    active: bool
    event_types_json: list[Any] = Field(default_factory=list)
    last_http_status: int | None
    last_delivered_at: datetime | None
    last_error: str | None


class HardwareCapabilityWebhookListOut(BaseModel):
    items: list[HardwareCapabilityWebhookOut]
    total: int


class HardwareCapabilityWebhookDeliveryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    webhook_id: str
    event_type: str
    http_status: int | None
    success: bool
    response_snippet: str | None
    status: str
    attempt_count: int
    replay_of_delivery_id: str | None
    created_at: datetime


class HardwareCapabilityWebhookDeliveryListOut(BaseModel):
    items: list[HardwareCapabilityWebhookDeliveryOut]
    total: int
