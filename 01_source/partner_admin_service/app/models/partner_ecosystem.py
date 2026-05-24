from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerEcosystemPlayer(Base):
    __tablename__ = "partner_ecosystem_players"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True, index=True)
    name = Column(String(160), nullable=False)
    player_role = Column(String(40), nullable=False)
    parent_group = Column(String(40), nullable=False, index=True)
    country = Column(String(2), nullable=False)
    regions_json = Column(Text, nullable=False, default="[]")
    supports_lockers = Column(Boolean, nullable=False, default=False)
    supports_marketplace = Column(Boolean, nullable=False, default=False)
    integration_mode = Column(String(40), nullable=False, default="DIRECT_API")
    marketplace_channel_id = Column(String(36), nullable=True)
    marketplace_channel_code = Column(String(48), nullable=True)
    locker_operator_ref = Column(String(48), nullable=True)
    ecommerce_partner_code = Column(String(48), nullable=True)
    api_docs_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    global_tier = Column(String(20), nullable=False, default="REGIONAL", index=True)
    integration_status = Column(String(16), nullable=False, default="PLANNED")
    website_url = Column(String(500), nullable=True)
    estimated_locker_count = Column(Integer, nullable=True)
    data_source = Column(String(32), nullable=False, default="CATALOG")
    finance_catalog_code = Column(String(48), nullable=True, index=True)
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerEcosystemLink(Base):
    __tablename__ = "partner_ecosystem_links"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    ecosystem_player_id = Column(String(36), ForeignKey("partner_ecosystem_players.id"), nullable=False)
    link_role = Column(String(40), nullable=False, default="CHANNEL")
    is_primary = Column(Boolean, nullable=False, default=False)
    integration_status = Column(String(30), nullable=False, default="PLANNED")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
