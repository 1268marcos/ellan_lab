from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BiLockerNetworkPlayer(Base):
    __tablename__ = "bi_locker_network_players"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    player_role = Column(String(32), nullable=False, default="LOCKER_NETWORK")
    parent_group = Column(String(64), nullable=False, default="GLOBAL")
    country = Column(String(2), nullable=False, default="BR")
    regions_json = Column(Text, nullable=False, default='["BR"]')
    supports_lockers = Column(Boolean, nullable=False, default=True)
    supports_marketplace = Column(Boolean, nullable=False, default=False)
    integration_mode = Column(String(32), nullable=False, default="API")
    global_tier = Column(String(16), nullable=False, default="TIER1")
    bi_priority_score = Column(Numeric(5, 2), nullable=False, default=50)
    sort_order = Column(Integer, nullable=False, default=100)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BiPlayerRelation(Base):
    __tablename__ = "bi_player_relations"

    id = Column(String(36), primary_key=True)
    from_player_code = Column(String(48), nullable=False, index=True)
    to_player_code = Column(String(48), nullable=False, index=True)
    relation_type = Column(String(32), nullable=False, default="DATA_SHARE")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
