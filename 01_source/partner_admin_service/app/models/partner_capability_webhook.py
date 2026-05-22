from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerCapabilityWebhook(Base):
    __tablename__ = "partner_capability_webhooks"

    id = Column(String(36), primary_key=True)
    ecosystem_player_id = Column(
        String(36), ForeignKey("partner_ecosystem_players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    player_code = Column(String(48), nullable=False, index=True)
    capability_code = Column(String(40), nullable=False)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    event_types_json = Column(Text, nullable=False, default='["capability.health","webhook.test"]')
    source = Column(String(32), nullable=False, default="SEED")
    marketplace_webhook_id = Column(String(36), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    last_http_status = Column(Integer, nullable=True)
    last_delivered_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PartnerCapabilityWebhookDelivery(Base):
    __tablename__ = "partner_capability_webhook_deliveries"

    id = Column(String(36), primary_key=True)
    webhook_id = Column(String(36), ForeignKey("partner_capability_webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
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
