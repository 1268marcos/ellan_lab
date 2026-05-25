from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HardwareIntegrationReadiness(Base):
    __tablename__ = "hardware_integration_readiness"

    player_id = Column(String(36), primary_key=True)
    player_code = Column(String(48), nullable=False, index=True)
    score_total = Column(Numeric(5, 2), nullable=False, default=0)
    score_capabilities = Column(Numeric(5, 2), nullable=False, default=0)
    score_api = Column(Numeric(5, 2), nullable=False, default=0)
    score_operations = Column(Numeric(5, 2), nullable=False, default=0)
    readiness_band = Column(String(16), nullable=False, default="PLANNED")
    blockers_json = Column(JSON, nullable=False, default=list)
    marketplace_partner_code = Column(String(48), nullable=True)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareReadinessAlert(Base):
    __tablename__ = "hardware_readiness_alerts"

    id = Column(String(36), primary_key=True)
    player_id = Column(String(36), nullable=False, index=True)
    player_code = Column(String(48), nullable=False)
    alert_type = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False, default="WARNING")
    previous_score = Column(Numeric(5, 2), nullable=True)
    new_score = Column(Numeric(5, 2), nullable=False)
    score_delta = Column(Numeric(5, 2), nullable=False, default=0)
    previous_band = Column(String(16), nullable=True)
    new_band = Column(String(16), nullable=False)
    status = Column(String(16), nullable=False, default="OPEN")
    webhook_dispatched = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareIntegrationIncident(Base):
    __tablename__ = "hardware_integration_incidents"

    id = Column(String(36), primary_key=True)
    player_id = Column(String(36), nullable=True, index=True)
    player_code = Column(String(48), nullable=True, index=True)
    locker_id = Column(String(120), nullable=True, index=True)
    severity = Column(String(16), nullable=False, default="WARNING")
    incident_type = Column(String(32), nullable=False)
    title = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    details_json = Column(JSON, nullable=False, default=dict)
    opened_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class HardwareSyncAuditLog(Base):
    __tablename__ = "hardware_sync_audit_log"

    id = Column(String(36), primary_key=True)
    event_type = Column(String(40), nullable=False)
    entity_type = Column(String(32), nullable=False)
    entity_id = Column(String(48), nullable=True)
    actor_id = Column(String(64), nullable=True)
    summary = Column(String(255), nullable=False)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwarePlayerCertification(Base):
    __tablename__ = "hardware_player_certifications"
    __table_args__ = (UniqueConstraint("player_id", "certification_type", name="uq_hw_player_cert"),)

    id = Column(String(36), primary_key=True)
    player_id = Column(String(36), nullable=False, index=True)
    player_code = Column(String(48), nullable=False, index=True)
    certification_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="VALID")
    source = Column(String(32), nullable=False, default="SEED")
    marketplace_cert_id = Column(String(36), nullable=True, index=True)
    issuer = Column(String(120), nullable=True)
    issued_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    evidence_url = Column(String(500), nullable=True)
    scope_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareLockerCorridor(Base):
    __tablename__ = "hardware_locker_corridors"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(64), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    origin_country = Column(String(2), nullable=False)
    dest_country = Column(String(2), nullable=False)
    handoff_type = Column(String(32), nullable=False, default="LOCKER_TO_PUDO")
    primary_player_id = Column(String(36), nullable=False)
    primary_player_code = Column(String(48), nullable=False)
    fallback_player_id = Column(String(36), nullable=True)
    fallback_player_code = Column(String(48), nullable=True)
    transit_hours_min = Column(Integer, nullable=False, default=4)
    transit_hours_max = Column(Integer, nullable=False, default=48)
    supports_returns = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareCorridorHandoffStep(Base):
    __tablename__ = "hardware_corridor_handoff_steps"
    __table_args__ = (UniqueConstraint("corridor_id", "step_order", name="uq_hw_corridor_step"),)

    id = Column(String(36), primary_key=True)
    corridor_id = Column(String(36), nullable=False, index=True)
    step_order = Column(Integer, nullable=False)
    player_id = Column(String(36), nullable=False)
    player_code = Column(String(48), nullable=False)
    step_role = Column(String(32), nullable=False, default="HANDOFF")
    locker_id = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)


class HardwareCorridorSla(Base):
    __tablename__ = "hardware_corridor_sla"

    id = Column(String(36), primary_key=True)
    corridor_id = Column(String(36), nullable=False, unique=True)
    corridor_code = Column(String(64), nullable=False, index=True)
    uptime_target_pct = Column(Numeric(5, 2), nullable=False, default=99.5)
    door_open_p95_ms = Column(Integer, nullable=False, default=2500)
    sync_lag_max_sec = Column(Integer, nullable=False, default=300)
    webhook_p95_latency_ms = Column(Integer, nullable=False, default=2000)
    compliance_status = Column(String(20), nullable=False, default="COMPLIANT")
    breach_count = Column(Integer, nullable=False, default=0)
    last_breach_at = Column(DateTime(timezone=True), nullable=True)
    measured_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareOnboardingPlaybook(Base):
    __tablename__ = "hardware_onboarding_playbooks"

    code = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False)
    segment_code = Column(String(32), nullable=False, index=True)
    version = Column(String(16), nullable=False, default="1.0")
    steps_json = Column(JSON, nullable=False, default=list)
    required_capabilities_json = Column(JSON, nullable=False, default=list)
    is_active = Column(Boolean, nullable=False, default=True)


class HardwareOnboardingRun(Base):
    __tablename__ = "hardware_onboarding_runs"

    id = Column(String(36), primary_key=True)
    subject_type = Column(String(16), nullable=False)
    subject_id = Column(String(120), nullable=False, index=True)
    playbook_code = Column(String(32), nullable=False)
    status = Column(String(20), nullable=False, default="IN_PROGRESS")
    current_step_order = Column(Integer, nullable=False, default=1)
    blockers_json = Column(JSON, nullable=False, default=list)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class HardwareOnboardingMilestone(Base):
    __tablename__ = "hardware_onboarding_milestones"

    id = Column(String(36), primary_key=True)
    run_id = Column(String(36), nullable=False, index=True)
    step_code = Column(String(40), nullable=False)
    step_order = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    evidence_json = Column(JSON, nullable=False, default=dict)
    completed_at = Column(DateTime(timezone=True), nullable=True)


class HardwareCapabilityWebhook(Base):
    __tablename__ = "hardware_capability_webhooks"
    __table_args__ = (UniqueConstraint("player_id", "capability_code", name="uq_hw_cap_webhook"),)

    id = Column(String(36), primary_key=True)
    player_id = Column(String(36), nullable=False, index=True)
    player_code = Column(String(48), nullable=False)
    capability_code = Column(String(40), nullable=False)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    event_types_json = Column(JSON, nullable=False, default=list)
    active = Column(Boolean, nullable=False, default=True)
    last_http_status = Column(Integer, nullable=True)
    last_delivered_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareCapabilityWebhookDelivery(Base):
    __tablename__ = "hardware_capability_webhook_deliveries"

    id = Column(String(36), primary_key=True)
    webhook_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(40), nullable=False)
    payload_json = Column(JSON, nullable=False, default=dict)
    http_status = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    response_snippet = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="FAILED")
    attempt_count = Column(Integer, nullable=False, default=1)
    dead_lettered_at = Column(DateTime(timezone=True), nullable=True)
    replay_of_delivery_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
