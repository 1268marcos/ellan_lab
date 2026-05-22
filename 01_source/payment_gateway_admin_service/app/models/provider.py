from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentProviderPartner(Base):
    """Adquirente / PSP gerenciado pelo admin (Stripe, Mercado Pago, etc.)."""

    __tablename__ = "payment_provider_partners"

    id = Column(String(36), primary_key=True)
    name = Column(String(128), nullable=False)
    code = Column(String(32), nullable=False, unique=True, index=True)
    provider_type = Column(String(30), nullable=False)
    region_code = Column(String(20), nullable=True)
    api_base_url = Column(String(500), nullable=True)
    credentials_secret_ref = Column(String(255), nullable=True)
    webhook_secret_ref = Column(String(255), nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    country = Column(String(2), nullable=False, default="BR")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentProviderWebhookEndpoint(Base):
    __tablename__ = "payment_provider_webhook_endpoints"

    id = Column(String(36), primary_key=True)
    provider_id = Column(String(36), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    events_json = Column(Text, nullable=False, default='["payment.*"]')
    api_version = Column(String(10), nullable=False, default="v1")
    retry_policy = Column(Text, nullable=False, default="{}")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentProviderApiKey(Base):
    __tablename__ = "payment_provider_api_keys"

    id = Column(String(36), primary_key=True)
    provider_id = Column(String(36), nullable=False, index=True)
    key_prefix = Column(String(16), nullable=False)
    key_hash = Column(String(128), nullable=False)
    label = Column(String(64), nullable=True)
    scopes_json = Column(Text, nullable=False, default='["payments:write"]')
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
