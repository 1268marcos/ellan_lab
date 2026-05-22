from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerIntegrationCapabilityCatalog(Base):
    __tablename__ = "partner_integration_capability_catalog"

    code = Column(String(40), primary_key=True)
    name = Column(String(120), nullable=False)
    category = Column(String(32), nullable=False, default="CORE")
    default_protocol = Column(String(20), nullable=False, default="REST")
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)


class PartnerPlayerCapability(Base):
    __tablename__ = "partner_player_capabilities"
    __table_args__ = (UniqueConstraint("ecosystem_player_id", "capability_code", name="uq_partner_player_capability"),)

    id = Column(String(36), primary_key=True)
    ecosystem_player_id = Column(
        String(36), ForeignKey("partner_ecosystem_players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    capability_code = Column(String(40), ForeignKey("partner_integration_capability_catalog.code"), nullable=False)
    protocol = Column(String(20), nullable=False, default="REST")
    direction = Column(String(10), nullable=False, default="OUTBOUND")
    enabled = Column(Boolean, nullable=False, default=True)
    sandbox_ready = Column(Boolean, nullable=False, default=False)
    production_ready = Column(Boolean, nullable=False, default=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerPlayerRelation(Base):
    __tablename__ = "partner_player_relations"
    __table_args__ = (
        UniqueConstraint("from_player_id", "to_player_id", "relation_type", name="uq_partner_player_relation"),
    )

    id = Column(String(36), primary_key=True)
    from_player_id = Column(String(36), ForeignKey("partner_ecosystem_players.id", ondelete="CASCADE"), nullable=False)
    to_player_id = Column(String(36), ForeignKey("partner_ecosystem_players.id", ondelete="CASCADE"), nullable=False)
    relation_type = Column(String(32), nullable=False)
    strength = Column(String(16), nullable=False, default="PRIMARY")
    notes = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerMarketPresence(Base):
    __tablename__ = "partner_market_presence"
    __table_args__ = (
        UniqueConstraint("ecosystem_player_id", "country", "region_code", name="uq_partner_market_presence"),
    )

    id = Column(String(36), primary_key=True)
    ecosystem_player_id = Column(
        String(36), ForeignKey("partner_ecosystem_players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    country = Column(String(2), nullable=False)
    region_code = Column(String(16), nullable=True)
    service_level = Column(String(20), nullable=False, default="FULL")
    locker_density = Column(String(16), nullable=False, default="MEDIUM")
    active = Column(Boolean, nullable=False, default=True)
    launched_at = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
