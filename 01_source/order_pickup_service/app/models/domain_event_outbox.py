# 01_source/order_pickup_service/app/models/domain_event_outbox.py
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, String, Text
from sqlalchemy.dialects.sqlite import JSON
from app.core.db import Base


class DomainEventOutbox(Base):
    __tablename__ = "domain_event_outbox"

    __table_args__ = (
        Index("idx_domain_event_outbox_status_created_at", "status", "created_at"),
        Index("idx_domain_event_outbox_event_key", "event_key"),
    )

    id = Column(String, primary_key=True)
    event_key = Column(String(200), nullable=False, unique=True)

    aggregate_type = Column(String(100), nullable=False)
    aggregate_id = Column(String(100), nullable=False)

    event_name = Column(String(150), nullable=False)
    event_version = Column(String(20), nullable=False, default="1")

    status = Column(String(30), nullable=False, default="PENDING")
    payload_json = Column(JSON, nullable=False, default=dict)

    occurred_at = Column(DateTime, nullable=False)
    published_at = Column(DateTime, nullable=True)

    last_error = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
