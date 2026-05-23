from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinanceEcosystemSegment(Base):
    __tablename__ = "finance_ecosystem_segments"

    code = Column(String(40), primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=100)


class FinancePlayerCapability(Base):
    __tablename__ = "finance_player_capabilities"
    __table_args__ = (UniqueConstraint("catalog_code", "capability_code", name="uq_fpc_catalog_cap"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    catalog_code = Column(String(48), nullable=False, index=True)
    capability_code = Column(String(40), nullable=False)
    protocol = Column(String(20), nullable=False, default="REST")
    direction = Column(String(10), nullable=False, default="OUTBOUND")


class FinancePlayerRelation(Base):
    __tablename__ = "finance_player_relations"
    __table_args__ = (
        UniqueConstraint("from_catalog_code", "to_catalog_code", "relation_type", name="uq_fpr_relation"),
    )

    id = Column(String(36), primary_key=True)
    from_catalog_code = Column(String(48), nullable=False, index=True)
    to_catalog_code = Column(String(48), nullable=False, index=True)
    relation_type = Column(String(40), nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
