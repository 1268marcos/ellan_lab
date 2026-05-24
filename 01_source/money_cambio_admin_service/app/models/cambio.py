from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, Numeric, String

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CambioFxRate(Base):
    __tablename__ = "cambio_fx_rates"

    id = Column(String(36), primary_key=True)
    base_currency = Column(String(8), nullable=False, index=True)
    quote_currency = Column(String(8), nullable=False, index=True)
    rate_date = Column(Date, nullable=False)
    rate = Column(Numeric(18, 8), nullable=False)
    source = Column(String(40), nullable=False, default="MANUAL")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
