from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FiscalProviderHealthStatus(Base):
    __tablename__ = "fiscal_provider_health_status"

    __table_args__ = (
        Index("ix_fiscal_provider_health_country", "country"),
        Index("ix_fiscal_provider_health_checked_at", "checked_at"),
    )

    country: Mapped[str] = mapped_column(String(5), primary_key=True)
    provider_name: Mapped[str] = mapped_column(String(80), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="stub")
    enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    last_status: Mapped[str] = mapped_column(String(20), nullable=False, default="UNKNOWN")
    last_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
