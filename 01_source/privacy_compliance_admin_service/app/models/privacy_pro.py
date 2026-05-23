from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyAuditEvent(Base):
    """Trilha imutável de ações administrativas (evidência DPO/regulador)."""

    __tablename__ = "privacy_audit_events"

    id = Column(String(36), primary_key=True)
    actor_id = Column(String(128), nullable=True, index=True)
    actor_role = Column(String(64), nullable=True)
    action = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_id = Column(String(64), nullable=True, index=True)
    regulation_code = Column(String(16), nullable=True, index=True)
    summary = Column(String(500), nullable=False)
    payload_json = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)


class PrivacyComplianceSnapshot(Base):
    """Score de maturidade compliance por marco regulatório."""

    __tablename__ = "privacy_compliance_snapshots"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    score_pct = Column(Float, nullable=False)
    grade = Column(String(2), nullable=False)
    gaps_json = Column(Text, nullable=False, default="[]")
    dimensions_json = Column(Text, nullable=False, default="{}")
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)


class PrivacyBreachTimelineEvent(Base):
    """Marcos regulatórios de incidente (72h GDPR, ANPD, notificação titulares)."""

    __tablename__ = "privacy_breach_timeline_events"

    id = Column(String(36), primary_key=True)
    breach_id = Column(String(36), ForeignKey("privacy_breach_incidents.id"), nullable=False, index=True)
    milestone = Column(String(32), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING")
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyDsrTask(Base):
    """Playbook automatizado por solicitação titular (DSAR)."""

    __tablename__ = "privacy_dsr_tasks"

    id = Column(String(36), primary_key=True)
    subject_request_id = Column(String(36), ForeignKey("data_subject_requests.id"), nullable=False, index=True)
    step_code = Column(String(32), nullable=False)
    step_order = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    assignee = Column(String(128), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyIntegrationHealthCheck(Base):
    """Saúde de integração ecosystem player (probe API/webhook)."""

    __tablename__ = "privacy_integration_health_checks"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(32), nullable=False, index=True)
    relation_type = Column(String(32), nullable=True)
    probe_type = Column(String(24), nullable=False, default="API")
    status = Column(String(16), nullable=False, default="HEALTHY", index=True)
    score_pct = Column(Float, nullable=False, default=100.0)
    latency_ms = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)


class PrivacyTransferWizardSession(Base):
    """Wizard step-by-step SCC/BCR/adequacy → privacy_transfer_records."""

    __tablename__ = "privacy_transfer_wizard_sessions"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    current_step = Column(String(24), nullable=False, default="SCOPE")
    status = Column(String(20), nullable=False, default="IN_PROGRESS", index=True)
    destination_country = Column(String(2), nullable=True)
    mechanism = Column(String(16), nullable=True)
    processor_id = Column(String(36), nullable=True)
    processing_activity_id = Column(String(36), nullable=True)
    document_ref = Column(String(500), nullable=True)
    adequacy_notes = Column(Text, nullable=True)
    steps_completed_json = Column(Text, nullable=False, default="[]")
    transfer_record_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyWebhookDelivery(Base):
    """Fila de entrega webhook privacy (DLQ + retries)."""

    __tablename__ = "privacy_webhook_deliveries"

    id = Column(String(36), primary_key=True)
    webhook_id = Column(String(36), ForeignKey("privacy_webhook_endpoints.id"), nullable=False, index=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    event_name = Column(String(64), nullable=False, index=True)
    aggregate_id = Column(String(64), nullable=True)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    last_status_code = Column(Integer, nullable=True)
    last_response_body = Column(Text, nullable=True)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyPlayerCertificationMirror(Base):
    """Cache/espelho certificações Partner global-ops ↔ ecosystem privacy."""

    __tablename__ = "privacy_player_certification_mirrors"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(32), nullable=False, index=True)
    certification_type = Column(String(32), nullable=False)
    status = Column(String(20), nullable=False, default="VALID")
    source = Column(String(24), nullable=False, default="PARTNER")
    external_id = Column(String(64), nullable=True)
    issuer = Column(String(128), nullable=True)
    evidence_url = Column(String(500), nullable=True)
    scope_notes = Column(Text, nullable=True)
    synced_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, index=True)
