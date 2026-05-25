from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HardwarePlayerSegmentCatalog(Base):
    """Taxonomia mundial: locker network, carrier, marketplace, food delivery, aggregator…"""

    __tablename__ = "hardware_player_segment_catalog"

    code = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False)
    parent_group = Column(String(32), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
    is_active = Column(Boolean, nullable=False, default=True)


class HardwarePlayerIntegrationCapability(Base):
    """Capability de integração por player (espelho marketplace_channel_capabilities)."""

    __tablename__ = "hardware_player_integration_capabilities"
    __table_args__ = (
        UniqueConstraint("player_id", "capability_code", "target_domain", name="uq_hw_player_cap_domain"),
    )

    id = Column(String(36), primary_key=True)
    player_id = Column(String(36), nullable=False, index=True)
    player_code = Column(String(48), nullable=False, index=True)
    capability_code = Column(String(40), nullable=False)
    protocol = Column(String(24), nullable=False)
    direction = Column(String(16), nullable=False)
    target_domain = Column(String(32), nullable=False, default="HARDWARE")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareEcosystemPlayerRelation(Base):
    """Relação entre players: opera rede, roteia via carrier, marketplace partner, hub aggregator."""

    __tablename__ = "hardware_ecosystem_player_relations"
    __table_args__ = (
        UniqueConstraint("from_player_id", "to_player_id", "relation_type", name="uq_hw_player_relation"),
    )

    id = Column(String(36), primary_key=True)
    from_player_id = Column(String(36), nullable=False, index=True)
    from_player_code = Column(String(48), nullable=False)
    to_player_id = Column(String(36), nullable=False, index=True)
    to_player_code = Column(String(48), nullable=False)
    relation_type = Column(String(32), nullable=False)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class HardwareLockerChannelBinding(Base):
    """Locker ↔ canal externo: FOOD_DELIVERY, AGGREGATOR, COLLECTION_POINT, MARKETPLACE, LOGISTICS_HUB."""

    __tablename__ = "hardware_locker_channel_bindings"
    __table_args__ = (
        UniqueConstraint("locker_id", "channel_type", "player_code", name="uq_hw_locker_channel"),
    )

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    channel_type = Column(String(32), nullable=False, index=True)
    player_id = Column(String(36), nullable=True, index=True)
    player_code = Column(String(48), nullable=False, index=True)
    player_name = Column(String(160), nullable=False)
    integration_mode = Column(String(32), nullable=False, default="DIRECT_API")
    priority = Column(Integer, nullable=False, default=100)
    metadata_json = Column(JSON, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
