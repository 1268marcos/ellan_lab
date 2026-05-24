from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinanceRelationType(Base):
    __tablename__ = "finance_relation_types"

    code = Column(String(40), primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)


class FinancePlayerAlias(Base):
    __tablename__ = "finance_player_aliases"

    alias_code = Column(String(48), primary_key=True)
    catalog_code = Column(String(48), nullable=False, index=True)
    source = Column(String(40), nullable=False, default="LEGACY")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FinancePlayerCountryCoverage(Base):
    __tablename__ = "finance_player_country_coverage"
    __table_args__ = (UniqueConstraint("catalog_code", "country_code", name="uq_fpcc_catalog_country"),)

    id = Column(String(36), primary_key=True)
    catalog_code = Column(String(48), nullable=False, index=True)
    country_code = Column(String(2), nullable=False)
    locker_service = Column(Boolean, nullable=False, default=False)
    pudo_service = Column(Boolean, nullable=False, default=False)
    marketplace_channel = Column(Boolean, nullable=False, default=False)
    food_pickup = Column(Boolean, nullable=False, default=False)


class FinanceIntegrationBlueprint(Base):
    __tablename__ = "finance_integration_blueprints"

    code = Column(String(40), primary_key=True)
    name = Column(String(160), nullable=False)
    target_segments_json = Column(Text, nullable=False, default="[]")
    auth_type = Column(String(30), nullable=False, default="API_KEY")
    primary_capability = Column(String(40), nullable=False)
    webhook_events_json = Column(Text, nullable=False, default="[]")
    reference_players_json = Column(Text, nullable=False, default="[]")
    docs_hint = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)
