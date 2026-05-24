from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FiscalJurisdiction(Base):
    __tablename__ = "fiscal_jurisdictions"

    country = Column(String(5), primary_key=True)
    name = Column(String(120), nullable=False)
    currency = Column(String(8), nullable=False)
    default_regime = Column(String(40), nullable=False)
    vat_label = Column(String(20), nullable=False, default="VAT")
    authority_name = Column(String(120), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FiscalDocumentTypeCatalog(Base):
    __tablename__ = "fiscal_document_type_catalog"

    id = Column(String(36), primary_key=True)
    code = Column(String(40), nullable=False, unique=True)
    name = Column(String(120), nullable=False)
    country = Column(String(5), nullable=False)
    family = Column(String(30), nullable=False)
    xml_schema = Column(String(80), nullable=True)
    requires_a1_cert = Column(Boolean, nullable=False, default=False)
    supports_contingency = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FiscalTaxCorridor(Base):
    __tablename__ = "fiscal_tax_corridors"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(48), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    origin_country = Column(String(5), nullable=False)
    dest_country = Column(String(5), nullable=False)
    primary_issuer_id = Column(String(36), nullable=False)
    primary_issuer_code = Column(String(32), nullable=False)
    fallback_issuer_id = Column(String(36), nullable=True)
    fallback_issuer_code = Column(String(32), nullable=True)
    document_type_code = Column(String(40), nullable=False)
    handoff_type = Column(String(32), nullable=False, default="LOCKER_EMISSION")
    service_level = Column(String(20), nullable=False, default="STANDARD")
    transit_hours_max = Column(Integer, nullable=False, default=72)
    supports_b2b = Column(Boolean, nullable=False, default=True)
    supports_b2c = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FiscalCorridorTaxRule(Base):
    __tablename__ = "fiscal_corridor_tax_rules"

    id = Column(String(36), primary_key=True)
    corridor_id = Column(String(36), nullable=False)
    rule_order = Column(Integer, nullable=False, default=1)
    tax_code = Column(String(20), nullable=False)
    rate_pct = Column(Numeric(7, 4), nullable=True)
    cfop = Column(String(5), nullable=True)
    ncm_pattern = Column(String(20), nullable=True)
    notes = Column(Text, nullable=True)


class FiscalIssuerJurisdictionGrant(Base):
    __tablename__ = "fiscal_issuer_jurisdiction_grants"

    id = Column(String(36), primary_key=True)
    issuer_id = Column(String(36), nullable=False)
    issuer_code = Column(String(32), nullable=False)
    country = Column(String(5), nullable=False)
    region_code = Column(String(20), nullable=True)
    document_type_code = Column(String(40), nullable=False)
    grant_status = Column(String(20), nullable=False, default="ACTIVE")
    valid_from = Column(Date, nullable=True)
    valid_to = Column(Date, nullable=True)
    cert_ref = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FiscalComplianceCertification(Base):
    __tablename__ = "fiscal_compliance_certifications"

    id = Column(String(36), primary_key=True)
    issuer_id = Column(String(36), nullable=False)
    issuer_code = Column(String(32), nullable=False)
    certification_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="VALID")
    issuer_authority = Column(String(120), nullable=True)
    issued_at = Column(Date, nullable=True)
    expires_at = Column(Date, nullable=True)
    evidence_url = Column(String(500), nullable=True)
    scope_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FiscalEmissionSloPolicy(Base):
    __tablename__ = "fiscal_emission_slo_policies"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(48), nullable=False)
    metric_name = Column(String(40), nullable=False)
    target_p99_ms = Column(Integer, nullable=False)
    target_success_rate_pct = Column(Numeric(5, 2), nullable=False, default=Decimal("99.50"))
    breach_credit_cents = Column(Integer, nullable=False, default=0)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FiscalIntegrationReadiness(Base):
    __tablename__ = "fiscal_integration_readiness"

    issuer_id = Column(String(36), primary_key=True)
    issuer_code = Column(String(32), nullable=False)
    country = Column(String(5), nullable=False)
    score_total = Column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    score_certificates = Column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    score_api = Column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    score_contingency = Column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    readiness_band = Column(String(1), nullable=False, default="D")
    blockers_json = Column(Text, nullable=False, default="[]")
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FiscalWebhookDeliveryLog(Base):
    __tablename__ = "fiscal_webhook_delivery_log"

    id = Column(String(36), primary_key=True)
    issuer_id = Column(String(36), nullable=False)
    event_type = Column(String(80), nullable=False)
    delivery_status = Column(String(20), nullable=False)
    http_status = Column(Integer, nullable=True)
    attempt = Column(Integer, nullable=False, default=1)
    payload_hash = Column(String(64), nullable=True)
    error_message = Column(String(500), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FiscalAutoClassificationRule(Base):
    __tablename__ = "fiscal_auto_classification_rules"

    id = Column(String(36), primary_key=True)
    sku_pattern = Column(String(80), nullable=False)
    category_code = Column(String(40), nullable=True)
    ncm_code = Column(String(10), nullable=False)
    icms_cst = Column(String(3), nullable=True)
    pis_cst = Column(String(2), nullable=True)
    cofins_cst = Column(String(2), nullable=True)
    cfop = Column(String(5), nullable=True)
    country = Column(String(5), nullable=False, default="BR")
    priority = Column(Integer, nullable=False, default=100)
    source = Column(String(20), nullable=False, default="MANUAL")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FiscalAutoClassificationLog(Base):
    __tablename__ = "fiscal_auto_classification_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(36), nullable=False)
    invoice_id = Column(String(50), nullable=True)
    sku_id = Column(String(255), nullable=False)
    ncm_applied = Column(String(10), nullable=True)
    icms_cst_applied = Column(String(3), nullable=True)
    pis_cst_applied = Column(String(2), nullable=True)
    cofins_cst_applied = Column(String(2), nullable=True)
    cfop_applied = Column(String(5), nullable=True)
    source = Column(String(20), nullable=False)
    classified_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
