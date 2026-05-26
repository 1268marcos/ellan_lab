from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Column, Date, DateTime, Numeric, String

from app.core.config import get_settings
from app.core.database import Base


def _mart_schema() -> str | None:
    url = get_settings().database_url
    if url.startswith("postgresql"):
        return "analytics_analytics"
    return None


class CompanyMrrTrend(Base):
    __tablename__ = "company_mrr_trend"
    __table_args__ = ({"schema": _mart_schema()} if _mart_schema() else {})

    month_ref = Column(Date, primary_key=True)
    currency = Column(String(8), primary_key=True, default="BRL")
    mrr_cents = Column(Numeric, nullable=True)
    company_deferred_cents = Column(Numeric, nullable=True)
    active_partner_count = Column(BigInteger, nullable=True)
    active_locker_count = Column(BigInteger, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)


class LockerPnl(Base):
    __tablename__ = "locker_pnl"
    __table_args__ = ({"schema": _mart_schema()} if _mart_schema() else {})

    month_ref = Column(Date, primary_key=True)
    partner_id = Column(String(36), primary_key=True)
    locker_id = Column(String(36), primary_key=True)
    currency = Column(String(8), primary_key=True, default="BRL")
    country_code = Column(String(2), nullable=True)
    jurisdiction_code = Column(String(32), nullable=True)
    revenue_cents = Column(BigInteger, nullable=True)
    opex_cents = Column(BigInteger, nullable=True)
    depreciation_cents = Column(BigInteger, nullable=True)
    gross_profit_cents = Column(BigInteger, nullable=True)
    gross_margin_pct = Column(Numeric(10, 4), nullable=True)
    ebitda_cents = Column(BigInteger, nullable=True)
    net_income_cents = Column(BigInteger, nullable=True)
    ar_open_cents = Column(BigInteger, nullable=True)
    dso_days = Column(Numeric(10, 2), nullable=True)
    computed_at = Column(DateTime(timezone=True), nullable=True)


class PartnerRevenueMonthly(Base):
    __tablename__ = "partner_revenue_monthly"
    __table_args__ = ({"schema": _mart_schema()} if _mart_schema() else {})

    month_ref = Column(Date, primary_key=True)
    partner_id = Column(String(36), primary_key=True)
    locker_id = Column(String(36), primary_key=True)
    currency = Column(String(8), primary_key=True, default="BRL")
    country_code = Column(String(2), nullable=True)
    jurisdiction_code = Column(String(32), nullable=True)
    revenue_recognized_cents = Column(Numeric, nullable=True)
    deferred_amount_cents = Column(Numeric, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
