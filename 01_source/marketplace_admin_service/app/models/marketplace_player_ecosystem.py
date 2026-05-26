from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketplacePlayerSegment(Base):
    __tablename__ = "marketplace_player_segments"

    code = Column(String(32), primary_key=True)
    name = Column(String(128), nullable=False)
    parent_group = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    default_integration_mode = Column(String(32), nullable=False, default="DIRECT_API")
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceChannelPartnerSegment(Base):
    __tablename__ = "marketplace_channel_partner_segments"

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    segment_code = Column(String(32), nullable=False, index=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplacePlayerRelationship(Base):
    __tablename__ = "marketplace_player_relationships"

    id = Column(String(36), primary_key=True)
    from_partner_id = Column(String(36), nullable=False, index=True)
    to_partner_id = Column(String(36), nullable=False, index=True)
    relationship_type = Column(String(32), nullable=False)
    corridor_code = Column(String(48), nullable=True)
    notes = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceCorridor(Base):
    __tablename__ = "marketplace_corridors"

    code = Column(String(48), primary_key=True)
    name = Column(String(128), nullable=False)
    origin_country = Column(String(2), nullable=False)
    destination_country = Column(String(2), nullable=False)
    corridor_type = Column(String(24), nullable=False, default="DOMESTIC")
    currency = Column(String(8), nullable=False, default="EUR")
    active = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceCorridorPlayer(Base):
    __tablename__ = "marketplace_corridor_players"

    id = Column(String(36), primary_key=True)
    corridor_code = Column(String(48), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False)
    player_role_in_corridor = Column(String(32), nullable=False)
    priority = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class SellerPlayerIntegrationPlan(Base):
    __tablename__ = "seller_player_integration_plans"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False, index=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    integration_path = Column(String(32), nullable=False)
    status = Column(String(20), nullable=False, default="PLANNED")
    target_go_live = Column(Date, nullable=True)
    primary_capability = Column(String(40), nullable=True)
    via_partner_id = Column(String(36), nullable=True)
    corridor_code = Column(String(48), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
