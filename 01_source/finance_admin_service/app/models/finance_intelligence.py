from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text, UniqueConstraint

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FinanceEcosystemInsight(Base):
    __tablename__ = "finance_ecosystem_insights"
    __table_args__ = (UniqueConstraint("catalog_code", "insight_type", "title", name="uq_fei_insight"),)

    id = Column(String(36), primary_key=True)
    catalog_code = Column(String(48), nullable=False, index=True)
    insight_type = Column(String(40), nullable=False)
    severity = Column(String(10), nullable=False, default="MEDIUM")
    title = Column(String(200), nullable=False)
    detail_json = Column(Text, nullable=False, default="{}")
    suggested_action = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class FinancePlayerBenchmark(Base):
    __tablename__ = "finance_player_benchmarks"

    catalog_code = Column(String(48), primary_key=True)
    segment_code = Column(String(40), nullable=False, index=True)
    readiness_score = Column(Integer, nullable=False, default=0)
    readiness_rank = Column(Integer, nullable=True)
    readiness_percentile = Column(Numeric(5, 2), nullable=True)
    relation_count = Column(Integer, nullable=False, default=0)
    capability_count = Column(Integer, nullable=False, default=0)
    coverage_count = Column(Integer, nullable=False, default=0)
    estimated_locker_count = Column(Integer, nullable=True)
    integration_status = Column(String(20), nullable=True)
    composite_score = Column(Integer, nullable=False, default=0)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FinanceIntegrationHealthCheck(Base):
    __tablename__ = "finance_integration_health_checks"
    __table_args__ = (UniqueConstraint("catalog_code", "check_type", name="uq_fihc_catalog_check"),)

    id = Column(String(36), primary_key=True)
    catalog_code = Column(String(48), nullable=False, index=True)
    check_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="UNKNOWN")
    latency_ms = Column(Integer, nullable=True)
    http_status = Column(Integer, nullable=True)
    message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
