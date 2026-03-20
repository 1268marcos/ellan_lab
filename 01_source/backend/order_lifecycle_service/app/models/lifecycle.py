# 01_source/backend/order_lifecycle_service/app/models/lifecycle.py
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DeadlineType(str, enum.Enum):
    PREPAYMENT_TIMEOUT = "PREPAYMENT_TIMEOUT"
    POSTPAYMENT_EXPIRY = "POSTPAYMENT_EXPIRY"


class DeadlineStatus(str, enum.Enum):
    PENDING = "PENDING"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class EventStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class LifecycleDeadline(Base):
    __tablename__ = "lifecycle_deadlines"
    __table_args__ = (
        UniqueConstraint("deadline_key", name="uq_lifecycle_deadlines_deadline_key"),
        Index("ix_lifecycle_deadlines_due_at_status", "due_at", "status"),
        Index("ix_lifecycle_deadlines_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deadline_key: Mapped[str] = mapped_column(String(200), nullable=False)
    order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    order_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deadline_type: Mapped[DeadlineType] = mapped_column(Enum(DeadlineType, name="deadline_type_enum"), nullable=False)
    status: Mapped[DeadlineStatus] = mapped_column(Enum(DeadlineStatus, name="deadline_status_enum"), nullable=False, default=DeadlineStatus.PENDING)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class DomainEvent(Base):
    __tablename__ = "domain_events"
    __table_args__ = (
        UniqueConstraint("event_key", name="uq_domain_events_event_key"),
        Index("ix_domain_events_aggregate_id", "aggregate_id"),
        Index("ix_domain_events_status_created_at", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_key: Mapped[str] = mapped_column(String(200), nullable=False)
    aggregate_type: Mapped[str] = mapped_column(String(100), nullable=False)
    aggregate_id: Mapped[str] = mapped_column(String(100), nullable=False)
    event_name: Mapped[str] = mapped_column(String(150), nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus, name="event_status_enum"), nullable=False, default=EventStatus.PENDING)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AnalyticsFact(Base):
    __tablename__ = "analytics_facts"
    __table_args__ = (
        UniqueConstraint("fact_key", name="uq_analytics_facts_fact_key"),
        Index("ix_analytics_facts_fact_name_occurred_at", "fact_name", "occurred_at"),
        Index("ix_analytics_facts_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fact_key: Mapped[str] = mapped_column(String(200), nullable=False)
    fact_name: Mapped[str] = mapped_column(String(150), nullable=False)
    order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    order_channel: Mapped[str | None] = mapped_column(String(50), nullable=True)
    region_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    slot_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)