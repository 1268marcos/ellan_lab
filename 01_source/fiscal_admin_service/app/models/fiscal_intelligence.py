from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FiscalOpsInsight(Base):
    __tablename__ = "fiscal_ops_insights"

    id = Column(String(36), primary_key=True)
    entity_type = Column(String(32), nullable=False)
    entity_ref = Column(String(64), nullable=False)
    insight_type = Column(String(40), nullable=False)
    severity = Column(String(10), nullable=False, default="MEDIUM")
    title = Column(String(200), nullable=False)
    detail_json = Column(Text, nullable=False, default="{}")
    suggested_action = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class FiscalContingencyEvent(Base):
    __tablename__ = "fiscal_contingency_events"

    id = Column(String(36), primary_key=True)
    country = Column(String(5), nullable=False)
    region_code = Column(String(20), nullable=True)
    authority = Column(String(80), nullable=False)
    contingency_mode = Column(String(32), nullable=False)
    reason = Column(String(500), nullable=True)
    issuer_code = Column(String(32), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
