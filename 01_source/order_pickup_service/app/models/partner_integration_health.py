from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, String

from app.core.db import Base


class PartnerIntegrationHealth(Base):
    __tablename__ = "partner_integration_health"

    __table_args__ = (
        Index("idx_pih_partner_time", "partner_id", "checked_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    partner_id = Column(String(36), nullable=False, index=True)
    partner_type = Column(String(20), nullable=False)
    endpoint_url = Column(String(500), nullable=True)
    checked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    status = Column(String(20), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    http_status = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
