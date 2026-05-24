from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FiscalIssuerPartner(Base):
    __tablename__ = "fiscal_issuer_partners"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(32), nullable=False, unique=True)
    issuer_type = Column(String(40), nullable=False, default="SEFAZ")
    country = Column(String(5), nullable=False, default="BR")
    region_code = Column(String(20), nullable=True)
    api_base_url = Column(String(500), nullable=True)
    credentials_secret_ref = Column(String(255), nullable=True)
    webhook_secret_ref = Column(String(255), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FiscalIssuerWebhookEndpoint(Base):
    __tablename__ = "fiscal_issuer_webhook_endpoints"

    id = Column(String(36), primary_key=True)
    issuer_id = Column(String(36), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    events_json = Column(Text, nullable=False, default='["fiscal.document.*"]')
    api_version = Column(String(10), nullable=False, default="v1")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FiscalIssuerApiKey(Base):
    __tablename__ = "fiscal_issuer_api_keys"

    id = Column(String(36), primary_key=True)
    issuer_id = Column(String(36), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default='["fiscal:read","fiscal:write"]')
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
