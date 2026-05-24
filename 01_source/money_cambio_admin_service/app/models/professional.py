from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MoneyOperatingCountry(Base):
    __tablename__ = "money_operating_country"

    id = Column(Integer, primary_key=True, autoincrement=True)
    country_code = Column(String(2), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    continent = Column(String(50), nullable=True)
    default_currency_code = Column(String(3), nullable=False)
    regulatory_zone = Column(String(20), nullable=False)
    primary_languages_json = Column(JsonType, nullable=False, default=list)
    locker_networks_json = Column(JsonType, nullable=False, default=list)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MoneyMethodCountryMatrix(Base):
    __tablename__ = "money_method_country_matrix"
    __table_args__ = (UniqueConstraint("country_code", "payment_method_code", name="uq_mmc_country_method"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    country_code = Column(String(2), nullable=False, index=True)
    payment_method_code = Column(String(80), nullable=False, index=True)
    min_amount_cents = Column(BigInteger, nullable=False, default=0)
    max_amount_cents = Column(BigInteger, nullable=True)
    is_instant_settlement = Column(Boolean, nullable=False, default=False)
    requires_kyc_above_cents = Column(BigInteger, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MoneyWalletCountryMatrix(Base):
    __tablename__ = "money_wallet_country_matrix"
    __table_args__ = (UniqueConstraint("country_code", "wallet_provider_code", name="uq_mwc_country_wallet"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    country_code = Column(String(2), nullable=False, index=True)
    wallet_provider_code = Column(String(80), nullable=False, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CambioPaymentCorridor(Base):
    __tablename__ = "cambio_payment_corridor"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(48), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    origin_country_code = Column(String(2), nullable=False, index=True)
    destination_country_code = Column(String(2), nullable=False, index=True)
    transaction_currency = Column(String(3), nullable=False)
    settlement_currency = Column(String(3), nullable=False)
    corridor_type = Column(String(24), nullable=False, default="CROSS_BORDER")
    default_spread_bps = Column(Integer, nullable=False, default=0)
    fx_partner_code = Column(String(32), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class CambioCorridorMarkup(Base):
    __tablename__ = "cambio_corridor_markup"

    id = Column(String(36), primary_key=True)
    corridor_id = Column(String(36), nullable=False, index=True)
    partner_code = Column(String(32), nullable=True)
    markup_bps = Column(Integer, nullable=False, default=0)
    valid_from = Column(Date, nullable=False)
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MoneyComplianceLimit(Base):
    __tablename__ = "money_compliance_limit"

    id = Column(String(36), primary_key=True)
    country_code = Column(String(2), nullable=False, index=True)
    currency_code = Column(String(3), nullable=False)
    limit_type = Column(String(32), nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    description = Column(String(255), nullable=True)
    regulatory_ref = Column(String(64), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MoneyLockerPlayerRegistry(Base):
    __tablename__ = "money_locker_player_registry"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(48), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    segment = Column(String(32), nullable=False, index=True)
    primary_country = Column(String(2), nullable=False)
    regions_json = Column(JsonType, nullable=False, default=list)
    default_settlement_currency = Column(String(3), nullable=False)
    finance_catalog_code = Column(String(48), nullable=True, index=True)
    fiscal_corridor_code = Column(String(48), nullable=True, index=True)
    cambio_corridor_code = Column(String(48), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MoneyEcosystemSegment(Base):
    __tablename__ = "money_ecosystem_segment"

    code = Column(String(32), primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)


class MoneyPlayerRelation(Base):
    __tablename__ = "money_player_relation"

    id = Column(String(36), primary_key=True)
    from_player_code = Column(String(48), nullable=False, index=True)
    to_player_code = Column(String(48), nullable=False, index=True)
    relation_type = Column(String(32), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class CambioFxRateAudit(Base):
    __tablename__ = "cambio_fx_rate_audit"

    id = Column(String(36), primary_key=True)
    base_currency = Column(String(8), nullable=False)
    quote_currency = Column(String(8), nullable=False)
    rate_date = Column(Date, nullable=False)
    old_rate = Column(Numeric(18, 8), nullable=True)
    new_rate = Column(Numeric(18, 8), nullable=False)
    source = Column(String(40), nullable=False)
    changed_by = Column(String(80), nullable=False, default="system")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
