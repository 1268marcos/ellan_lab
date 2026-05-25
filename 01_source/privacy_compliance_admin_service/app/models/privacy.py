from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyRegulation(Base):
    __tablename__ = "privacy_regulations"

    id = Column(String(36), primary_key=True)
    code = Column(String(16), nullable=False, unique=True, index=True)
    name = Column(String(128), nullable=False)
    jurisdiction = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    dpo_email = Column(String(255), nullable=True)
    supervisory_authority = Column(String(255), nullable=True)
    default_retention_days = Column(Integer, nullable=False, default=365)
    response_sla_days = Column(Integer, nullable=False, default=30)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyPolicyVersion(Base):
    __tablename__ = "privacy_policy_versions"

    id = Column(String(36), primary_key=True)
    regulation_id = Column(String(36), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    title = Column(String(255), nullable=False)
    content_url = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    effective_at = Column(DateTime(timezone=True), nullable=False)
    is_current = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyConsent(Base):
    __tablename__ = "privacy_consents"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=True, index=True)
    guest_identifier = Column(String(255), nullable=True, index=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False, index=True)
    granted = Column(Boolean, nullable=False)
    channel = Column(String(20), nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(500), nullable=True)
    policy_version = Column(String(20), nullable=True)
    granted_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    recorded_by_service = Column(String(64), nullable=True)
    access_policy_version = Column(Integer, nullable=False, default=1)


class DataDeletionRequest(Base):
    __tablename__ = "data_deletion_requests"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True, default="GDPR")
    user_id = Column(String(36), nullable=True, index=True)
    requested_by = Column(String(255), nullable=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    reason = Column(String(255), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class DataSubjectRequest(Base):
    __tablename__ = "data_subject_requests"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    user_id = Column(String(36), nullable=True, index=True)
    guest_identifier = Column(String(255), nullable=True)
    request_type = Column(String(32), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    requested_by = Column(String(255), nullable=True)
    details = Column(Text, nullable=True)
    response_notes = Column(Text, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyWebhookEndpoint(Base):
    __tablename__ = "privacy_webhook_endpoints"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    events_json = Column(Text, nullable=False, default="[]")
    secret_ref = Column(String(255), nullable=True)
    signing_algo = Column(String(20), nullable=False, default="HMAC_SHA256")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyApiKey(Base):
    __tablename__ = "privacy_api_keys"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default="[]")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
