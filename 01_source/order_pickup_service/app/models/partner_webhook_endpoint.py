from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Index, String, Text

from app.core.db import Base


class PartnerWebhookEndpoint(Base):
    __tablename__ = "partner_webhook_endpoints"

    __table_args__ = (
        Index("idx_pwe_partner", "partner_id", "partner_type"),
    )

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    url = Column(String(500), nullable=False)
    secret_hash = Column(String(128), nullable=False)
    secret_key = Column(String(256), nullable=True)
    events_json = Column(Text, nullable=False, default='["*"]')
    api_version = Column(String(10), nullable=False, default="v1")
    retry_policy = Column(Text, nullable=False, default='{"max_attempts":5,"backoff_sec":30}')
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
