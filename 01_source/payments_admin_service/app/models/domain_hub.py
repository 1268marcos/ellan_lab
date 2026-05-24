from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON

from app.core.database import Base

JsonType = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PaymentDomainRegistry(Base):
    __tablename__ = "payment_domain_registry"

    code = Column(String(40), primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(Text, nullable=True)
    ops_base_path = Column(String(255), nullable=True)
    api_service_name = Column(String(80), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentExternalReference(Base):
    __tablename__ = "payment_external_reference"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=True, index=True)
    payment_entity_type = Column(String(40), nullable=False)
    payment_entity_id = Column(String(64), nullable=False)
    external_domain = Column(String(40), nullable=False, index=True)
    external_entity_type = Column(String(60), nullable=False)
    external_entity_id = Column(String(120), nullable=False)
    link_role = Column(String(40), nullable=False, default="PRIMARY")
    sync_status = Column(String(20), nullable=False, default="LINKED")
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentDomainObligation(Base):
    __tablename__ = "payment_domain_obligation"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    domain_code = Column(String(40), nullable=False)
    obligation_type = Column(String(60), nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    priority = Column(Integer, nullable=False, default=50)
    blocking_payment = Column(Boolean, nullable=False, default=False)
    due_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    external_ref_id = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)
    metadata_json = Column(JsonType, nullable=False, default=dict)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PaymentCrossDomainEvent(Base):
    __tablename__ = "payment_cross_domain_event"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(80), nullable=False)
    source_domain = Column(String(40), nullable=False, default="PAYMENT")
    target_domains_json = Column(JsonType, nullable=False, default=list)
    payload_json = Column(JsonType, nullable=False, default=dict)
    status = Column(String(20), nullable=False, default="PENDING")
    published_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
