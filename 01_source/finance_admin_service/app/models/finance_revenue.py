from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PartnerRevenueSchedule(Base):
    __tablename__ = "partner_revenue_schedules"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    source_type = Column(String(40), nullable=False)
    source_id = Column(String(60), nullable=False, index=True)
    total_cents = Column(BigInteger, nullable=False)
    recognized_cents = Column(BigInteger, nullable=False, default=0)
    deferred_cents = Column(BigInteger, nullable=False)
    recognition_method = Column(String(30), nullable=False, default="STRAIGHT_LINE")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(20), nullable=False, default="ACTIVE")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerRevenueRecognitionEntry(Base):
    __tablename__ = "partner_revenue_recognition_entries"

    id = Column(String(36), primary_key=True)
    schedule_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False, index=True)
    recognition_date = Column(Date, nullable=False)
    amount_cents = Column(BigInteger, nullable=False)
    entry_status = Column(String(20), nullable=False, default="RECOGNIZED")
    fiscal_synced = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FinanceScheduledJobRun(Base):
    __tablename__ = "finance_scheduled_job_runs"

    id = Column(String(36), primary_key=True)
    job_code = Column(String(40), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="RUNNING")
    result_json = Column(Text, nullable=False, default="{}")
    error_message = Column(Text, nullable=True)
