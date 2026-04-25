from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint

from app.core.db import Base


class LogisticsTrackingEvent(Base):
    __tablename__ = "logistics_tracking_events"

    __table_args__ = (
        Index("idx_lte_delivery_time", "delivery_id", "occurred_at"),
        Index("idx_lte_source_ref", "source", "source_ref"),
    )

    id = Column(String(36), primary_key=True)
    delivery_id = Column(String(36), ForeignKey("inbound_deliveries.id"), nullable=False, index=True)
    event_code = Column(String(40), nullable=False)
    event_label = Column(String(120), nullable=False)
    raw_status = Column(String(80), nullable=True)
    location_city = Column(String(80), nullable=True)
    location_state = Column(String(80), nullable=True)
    location_country = Column(String(2), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    source = Column(String(40), nullable=False, default="CARRIER_WEBHOOK")
    source_ref = Column(String(128), nullable=True)
    payload_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class LogisticsDeliveryAttempt(Base):
    __tablename__ = "logistics_delivery_attempts"

    __table_args__ = (
        UniqueConstraint("delivery_id", "attempt_number", name="ux_lda_delivery_attempt"),
        Index("idx_lda_delivery_time", "delivery_id", "attempted_at"),
    )

    id = Column(String(36), primary_key=True)
    delivery_id = Column(String(36), ForeignKey("inbound_deliveries.id"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)
    attempted_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    failure_reason = Column(String(160), nullable=True)
    carrier_note = Column(Text, nullable=True)
    carrier_agent = Column(String(128), nullable=True)
    proof_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class LogisticsShipmentLabel(Base):
    __tablename__ = "logistics_shipment_labels"

    __table_args__ = (
        UniqueConstraint("tracking_code", name="ux_lsl_tracking_code"),
        Index("idx_lsl_delivery", "delivery_id", "created_at"),
    )

    id = Column(String(36), primary_key=True)
    delivery_id = Column(String(36), ForeignKey("inbound_deliveries.id"), nullable=False, index=True)
    carrier_code = Column(String(20), nullable=False)
    tracking_code = Column(String(128), nullable=False)
    label_format = Column(String(10), nullable=False, default="PDF")
    label_url = Column(String(500), nullable=True)
    label_payload = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="GENERATED")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)


class LogisticsCarrierAuthConfig(Base):
    __tablename__ = "logistics_carrier_auth_config"

    __table_args__ = (
        UniqueConstraint("carrier_code", name="ux_lcac_carrier_code"),
    )

    id = Column(String(36), primary_key=True)
    carrier_code = Column(String(20), nullable=False)
    signature_header = Column(String(64), nullable=False, default="X-Carrier-Signature")
    algorithm = Column(String(20), nullable=False, default="HMAC_SHA256")
    secret_key = Column(String(256), nullable=True)
    required = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class LogisticsCarrierStatusMap(Base):
    __tablename__ = "logistics_carrier_status_map"

    __table_args__ = (
        UniqueConstraint("carrier_code", "raw_status", name="ux_lcsm_carrier_raw_status"),
        Index("idx_lcsm_carrier", "carrier_code", "active"),
    )

    id = Column(String(36), primary_key=True)
    carrier_code = Column(String(20), nullable=False)
    raw_status = Column(String(80), nullable=False)
    normalized_event_code = Column(String(40), nullable=False)
    normalized_event_label = Column(String(120), nullable=False)
    normalized_outcome = Column(String(20), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
