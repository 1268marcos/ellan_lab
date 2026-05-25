from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HardwareEcosystemPlayer(Base):
    """Registro mundial de players locker — liga hardware ↔ marketplace ↔ ML ↔ finance ↔ payment."""

    __tablename__ = "hardware_ecosystem_players"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(48), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    segment = Column(String(32), nullable=False)
    parent_group = Column(String(32), nullable=False, default="LOCKER_NETWORK", index=True)
    integration_mode = Column(String(32), nullable=False, default="DIRECT_API")
    supports_lockers = Column(Boolean, nullable=False, default=True)
    supports_marketplace = Column(Boolean, nullable=False, default=False)
    supports_food_delivery = Column(Boolean, nullable=False, default=False)
    supports_aggregation = Column(Boolean, nullable=False, default=False)
    primary_country = Column(String(2), nullable=False)
    vendor_id = Column(String(36), nullable=True, index=True)
    operator_id = Column(String(64), nullable=True, index=True)
    marketplace_channel_code = Column(String(48), nullable=True, index=True)
    ml_network_code = Column(String(48), nullable=True, index=True)
    payment_provider_code = Column(String(32), nullable=True)
    finance_catalog_code = Column(String(48), nullable=True)
    fiscal_corridor_code = Column(String(48), nullable=True)
    carrier_code = Column(String(32), nullable=True)
    regions_json = Column(JSON, nullable=False, default=list)
    metadata_json = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class HardwareLockerMarketplaceLink(Base):
    __tablename__ = "hardware_locker_marketplace_links"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    seller_name = Column(String(128), nullable=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    channel_code = Column(String(48), nullable=False)
    channel_name = Column(String(128), nullable=True)
    locker_id = Column(String(120), nullable=True, index=True)
    vendor_id = Column(String(36), nullable=True, index=True)
    priority = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareLockerPaymentBinding(Base):
    __tablename__ = "hardware_locker_payment_bindings"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    payment_method_code = Column(String(80), nullable=False)
    payment_provider_code = Column(String(32), nullable=True)
    payment_interface_code = Column(String(80), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class HardwareLockerCarrierBinding(Base):
    __tablename__ = "hardware_locker_carrier_bindings"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    carrier_code = Column(String(32), nullable=False, index=True)
    carrier_name = Column(String(128), nullable=False)
    service_level = Column(String(32), nullable=False, default="STANDARD")
    country_code = Column(String(2), nullable=False)
    operator_id = Column(String(64), nullable=True, index=True)
    tracking_prefix = Column(String(16), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareDomainReference(Base):
    """Ponte genérica: hardware locker ↔ outro domínio (PARTNER, ORDER_PICKUP, RUNTIME, FISCAL…)."""

    __tablename__ = "hardware_domain_references"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    domain_type = Column(String(32), nullable=False, index=True)
    external_id = Column(String(120), nullable=False)
    external_code = Column(String(64), nullable=True)
    relation_type = Column(String(32), nullable=False, default="LINK")
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
