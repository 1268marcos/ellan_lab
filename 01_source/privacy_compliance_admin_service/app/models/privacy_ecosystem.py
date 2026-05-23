from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PrivacyEcosystemPlayer(Base):
    """Catálogo mundial de redes locker, carriers, marketplaces, PUDO, agregadores e food delivery."""

    __tablename__ = "privacy_ecosystem_players"

    id = Column(String(36), primary_key=True)
    code = Column(String(32), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    player_segment = Column(String(32), nullable=False, index=True)
    network_type = Column(String(32), nullable=False, default="LOCKER_NETWORK")
    region_group = Column(String(16), nullable=False, index=True)
    countries_json = Column(Text, nullable=False, default="[]")
    hardware_vendor = Column(String(128), nullable=True)
    global_player_code = Column(String(64), nullable=True, index=True)
    website_url = Column(String(500), nullable=True)
    privacy_contact_email = Column(String(255), nullable=True)
    rental_network_id = Column(String(36), nullable=True, index=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PrivacyPlayerRegulationLink(Base):
    """Vínculo player ↔ marco regulatório (GDPR, LGPD, CCPA, …)."""

    __tablename__ = "privacy_player_regulation_links"
    __table_args__ = (UniqueConstraint("player_id", "regulation_code", name="uq_player_regulation"),)

    id = Column(String(36), primary_key=True)
    player_id = Column(String(36), ForeignKey("privacy_ecosystem_players.id"), nullable=False, index=True)
    regulation_code = Column(String(16), nullable=False, index=True)
    privacy_role = Column(String(24), nullable=False, default="PROCESSOR")
    data_shared_json = Column(Text, nullable=False, default="[]")
    dpa_required = Column(Boolean, nullable=False, default=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PrivacyEcosystemRelation(Base):
    """Relações entre players: interconnect, routing marketplace, agregador, food handoff."""

    __tablename__ = "privacy_ecosystem_relations"
    __table_args__ = (UniqueConstraint("from_player_id", "to_player_id", "relation_type", name="uq_ecosystem_relation"),)

    id = Column(String(36), primary_key=True)
    from_player_id = Column(String(36), ForeignKey("privacy_ecosystem_players.id"), nullable=False, index=True)
    to_player_id = Column(String(36), ForeignKey("privacy_ecosystem_players.id"), nullable=False, index=True)
    relation_type = Column(String(32), nullable=False, index=True)
    integration_mode = Column(String(16), nullable=False, default="API")
    description = Column(Text, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
