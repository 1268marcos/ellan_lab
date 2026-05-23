from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyLegalBasis(Base):
    __tablename__ = "privacy_legal_bases"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    code = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    article_ref = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    requires_consent = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyDataCategory(Base):
    __tablename__ = "privacy_data_categories"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    code = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    sensitivity = Column(String(16), nullable=False, default="NORMAL")
    description = Column(Text, nullable=True)
    special_category = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyProcessingActivity(Base):
    __tablename__ = "privacy_processing_activities"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    code = Column(String(32), nullable=False)
    name = Column(String(255), nullable=False)
    purpose = Column(Text, nullable=False)
    data_controller = Column(String(255), nullable=True)
    legal_basis_id = Column(String(36), nullable=True, index=True)
    data_categories_json = Column(Text, nullable=False, default="[]")
    recipients_json = Column(Text, nullable=False, default="[]")
    retention_days = Column(Integer, nullable=True)
    cross_border = Column(Boolean, nullable=False, default=False)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyProcessor(Base):
    __tablename__ = "privacy_processors"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    processor_type = Column(String(32), nullable=False, default="SUB_PROCESSOR")
    country = Column(String(2), nullable=True)
    contact_email = Column(String(255), nullable=True)
    services_json = Column(Text, nullable=False, default="[]")
    regulation_codes_json = Column(Text, nullable=False, default="[]")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyProcessorAgreement(Base):
    __tablename__ = "privacy_processor_agreements"

    id = Column(String(36), primary_key=True)
    processor_id = Column(String(36), nullable=False, index=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    agreement_type = Column(String(16), nullable=False, default="DPA")
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    signed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    document_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyActivityProcessorLink(Base):
    __tablename__ = "privacy_activity_processor_links"

    id = Column(String(36), primary_key=True)
    processing_activity_id = Column(String(36), nullable=False, index=True)
    processor_id = Column(String(36), nullable=False, index=True)
    role = Column(String(24), nullable=False, default="SUB_PROCESSOR")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyRetentionRule(Base):
    __tablename__ = "privacy_retention_rules"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    data_category_id = Column(String(36), nullable=True, index=True)
    processing_activity_id = Column(String(36), nullable=True, index=True)
    retention_days = Column(Integer, nullable=False)
    purge_method = Column(String(32), nullable=False, default="ANONYMIZE")
    legal_basis_code = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyBreachIncident(Base):
    __tablename__ = "privacy_breach_incidents"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    severity = Column(String(16), nullable=False, default="MEDIUM", index=True)
    status = Column(String(20), nullable=False, default="OPEN", index=True)
    discovered_at = Column(DateTime(timezone=True), nullable=False)
    reported_at = Column(DateTime(timezone=True), nullable=True)
    affected_count = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    remediation = Column(Text, nullable=True)
    notification_required = Column(Boolean, nullable=False, default=False)
    supervisory_notified_at = Column(DateTime(timezone=True), nullable=True)
    subjects_notified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyImpactAssessment(Base):
    __tablename__ = "privacy_impact_assessments"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    processing_activity_id = Column(String(36), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    risk_level = Column(String(16), nullable=False, default="MEDIUM")
    status = Column(String(20), nullable=False, default="DRAFT", index=True)
    assessed_at = Column(DateTime(timezone=True), nullable=True)
    reviewer = Column(String(255), nullable=True)
    mitigation_summary = Column(Text, nullable=True)
    document_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyTransferRecord(Base):
    __tablename__ = "privacy_transfer_records"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    destination_country = Column(String(2), nullable=False)
    mechanism = Column(String(16), nullable=False, default="SCC")
    processor_id = Column(String(36), nullable=True, index=True)
    processing_activity_id = Column(String(36), nullable=True, index=True)
    status = Column(String(20), nullable=False, default="ACTIVE")
    document_ref = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
