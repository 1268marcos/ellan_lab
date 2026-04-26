from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint

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


class LogisticsReturn(Base):
    __tablename__ = "logistics_returns"

    __table_args__ = (
        Index("idx_lr_partner_status_created", "partner_id", "status", "created_at"),
        Index("idx_lr_order_created", "order_id", "created_at"),
    )

    id = Column(String(36), primary_key=True)
    order_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False, index=True)
    reason_code = Column(String(40), nullable=False)
    status = Column(String(30), nullable=False, default="REQUESTED")
    notes = Column(Text, nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class LogisticsReturnEvent(Base):
    __tablename__ = "logistics_return_events"

    __table_args__ = (
        Index("idx_lre_return_occurred", "return_id", "occurred_at"),
    )

    id = Column(String(36), primary_key=True)
    return_id = Column(String(36), ForeignKey("logistics_returns.id"), nullable=False, index=True)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    reason = Column(String(200), nullable=True)
    changed_by = Column(String(36), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    __table_args__ = (
        Index("idx_rr_status_requested", "status", "requested_at"),
        Index("idx_rr_delivery_created", "original_delivery_id", "created_at"),
    )

    id = Column(String(36), primary_key=True)
    original_delivery_id = Column(String(36), ForeignKey("inbound_deliveries.id"), nullable=False, index=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=True, index=True)
    requester_type = Column(String(20), nullable=False)
    requester_id = Column(String(36), nullable=True)
    return_reason_code = Column(String(30), nullable=False, index=True)
    return_reason_detail = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    status = Column(String(30), nullable=False, default="REQUESTED")
    requested_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(String(36), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    close_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ReturnLeg(Base):
    __tablename__ = "return_legs"

    __table_args__ = (
        Index("idx_rl_return_status", "return_request_id", "status"),
    )

    id = Column(String(36), primary_key=True)
    return_request_id = Column(String(36), ForeignKey("return_requests.id"), nullable=False, index=True)
    logistics_partner_id = Column(String(36), ForeignKey("logistics_partners.id"), nullable=True)
    tracking_code = Column(String(128), nullable=True)
    label_id = Column(String(36), ForeignKey("logistics_shipment_labels.id"), nullable=True)
    from_locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=True)
    to_hub_address_json = Column(Text, nullable=True, default="{}")
    status = Column(String(20), nullable=False, default="PENDING")
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ReturnTrackingEvent(Base):
    __tablename__ = "return_tracking_events"

    __table_args__ = (
        Index("idx_rte_leg_time", "return_leg_id", "occurred_at"),
    )

    id = Column(String(36), primary_key=True)
    return_leg_id = Column(String(36), ForeignKey("return_legs.id"), nullable=False, index=True)
    event_code = Column(String(30), nullable=False)
    description = Column(String(255), nullable=True)
    location_name = Column(String(128), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    source = Column(String(20), nullable=False, default="CARRIER_WEBHOOK")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class ReturnReasonCatalog(Base):
    __tablename__ = "return_reasons_catalog"

    __table_args__ = (
        UniqueConstraint("code", name="ux_rrc_code"),
    )

    id = Column(String(36), primary_key=True)
    code = Column(String(30), nullable=False)
    label_pt = Column(String(128), nullable=False)
    label_en = Column(String(128), nullable=True)
    category = Column(String(30), nullable=True)
    requires_photo = Column(Boolean, nullable=False, default=False)
    requires_detail = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class SlaBreachEvent(Base):
    __tablename__ = "sla_breach_events"

    __table_args__ = (
        Index("idx_sbe_detected", "detected_at"),
        Index("idx_sbe_type_severity", "breach_type", "severity"),
    )

    id = Column(String(36), primary_key=True)
    delivery_id = Column(String(36), ForeignKey("inbound_deliveries.id"), nullable=True)
    return_request_id = Column(String(36), ForeignKey("return_requests.id"), nullable=True)
    logistics_partner_id = Column(String(36), ForeignKey("logistics_partners.id"), nullable=True)
    breach_type = Column(String(40), nullable=False)
    severity = Column(String(10), nullable=False)
    expected_at = Column(DateTime(timezone=True), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    notified_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
