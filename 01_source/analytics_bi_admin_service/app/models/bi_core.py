from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AnalyticsFact(Base):
    __tablename__ = "analytics_facts"

    id = Column(UUID(as_uuid=True), primary_key=True)
    fact_key = Column(String(200), nullable=False, unique=True)
    fact_name = Column(String(150), nullable=False)
    order_id = Column(String(100), nullable=False, index=True)
    order_channel = Column(String(50), nullable=True)
    region_code = Column(String(20), nullable=True)
    slot_id = Column(String(100), nullable=True)
    payload = Column(JSONB().with_variant(Text, "sqlite"), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class BiKpiDefinition(Base):
    __tablename__ = "bi_kpi_definitions"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    domain = Column(String(32), nullable=False, default="LOCKER")
    grain = Column(String(24), nullable=False, default="DAILY")
    source_table = Column(String(80), nullable=False)
    formula_hint = Column(Text, nullable=True)
    owner_team = Column(String(64), nullable=False, default="data-platform")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class BiReportCatalog(Base):
    __tablename__ = "bi_report_catalog"

    id = Column(String(36), primary_key=True)
    code = Column(String(48), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    report_type = Column(String(24), nullable=False, default="DASHBOARD")
    metabase_dashboard_id = Column(String(36), nullable=True)
    description = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=False, default='["ops","locker"]')
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
