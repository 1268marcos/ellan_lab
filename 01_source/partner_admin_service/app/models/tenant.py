from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TenantFiscalConfig(Base):
    __tablename__ = "tenant_fiscal_config"

    tenant_id = Column(String(100), primary_key=True)
    cnpj = Column(String(18), nullable=False)
    razao_social = Column(String(140), nullable=False)
    ie = Column(String(20), nullable=True)
    regime = Column(String(20), nullable=False)
    crt = Column(String(1), nullable=False)
    cert_a1_ref = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    brand_config = Column(JsonType, nullable=False, default=dict)


class CustomDomain(Base):
    __tablename__ = "custom_domains"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    verified = Column(Boolean, nullable=True, default=False)
    ssl_cert_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    verified_at = Column(DateTime(timezone=True), nullable=True)


class TenantPartnerLink(Base):
    __tablename__ = "tenant_partner_links"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(100), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False)
    partner_type = Column(String(20), nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
