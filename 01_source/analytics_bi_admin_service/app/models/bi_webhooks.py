from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BiCapabilityWebhook(Base):
    __tablename__ = "bi_capability_webhooks"

    id = Column(String(36), primary_key=True)
    network_player_code = Column(String(48), nullable=False, index=True)
    capability_code = Column(String(40), nullable=False)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    event_types_json = Column(Text, nullable=False, default='["mart.refreshed","kpi.threshold"]')
    active = Column(Boolean, nullable=False, default=True)
    last_http_status = Column(Integer, nullable=True)
    last_delivered_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
