from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MlInferenceUsageDaily(Base):
    __tablename__ = "ml_inference_usage_daily"

    id = Column(String(36), primary_key=True)
    usage_date = Column(Date, nullable=False, index=True)
    use_case_code = Column(String(48), nullable=False, index=True)
    network_player_code = Column(String(48), nullable=True)
    request_count = Column(BigInteger, nullable=False, default=0)
    p95_latency_ms = Column(Integer, nullable=True)
    error_rate_pct = Column(Numeric(6, 3), nullable=True)
    estimated_cost_usd = Column(Numeric(12, 4), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MlFeatureFreshnessBreach(Base):
    __tablename__ = "ml_feature_freshness_breaches"

    id = Column(String(36), primary_key=True)
    feature_name = Column(String(64), nullable=False, index=True)
    source_table = Column(String(120), nullable=False)
    sla_hours = Column(Integer, nullable=False, default=24)
    lag_hours = Column(Numeric(8, 2), nullable=False)
    severity = Column(String(16), nullable=False, default="WARNING")
    status = Column(String(20), nullable=False, default="OPEN")
    summary = Column(String(255), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class MlOpsRecommendation(Base):
    __tablename__ = "ml_ops_recommendations"

    id = Column(String(36), primary_key=True)
    recommendation_code = Column(String(48), nullable=False)
    category = Column(String(32), nullable=False, default="EFFICIENCY")
    priority = Column(String(16), nullable=False, default="MEDIUM")
    title = Column(String(160), nullable=False)
    action_hint = Column(Text, nullable=False)
    related_entity = Column(String(64), nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")
    impact_score = Column(Numeric(5, 2), nullable=False, default=50)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
