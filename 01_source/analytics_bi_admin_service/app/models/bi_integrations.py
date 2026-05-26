from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BiPlayerIntegrationProfile(Base):
    __tablename__ = "bi_player_integration_profiles"

    id = Column(String(36), primary_key=True)
    network_player_code = Column(String(48), nullable=False, unique=True, index=True)
    segment_code = Column(String(32), nullable=False)
    integration_mode = Column(String(32), nullable=False, default="API")
    api_base_url = Column(String(500), nullable=True)
    auth_method = Column(String(32), nullable=False, default="API_KEY")
    webhook_support = Column(Boolean, nullable=False, default=False)
    bi_data_feed = Column(Boolean, nullable=False, default=True)
    ml_scoring_enabled = Column(Boolean, nullable=False, default=False)
    target_service = Column(String(48), nullable=False, default="analytics-bi-admin")
    docs_url = Column(String(500), nullable=True)
    status = Column(String(20), nullable=False, default="PLANNED")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BiPlayerCapabilityLink(Base):
    __tablename__ = "bi_player_capability_links"

    id = Column(String(36), primary_key=True)
    network_player_code = Column(String(48), nullable=False, index=True)
    capability_code = Column(String(40), nullable=False)
    capability_name = Column(String(120), nullable=True)
    protocol = Column(String(16), nullable=False, default="REST")
    direction = Column(String(16), nullable=False, default="OUTBOUND")
    production_ready = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiCrossDomainIntegration(Base):
    __tablename__ = "bi_cross_domain_integrations"

    id = Column(String(36), primary_key=True)
    source_player_code = Column(String(48), nullable=False, index=True)
    target_domain = Column(String(24), nullable=False)
    target_player_code = Column(String(48), nullable=True)
    integration_type = Column(String(32), nullable=False, default="DATA_SYNC")
    route_path = Column(String(255), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
