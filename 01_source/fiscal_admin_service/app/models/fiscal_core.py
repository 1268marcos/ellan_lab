from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FiscalDocument(Base):
    __tablename__ = "fiscal_documents"

    id = Column(String(80), primary_key=True)
    order_id = Column(String(80), nullable=False, index=True)
    receipt_code = Column(String(64), nullable=False)
    document_type = Column(String(50), nullable=False)
    channel = Column(String(20), nullable=True)
    region = Column(String(10), nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False, default="BRL")
    delivery_mode = Column(String(20), nullable=True)
    send_status = Column(String(50), nullable=True)
    send_target = Column(String(255), nullable=True)
    print_status = Column(String(50), nullable=True)
    payload_json = Column(Text, nullable=False, default="{}")
    issued_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    tenant_id = Column(String(64), nullable=True)
    attempt = Column(Integer, nullable=False, default=1)


class FiscalReconciliationGap(Base):
    __tablename__ = "fiscal_reconciliation_gaps"

    id = Column(String(60), primary_key=True)
    dedupe_key = Column(String(180), nullable=False)
    gap_type = Column(String(80), nullable=False)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    order_id = Column(String(100), nullable=True)
    invoice_id = Column(String(50), nullable=True)
    details_json = Column(JsonType, nullable=True)
    first_detected_at = Column(DateTime(timezone=True), nullable=False)
    last_detected_at = Column(DateTime(timezone=True), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class FiscalProviderHealthStatus(Base):
    __tablename__ = "fiscal_provider_health_status"

    country = Column(String(5), primary_key=True)
    provider_name = Column(String(80), nullable=False)
    mode = Column(String(20), nullable=False)
    enabled = Column(Boolean, nullable=False)
    base_url = Column(String(300), nullable=True)
    last_status = Column(String(20), nullable=False)
    last_http_status = Column(Integer, nullable=True)
    last_latency_ms = Column(Integer, nullable=True)
    last_error = Column(String(1000), nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False)


class FiscalAccountingApproval(Base):
    __tablename__ = "fiscal_accounting_approvals"

    id = Column(String(80), primary_key=True)
    owner = Column(String(160), nullable=False)
    eta = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(80), nullable=False)
    payload_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FiscalAuthorityCallback(Base):
    __tablename__ = "fiscal_authority_callbacks"

    id = Column(String(60), primary_key=True)
    invoice_id = Column(String(50), nullable=False)
    authority = Column(String(30), nullable=False)
    event_type = Column(String(80), nullable=True)
    status = Column(String(40), nullable=True)
    protocol_number = Column(String(120), nullable=True)
    raw_payload = Column(JsonType, nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=False)


class ProductFiscalConfig(Base):
    __tablename__ = "product_fiscal_config"

    sku_id = Column(String(255), primary_key=True)
    ncm_code = Column(String(10), nullable=True)
    cest = Column(String(9), nullable=True)
    icms_cst = Column(String(3), nullable=True)
    pis_cst = Column(String(2), nullable=True)
    cofins_cst = Column(String(2), nullable=True)
    iva_category = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    cfop = Column(String(5), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


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
    brand_config = Column(JsonType, nullable=True, default=dict)
