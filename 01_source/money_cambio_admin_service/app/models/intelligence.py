from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text, UniqueConstraint

from app.core.database import Base
from app.models.professional import JsonType


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MoneyPlayerReadiness(Base):
    __tablename__ = "money_player_readiness"

    player_code = Column(String(48), primary_key=True)
    readiness_score = Column(Integer, nullable=False, default=0)
    grade = Column(String(1), nullable=False, default="F")
    fx_linked = Column(Boolean, nullable=False, default=False)
    fiscal_linked = Column(Boolean, nullable=False, default=False)
    compliance_ok = Column(Boolean, nullable=False, default=False)
    relation_count = Column(Integer, nullable=False, default=0)
    corridor_count = Column(Integer, nullable=False, default=0)
    detail_json = Column(JsonType, nullable=False, default=dict)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MoneyEcosystemInsight(Base):
    __tablename__ = "money_ecosystem_insight"

    id = Column(String(36), primary_key=True)
    player_code = Column(String(48), nullable=True, index=True)
    corridor_code = Column(String(48), nullable=True, index=True)
    insight_type = Column(String(40), nullable=False)
    severity = Column(String(12), nullable=False)
    title = Column(String(200), nullable=False)
    detail_json = Column(JsonType, nullable=False, default=dict)
    suggested_action = Column(Text, nullable=True)
    status = Column(String(16), nullable=False, default="OPEN")
    detected_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)


class MoneyFxAlertRule(Base):
    __tablename__ = "money_fx_alert_rule"

    id = Column(String(36), primary_key=True)
    name = Column(String(120), nullable=False)
    base_currency = Column(String(8), nullable=False)
    quote_currency = Column(String(8), nullable=False)
    threshold_bps = Column(Integer, nullable=False)
    direction = Column(String(8), nullable=False, default="BOTH")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MoneyFxAlertEvent(Base):
    __tablename__ = "money_fx_alert_event"

    id = Column(String(36), primary_key=True)
    rule_id = Column(String(36), nullable=False, index=True)
    base_currency = Column(String(8), nullable=False)
    quote_currency = Column(String(8), nullable=False)
    previous_rate = Column(Numeric(18, 8), nullable=True)
    current_rate = Column(Numeric(18, 8), nullable=False)
    change_bps = Column(Integer, nullable=False)
    status = Column(String(16), nullable=False, default="OPEN")
    triggered_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)


class MoneySettlementSchedule(Base):
    __tablename__ = "money_settlement_schedule"
    __table_args__ = (
        UniqueConstraint("scope_type", "scope_code", "country_code", name="uq_mss_scope"),
    )

    id = Column(String(36), primary_key=True)
    scope_type = Column(String(16), nullable=False)
    scope_code = Column(String(48), nullable=False)
    country_code = Column(String(2), nullable=False)
    settlement_currency = Column(String(3), nullable=False)
    settlement_days = Column(Integer, nullable=False, default=2)
    cut_off_time_utc = Column(String(8), nullable=False, default="17:00")
    weekend_policy = Column(String(24), nullable=False, default="SKIP_WEEKEND")
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
