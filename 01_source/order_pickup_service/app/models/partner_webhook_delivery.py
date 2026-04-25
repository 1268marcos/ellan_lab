from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.core.db import Base


class PartnerWebhookDelivery(Base):
    __tablename__ = "partner_webhook_deliveries"

    __table_args__ = (
        Index("idx_pwd_status_retry", "status", "next_retry_at"),
        Index("idx_pwd_endpoint", "endpoint_id"),
    )

    id = Column(String(36), primary_key=True)
    endpoint_id = Column(
        String(36),
        ForeignKey("partner_webhook_endpoints.id"),
        nullable=False,
        index=True,
    )
    event_id = Column(String(36), nullable=False)
    event_type = Column(String(80), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    payload_hash = Column(String(64), nullable=True)
    http_status = Column(Integer, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING")
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
