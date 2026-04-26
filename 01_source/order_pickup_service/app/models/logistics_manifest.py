from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Index, Integer, String, Text

from app.core.db import Base


class LogisticsManifest(Base):
    __tablename__ = "logistics_manifests"

    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','IN_TRANSIT','DELIVERED','PARTIAL','FAILED','CANCELLED')",
            name="ck_lm_status",
        ),
        Index("idx_lm_partner_date", "logistics_partner_id", "manifest_date"),
        Index("idx_lm_locker_status", "locker_id", "status", "manifest_date"),
    )

    id = Column(String(36), primary_key=True)
    logistics_partner_id = Column(String(36), ForeignKey("logistics_partners.id"), nullable=False, index=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    manifest_date = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    carrier_route_code = Column(String(64), nullable=True)
    carrier_vehicle_id = Column(String(64), nullable=True)
    expected_parcel_count = Column(Integer, nullable=False, default=0)
    actual_parcel_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING")
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    carrier_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class LogisticsManifestItem(Base):
    __tablename__ = "logistics_manifest_items"

    __table_args__ = (
        CheckConstraint("status IN ('EXPECTED','STORED','EXCEPTION','MISSING')", name="ck_lmi_status"),
        Index("idx_lmi_manifest", "manifest_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    manifest_id = Column(String(36), ForeignKey("logistics_manifests.id"), nullable=False)
    delivery_id = Column(String(36), ForeignKey("inbound_deliveries.id"), nullable=True)
    tracking_code = Column(String(128), nullable=False)
    sequence_number = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="EXPECTED")
    exception_note = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class LogisticsCapacityAllocation(Base):
    __tablename__ = "logistics_capacity_allocations"

    __table_args__ = (
        CheckConstraint("slot_size IN ('S','M','L','XL')", name="ck_lca_slot_size"),
        CheckConstraint("reserved_slots >= 0", name="ck_lca_reserved_slots_non_negative"),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="ck_lca_date_range"),
        Index("idx_lca_partner_locker_slot", "logistics_partner_id", "locker_id", "slot_size"),
        Index("idx_lca_active_window", "is_active", "valid_from", "valid_until"),
    )

    id = Column(String(36), primary_key=True)
    logistics_partner_id = Column(String(36), ForeignKey("logistics_partners.id"), nullable=False, index=True)
    locker_id = Column(String(64), ForeignKey("lockers.id"), nullable=False, index=True)
    slot_size = Column(String(8), nullable=False)
    reserved_slots = Column(Integer, nullable=False)
    valid_from = Column(Date, nullable=False, default=lambda: datetime.now(timezone.utc).date())
    valid_until = Column(Date, nullable=True)
    priority = Column(Integer, nullable=False, default=100)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class LogisticsCarrierRate(Base):
    __tablename__ = "logistics_carrier_rates"

    __table_args__ = (
        CheckConstraint("weight_tier_g > 0", name="ck_lcr_weight_tier_positive"),
        CheckConstraint("amount_cents >= 0", name="ck_lcr_amount_non_negative"),
        CheckConstraint("valid_until IS NULL OR valid_until >= valid_from", name="ck_lcr_date_range"),
        Index("idx_lcr_lookup", "carrier_code", "origin_zone", "destination_zone", "is_active"),
        Index("idx_lcr_validity", "valid_from", "valid_until"),
    )

    id = Column(String(36), primary_key=True)
    carrier_code = Column(String(20), nullable=False, index=True)
    origin_zone = Column(String(10), nullable=False)
    destination_zone = Column(String(10), nullable=False)
    weight_tier_g = Column(Integer, nullable=False)
    size_tier = Column(String(8), nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    valid_from = Column(Date, nullable=False, default=lambda: date.today())
    valid_until = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
