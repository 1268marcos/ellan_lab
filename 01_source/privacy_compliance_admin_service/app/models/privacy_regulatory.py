from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacySubjectRight(Base):
    """Direitos do titular por marco (GDPR Art. 15–22, LGPD Art. 18, CCPA §1798.100+)."""

    __tablename__ = "privacy_subject_rights"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    right_code = Column(String(32), nullable=False)
    name = Column(String(128), nullable=False)
    article_ref = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    response_sla_days = Column(String(8), nullable=True)
    dsar_type = Column(String(24), nullable=True, index=True)
    automated_available = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyRegulatoryObligation(Base):
    """Obrigações contínuas: DPO, ROPA, Do Not Sell, ANPD, notice at collection."""

    __tablename__ = "privacy_regulatory_obligations"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    obligation_code = Column(String(32), nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(32), nullable=False, index=True)
    article_ref = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    compliance_status = Column(String(20), nullable=False, default="PENDING", index=True)
    evidence_url = Column(String(500), nullable=True)
    due_review_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyOptOutRecord(Base):
    """CCPA/CPRA — opt-out venda/compartilhamento, GPC, sensitive PI limit."""

    __tablename__ = "privacy_opt_out_records"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, default="CCPA", index=True)
    user_id = Column(String(128), nullable=True, index=True)
    guest_identifier = Column(String(128), nullable=True)
    opt_out_type = Column(String(32), nullable=False, index=True)
    signal_source = Column(String(24), nullable=False, default="WEB")
    gpc_signal = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class PrivacyLegitimateInterestAssessment(Base):
    """LIA — GDPR Art. 6(1)(f) / LGPD Art. 7, IX (interesse legítimo)."""

    __tablename__ = "privacy_lia_records"

    id = Column(String(36), primary_key=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    processing_activity_id = Column(String(36), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    purpose = Column(Text, nullable=False)
    balancing_test_summary = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="DRAFT", index=True)
    reviewer = Column(String(128), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    document_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
