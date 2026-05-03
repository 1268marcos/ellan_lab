"""Fila de auditoria para sincronização runtime (SQLite) → Postgres central."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.db import Base


class RuntimeSyncQueue(Base):
    """
    Cada execução de sync por locker gera um registro para trilha operacional
    (PENDING → PROCESSING → SUCCESS | FAILED).
    """

    __tablename__ = "runtime_sync_queue"

    id = Column(String(36), primary_key=True)
    locker_id = Column(String(64), nullable=False, index=True)
    operation = Column(String(32), nullable=False)  # SYNC_SLOTS | WEBHOOK_SLOT_STATE | SYNC_DOOR_STATE | SYNC_FEATURES
    status = Column(String(20), nullable=False, index=True)  # PENDING | PROCESSING | SUCCESS | FAILED | WEBHOOK_TRIGGERED
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
