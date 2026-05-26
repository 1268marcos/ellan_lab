from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BiDataPartner(Base):
    __tablename__ = "bi_data_partners"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(32), nullable=False, unique=True)
    partner_type = Column(String(30), nullable=False, default="WAREHOUSE")
    region_code = Column(String(20), nullable=True)
    api_base_url = Column(String(500), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BiPartnerWebhookEndpoint(Base):
    __tablename__ = "bi_partner_webhook_endpoints"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    events_json = Column(Text, nullable=False, default='["fact.ingested","mart.refreshed"]')
    api_version = Column(String(10), nullable=False, default="v1")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BiPartnerApiKey(Base):
    __tablename__ = "bi_partner_api_keys"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default='["bi:read","bi:write","analytics:export"]')
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiApiKeyRotationLog(Base):
    __tablename__ = "bi_api_key_rotation_log"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    old_key_prefix = Column(String(16), nullable=True)
    new_key_prefix = Column(String(16), nullable=False)
    rotated_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
