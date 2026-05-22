from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MarketplaceReadinessScoreHistory(Base):
    __tablename__ = "marketplace_readiness_score_history"

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    partner_code = Column(String(48), nullable=False)
    score_total = Column(Numeric(5, 2), nullable=False)
    readiness_band = Column(String(16), nullable=False)
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class MarketplaceReadinessAlert(Base):
    __tablename__ = "marketplace_readiness_alerts"

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    partner_code = Column(String(48), nullable=False)
    alert_type = Column(String(32), nullable=False, default="SCORE_DROP")
    severity = Column(String(16), nullable=False, default="WARNING")
    previous_score = Column(Numeric(5, 2), nullable=True)
    new_score = Column(Numeric(5, 2), nullable=False)
    score_delta = Column(Numeric(5, 2), nullable=False)
    previous_band = Column(String(16), nullable=True)
    new_band = Column(String(16), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    webhook_dispatched = Column(Boolean, nullable=False, default=False)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)


class MarketplaceCapabilityWebhook(Base):
    __tablename__ = "marketplace_capability_webhooks"

    id = Column(String(36), primary_key=True)
    channel_partner_id = Column(String(36), nullable=False, index=True)
    partner_code = Column(String(48), nullable=False)
    capability_code = Column(String(40), nullable=False)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    event_types_json = Column(Text, nullable=False, default='["readiness.score_drop"]')
    active = Column(Boolean, nullable=False, default=True)
    last_http_status = Column(Integer, nullable=True)
    last_delivered_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class MarketplaceCapabilityWebhookDelivery(Base):
    __tablename__ = "marketplace_capability_webhook_deliveries"

    id = Column(String(36), primary_key=True)
    webhook_id = Column(String(36), nullable=False, index=True)
    event_type = Column(String(48), nullable=False)
    payload_json = Column(Text, nullable=False)
    http_status = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=False)
    response_snippet = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="DELIVERED")
    attempt_count = Column(Integer, nullable=False, default=1)
    dead_lettered_at = Column(DateTime(timezone=True), nullable=True)
    replay_of_delivery_id = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
