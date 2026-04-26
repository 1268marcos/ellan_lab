from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Index, Integer, Numeric, String

from app.core.db import Base


class PartnerPerformanceMetric(Base):
    __tablename__ = "partner_performance_metrics"

    __table_args__ = (
        Index("idx_ppm_partner_month", "partner_id", "period_month"),
    )

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    period_month = Column(String(7), nullable=False)
    total_orders = Column(Integer, nullable=False, default=0)
    on_time_pickup_pct = Column(Numeric(5, 2), nullable=True)
    return_rate_pct = Column(Numeric(5, 2), nullable=True)
    avg_pickup_hours = Column(Numeric(6, 2), nullable=True)
    sla_compliance_pct = Column(Numeric(5, 2), nullable=True)
    webhook_success_rate = Column(Numeric(5, 2), nullable=True)
    generated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
