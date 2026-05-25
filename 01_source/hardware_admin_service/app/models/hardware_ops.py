from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from sqlalchemy.types import JSON

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class HardwareSyncQueue(Base):
    __tablename__ = "hardware_sync_queue"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(64), nullable=False, index=True)
    operation = Column(String(32), nullable=False)
    status = Column(String(20), nullable=False)
    payload_json = Column(JSON, nullable=False, default=dict)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class HardwareTelemetryEvent(Base):
    __tablename__ = "hardware_telemetry_events"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(120), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    severity = Column(String(20), nullable=False, default="INFO")
    slot_number = Column(Integer, nullable=True)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at_epoch = Column(BigInteger, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
