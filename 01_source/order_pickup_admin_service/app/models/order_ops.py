from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, Integer, Numeric, String, Text

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderRecord(Base):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True)
    channel = Column(String(32), nullable=False, default="KIOSK")
    region = Column(String(32), nullable=False, default="BR")
    totem_id = Column(String(100), nullable=False, default="")
    amount_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(32), nullable=False, default="PENDING")
    payment_status = Column(String(32), nullable=False, default="PENDING")
    ecommerce_partner_id = Column(String(100), nullable=True, index=True)
    tenant_id = Column(String(100), nullable=True, index=True)
    partner_order_ref = Column(String(255), nullable=True)
    sku_id = Column(String(255), nullable=True)
    locker_id = Column(String(120), nullable=True)
    pickup_deadline_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    order_metadata = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PickupRecord(Base):
    __tablename__ = "pickups"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    channel = Column(String(32), nullable=False, default="KIOSK")
    region = Column(String(32), nullable=False, default="BR")
    locker_id = Column(String(120), nullable=True, index=True)
    slot = Column(String(32), nullable=True)
    status = Column(String(32), nullable=False, default="PENDING")
    lifecycle_stage = Column(String(40), nullable=False, default="CREATED")
    expires_at = Column(DateTime(timezone=True), nullable=True)
    ready_at = Column(DateTime(timezone=True), nullable=True)
    redeemed_at = Column(DateTime(timezone=True), nullable=True)
    fraud_flag = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class CreditRecord(Base):
    __tablename__ = "credits"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(64), nullable=False, index=True)
    type = Column(String(32), nullable=False, default="REFUND")
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(32), nullable=False, default="AVAILABLE")
    created_at_epoch = Column(BigInteger, nullable=False, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    meta_json = Column(Text, nullable=False, default="{}")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PartnerOrderEventsOutbox(Base):
    __tablename__ = "partner_order_events_outbox"

    id = Column(String(36), primary_key=True)
    partner_id = Column(String(36), nullable=False, index=True)
    order_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    status = Column(String(20), nullable=False, default="PENDING")
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=5)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderFulfillmentTracking(Base):
    __tablename__ = "order_fulfillment_tracking"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    fulfillment_type = Column(String(30), nullable=False, default="ECOMMERCE_PARTNER")
    partner_id = Column(String(36), nullable=True, index=True)
    status = Column(String(30), nullable=False, default="PENDING")
    last_event_type = Column(String(50), nullable=True)
    last_outbox_status = Column(String(20), nullable=True)
    allocated_at = Column(DateTime(timezone=True), nullable=True)
    dispensed_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderItemRecord(Base):
    __tablename__ = "order_items"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    sku_id = Column(String(255), nullable=False)
    sku_description = Column(String(500), nullable=True)
    quantity = Column(Integer, nullable=False, default=1)
    unit_amount_cents = Column(Integer, nullable=False)
    total_amount_cents = Column(Integer, nullable=False)
    item_status = Column(String(32), nullable=False, default="PENDING")
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PickupEventRecord(Base):
    __tablename__ = "pickup_events"

    id = Column(String(36), primary_key=True)
    pickup_id = Column(String(64), nullable=False, index=True)
    version = Column(BigInteger, nullable=False, default=1)
    event_type = Column(String(100), nullable=False)
    payload_json = Column(Text, nullable=False, default="{}")
    source = Column(String(100), nullable=False, default="admin")
    occurred_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PickupTokenRecord(Base):
    __tablename__ = "pickup_tokens"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    pickup_id = Column(String(64), nullable=True, index=True)
    token_hash = Column(String(128), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    manual_code = Column(String(32), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class PickupAttemptRecord(Base):
    __tablename__ = "pickup_attempts"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    gateway_id = Column(String(64), nullable=False, default="")
    created_at_epoch = Column(BigInteger, nullable=False, default=0)
    ok = Column(Boolean, nullable=False, default=False)
    reason = Column(String(255), nullable=True)
    payload_json = Column(Text, nullable=False, default="{}")


class AllocationRecord(Base):
    __tablename__ = "allocations"

    id = Column(String(64), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    locker_id = Column(String(120), nullable=True)
    slot = Column(Integer, nullable=False)
    state = Column(String(40), nullable=False, default="RESERVED_PENDING_PAYMENT")
    locked_until = Column(DateTime(timezone=True), nullable=True)
    allocated_at = Column(DateTime(timezone=True), nullable=True)
    released_at = Column(DateTime(timezone=True), nullable=True)
    release_reason = Column(String(255), nullable=True)
    slot_size = Column(String(20), nullable=True)
    ttl_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class LogisticsManifest(Base):
    __tablename__ = "logistics_manifests"

    id = Column(String(36), primary_key=True)
    logistics_partner_id = Column(String(36), nullable=False, index=True)
    locker_id = Column(String(64), nullable=False)
    manifest_date = Column(Date, nullable=False)
    carrier_route_code = Column(String(64), nullable=True)
    carrier_vehicle_id = Column(String(64), nullable=True)
    expected_parcel_count = Column(Integer, nullable=False, default=0)
    actual_parcel_count = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="PENDING")
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    carrier_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class LogisticsManifestItem(Base):
    __tablename__ = "logistics_manifest_items"

    id = Column(String(36), primary_key=True)
    manifest_id = Column(String(36), nullable=False, index=True)
    delivery_id = Column(String(36), nullable=True)
    tracking_code = Column(String(128), nullable=False)
    sequence_number = Column(Integer, nullable=True)
    status = Column(String(20), nullable=False, default="EXPECTED")
    exception_note = Column(Text, nullable=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)


class OrderChannelPartnerLink(Base):
    __tablename__ = "order_channel_partner_links"

    id = Column(String(36), primary_key=True)
    channel_id = Column(String(36), nullable=False, index=True)
    partner_id = Column(String(36), nullable=False)
    partner_kind = Column(String(20), nullable=False)
    link_role = Column(String(30), nullable=False, default="PRIMARY")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderIntegrationChannel(Base):
    __tablename__ = "order_integration_channels"

    id = Column(String(36), primary_key=True)
    code = Column(String(32), nullable=False, unique=True)
    name = Column(String(128), nullable=False)
    player_type = Column(String(30), nullable=False)
    country = Column(String(2), nullable=False, default="BR")
    region_scope = Column(String(20), nullable=False, default="LOCAL")
    api_profile = Column(String(50), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderMarketplaceCommission(Base):
    __tablename__ = "order_marketplace_commissions"

    id = Column(String(36), primary_key=True)
    seller_id = Column(String(36), nullable=False)
    order_id = Column(String(64), nullable=False, index=True)
    order_item_id = Column(String(36), nullable=True)
    commission_rate_pct = Column(Numeric(5, 2), nullable=False)
    commission_amount_cents = Column(Integer, nullable=False)
    ellan_fee_cents = Column(Integer, nullable=False)
    payment_gateway_fee_cents = Column(Integer, nullable=False, default=0)
    net_to_seller_cents = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="PENDING")
    settled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class LifecycleDeadlineRecord(Base):
    __tablename__ = "lifecycle_deadlines"

    id = Column(String(36), primary_key=True)
    deadline_key = Column(String(200), nullable=False, unique=True)
    order_id = Column(String(100), nullable=False, index=True)
    order_channel = Column(String(50), nullable=True)
    deadline_type = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    failure_count = Column(Integer, nullable=False, default=0)
    payload_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderOpsAudit(Base):
    __tablename__ = "order_ops_audit"

    id = Column(String(40), primary_key=True)
    action = Column(String(120), nullable=False)
    result = Column(String(20), nullable=False)
    correlation_id = Column(String(80), nullable=False)
    order_id = Column(String(64), nullable=True, index=True)
    user_id = Column(String(36), nullable=True)
    role = Column(String(80), nullable=True)
    error_message = Column(Text, nullable=True)
    details_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class FoodDeliveryOrder(Base):
    __tablename__ = "food_delivery_orders"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    platform_code = Column(String(32), nullable=False, index=True)
    external_order_ref = Column(String(255), nullable=True)
    restaurant_id = Column(String(36), nullable=True)
    status = Column(String(30), nullable=False, default="PLACED")
    temperature_zone = Column(String(20), nullable=False, default="HOT")
    prep_ready_at = Column(DateTime(timezone=True), nullable=True)
    locker_handoff_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OmnichannelOrder(Base):
    __tablename__ = "omnichannel_orders"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    store_id = Column(String(36), nullable=False)
    pickup_type = Column(String(20), nullable=False, default="LOCKER_DELIVERY")
    status = Column(String(20), nullable=False, default="PENDING")
    ready_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class FulfillmentOrder(Base):
    __tablename__ = "fulfillment_orders"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    fulfillment_center_id = Column(String(36), nullable=False)
    status = Column(String(30), nullable=False, default="PENDING")
    priority = Column(Integer, nullable=False, default=100)
    picked_at = Column(DateTime(timezone=True), nullable=True)
    packed_at = Column(DateTime(timezone=True), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_to_locker_at = Column(DateTime(timezone=True), nullable=True)
    tracking_code = Column(String(128), nullable=True)
    carrier = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderOpsTimeline(Base):
    __tablename__ = "order_ops_timeline"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    event_source = Column(String(40), nullable=False)
    event_type = Column(String(80), nullable=False)
    severity = Column(String(20), nullable=False, default="INFO")
    title = Column(String(200), nullable=False)
    detail_json = Column(Text, nullable=False, default="{}")
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class OrderSlaWatch(Base):
    __tablename__ = "order_sla_watches"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    watch_type = Column(String(40), nullable=False)
    due_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    breached_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    breach_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderDispute(Base):
    __tablename__ = "order_disputes"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    dispute_type = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="OPEN")
    amount_cents = Column(Integer, nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    reason_code = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    opened_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderReturn(Base):
    __tablename__ = "order_returns"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    return_type = Column(String(30), nullable=False, default="LOCKER_DROP_OFF")
    status = Column(String(20), nullable=False, default="REQUESTED")
    reason_code = Column(String(64), nullable=True)
    refund_amount_cents = Column(Integer, nullable=True)
    currency = Column(String(8), nullable=False, default="BRL")
    locker_id = Column(String(120), nullable=True)
    tracking_code = Column(String(128), nullable=True)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    received_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderNotificationLog(Base):
    __tablename__ = "order_notification_logs"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    channel = Column(String(20), nullable=False)
    template_code = Column(String(64), nullable=False)
    recipient_masked = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False, default="SENT")
    provider_ref = Column(String(128), nullable=True)
    payload_json = Column(Text, nullable=False, default="{}")
    sent_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class OrderPaymentReconciliation(Base):
    __tablename__ = "order_payment_reconciliation"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, unique=True, index=True)
    payment_ref = Column(String(128), nullable=True)
    expected_cents = Column(Integer, nullable=False)
    captured_cents = Column(Integer, nullable=False)
    fee_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String(8), nullable=False, default="BRL")
    status = Column(String(20), nullable=False, default="PENDING")
    mismatch_reason = Column(String(255), nullable=True)
    reconciled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderOpsHold(Base):
    __tablename__ = "order_ops_holds"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    hold_type = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")
    reason = Column(Text, nullable=True)
    placed_by = Column(String(64), nullable=False, default="ops")
    released_by = Column(String(64), nullable=True)
    placed_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    released_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderItemSubstitution(Base):
    __tablename__ = "order_item_substitutions"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    order_item_id = Column(String(36), nullable=True)
    original_sku_id = Column(String(255), nullable=False)
    substitute_sku_id = Column(String(255), nullable=False)
    reason_code = Column(String(40), nullable=False)
    status = Column(String(20), nullable=False, default="REQUESTED")
    quantity = Column(Integer, nullable=False, default=1)
    approved_by = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderGiftPickup(Base):
    __tablename__ = "order_gift_pickup"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, unique=True, index=True)
    is_gift = Column(Boolean, nullable=False, default=True)
    purchaser_name = Column(String(200), nullable=True)
    recipient_name = Column(String(200), nullable=False)
    recipient_phone_masked = Column(String(32), nullable=True)
    recipient_document_masked = Column(String(32), nullable=True)
    pickup_authorization_code = Column(String(32), nullable=True)
    id_verification_required = Column(Boolean, nullable=False, default=True)
    status = Column(String(30), nullable=False, default="PENDING_VERIFICATION")
    verified_at = Column(DateTime(timezone=True), nullable=True)
    picked_up_at = Column(DateTime(timezone=True), nullable=True)
    message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class PaymentTransactionRecord(Base):
    """Espelho operacional das transações do payments-admin / gateway."""

    __tablename__ = "payment_transactions"

    id = Column(String(36), primary_key=True)
    order_id = Column(String(64), nullable=False, index=True)
    gateway = Column(String(50), nullable=False)
    gateway_transaction_id = Column(String(128), nullable=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(8), nullable=False, default="BRL")
    payment_method = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="INITIATED")
    gateway_fee_cents = Column(Integer, nullable=False, default=0)
    net_amount_cents = Column(Integer, nullable=True)
    reconciliation_status = Column(String(20), nullable=False, default="PENDING")
    approved_at = Column(DateTime(timezone=True), nullable=True)
    synced_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(String(20), nullable=False, default="LOCAL")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)


class OrderIntegrationHealth(Base):
    __tablename__ = "order_integration_health"

    id = Column(String(36), primary_key=True)
    channel_code = Column(String(32), nullable=False, index=True)
    check_type = Column(String(40), nullable=False, default="WEBHOOK_DELIVERY")
    status = Column(String(20), nullable=False)
    latency_ms = Column(Integer, nullable=True)
    last_error = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)


class DomainEventOutboxRecord(Base):
    __tablename__ = "domain_event_outbox"

    id = Column(String(36), primary_key=True)
    event_key = Column(String(255), nullable=False)
    aggregate_type = Column(String(100), nullable=True)
    aggregate_id = Column(String(100), nullable=True, index=True)
    event_name = Column(String(100), nullable=True)
    event_version = Column(Integer, nullable=True, default=1)
    status = Column(String(50), nullable=False, default="PENDING")
    payload_json = Column(Text, nullable=False, default="{}")
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)
