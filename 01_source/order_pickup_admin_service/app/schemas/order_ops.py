from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class OrderCreateIn(BaseModel):
    id: Optional[str] = None
    channel: str = "KIOSK"
    region: str = "BR"
    totem_id: str = "TOTEM-01"
    amount_cents: int = Field(ge=0)
    currency: str = "BRL"
    status: str = "PENDING"
    payment_status: str = "PENDING"
    ecommerce_partner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    partner_order_ref: Optional[str] = None
    sku_id: Optional[str] = None
    locker_id: Optional[str] = None


class OrderUpdateIn(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    locker_id: Optional[str] = None


class OrderOut(BaseModel):
    id: str
    channel: str
    region: str
    totem_id: str
    amount_cents: int
    currency: str
    status: str
    payment_status: str
    ecommerce_partner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    partner_order_ref: Optional[str] = None
    sku_id: Optional[str] = None
    locker_id: Optional[str] = None
    pickup_deadline_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListOut(BaseModel):
    items: list[OrderOut]
    total: int


class PickupCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    channel: str = "KIOSK"
    region: str = "BR"
    locker_id: Optional[str] = None
    slot: Optional[str] = None
    status: str = "PENDING"
    lifecycle_stage: str = "CREATED"


class PickupUpdateIn(BaseModel):
    status: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    locker_id: Optional[str] = None
    slot: Optional[str] = None
    fraud_flag: Optional[bool] = None


class PickupOut(BaseModel):
    id: str
    order_id: str
    channel: str
    region: str
    locker_id: Optional[str] = None
    slot: Optional[str] = None
    status: str
    lifecycle_stage: str
    expires_at: Optional[datetime] = None
    ready_at: Optional[datetime] = None
    redeemed_at: Optional[datetime] = None
    fraud_flag: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PickupListOut(BaseModel):
    items: list[PickupOut]
    total: int


class CreditOut(BaseModel):
    id: str
    order_id: str
    user_id: str
    type: str
    amount_cents: int
    currency: str
    status: str
    created_at_epoch: int
    expires_at: Optional[datetime] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreditListOut(BaseModel):
    items: list[CreditOut]
    total: int


class OutboxOut(BaseModel):
    id: str
    partner_id: str
    order_id: str
    event_type: str
    status: str
    attempt_count: int
    max_attempts: int
    next_retry_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OutboxListOut(BaseModel):
    items: list[OutboxOut]
    total: int


class OutboxReplayOut(BaseModel):
    ok: bool
    replayed: bool
    item: OutboxOut


class FulfillmentOut(BaseModel):
    id: str
    order_id: str
    fulfillment_type: str
    partner_id: Optional[str] = None
    status: str
    last_event_type: Optional[str] = None
    last_outbox_status: Optional[str] = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class FulfillmentListOut(BaseModel):
    items: list[FulfillmentOut]
    total: int


class FulfillmentUpdateIn(BaseModel):
    status: Optional[str] = None
    last_event_type: Optional[str] = None
    last_outbox_status: Optional[str] = None


class CreditCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    user_id: str
    type: str = "GOODWILL"
    amount_cents: int = Field(gt=0)
    currency: str = "BRL"
    status: str = "AVAILABLE"


class OrderItemOut(BaseModel):
    id: str
    order_id: str
    sku_id: str
    sku_description: Optional[str] = None
    quantity: int
    unit_amount_cents: int
    total_amount_cents: int
    item_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderItemListOut(BaseModel):
    items: list[OrderItemOut]
    total: int


class OrderItemCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    sku_id: str
    sku_description: Optional[str] = None
    quantity: int = Field(default=1, gt=0)
    unit_amount_cents: int = Field(ge=0)
    item_status: str = "PENDING"
    metadata: Optional[dict[str, Any]] = None


class OrderItemUpdateIn(BaseModel):
    quantity: Optional[int] = Field(default=None, gt=0)
    unit_amount_cents: Optional[int] = Field(default=None, ge=0)
    item_status: Optional[str] = None


class PickupEventOut(BaseModel):
    id: str
    pickup_id: str
    version: int
    event_type: str
    source: str
    occurred_at: datetime

    model_config = {"from_attributes": True}


class PickupEventListOut(BaseModel):
    items: list[PickupEventOut]
    total: int


class PickupTokenOut(BaseModel):
    id: str
    order_id: str
    pickup_id: Optional[str] = None
    token_hash: Optional[str] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    manual_code: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PickupTokenListOut(BaseModel):
    items: list[PickupTokenOut]
    total: int


class PickupAttemptOut(BaseModel):
    id: str
    order_id: str
    gateway_id: str
    created_at_epoch: int
    ok: bool
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


class PickupAttemptListOut(BaseModel):
    items: list[PickupAttemptOut]
    total: int


class DomainOutboxOut(BaseModel):
    id: str
    event_key: str
    aggregate_type: Optional[str] = None
    aggregate_id: Optional[str] = None
    event_name: Optional[str] = None
    status: str
    retry_count: int
    occurred_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DomainOutboxListOut(BaseModel):
    items: list[DomainOutboxOut]
    total: int


class DomainOutboxReplayOut(BaseModel):
    ok: bool
    replayed: bool
    item: DomainOutboxOut


class LifecycleDeadlineOut(BaseModel):
    id: str
    deadline_key: str
    order_id: str
    deadline_type: str
    status: str
    due_at: datetime
    failure_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class LifecycleDeadlineListOut(BaseModel):
    items: list[LifecycleDeadlineOut]
    total: int


class InventorySyncQueueOut(BaseModel):
    id: str
    product_id: str
    marketplace: str
    status: str
    quantity_available: int
    retry_count: int
    last_error: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InventorySyncQueueListOut(BaseModel):
    items: list[InventorySyncQueueOut]
    total: int


class WorkerDlqOut(BaseModel):
    id: str
    worker_name: str
    source_table: str
    source_id: str
    error_message: Optional[str] = None
    attempt_count: int
    dead_lettered_at: datetime

    model_config = {"from_attributes": True}


class WorkerDlqListOut(BaseModel):
    items: list[WorkerDlqOut]
    total: int


class WorkerQueueStatsOut(BaseModel):
    domain_event_outbox: dict[str, int]
    lifecycle_deadlines: dict[str, int]
    inventory_sync_queue: dict[str, int]
    worker_dead_letter_queue: dict[str, int]


class OmnichannelOrderCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    store_id: str
    pickup_type: str = "LOCKER_DELIVERY"
    status: str = "PENDING"


class OmnichannelOrderUpdateIn(BaseModel):
    pickup_type: Optional[str] = None
    status: Optional[str] = None
    ready_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None


class OmnichannelOrderOut(BaseModel):
    id: str
    order_id: str
    store_id: str
    pickup_type: str
    status: str
    ready_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OmnichannelOrderListOut(BaseModel):
    items: list[OmnichannelOrderOut]
    total: int


class FulfillmentOrderCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    fulfillment_center_id: str
    status: str = "PENDING"
    priority: int = 100
    tracking_code: Optional[str] = None
    carrier: Optional[str] = None


class FulfillmentOrderUpdateIn(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None
    tracking_code: Optional[str] = None
    carrier: Optional[str] = None
    picked_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_to_locker_at: Optional[datetime] = None


class FulfillmentOrderOut(BaseModel):
    id: str
    order_id: str
    fulfillment_center_id: str
    status: str
    priority: int
    tracking_code: Optional[str] = None
    carrier: Optional[str] = None
    picked_at: Optional[datetime] = None
    packed_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_to_locker_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FulfillmentOrderListOut(BaseModel):
    items: list[FulfillmentOrderOut]
    total: int


class OrdersHubSummaryOut(BaseModel):
    orders: int
    pickups: int
    credits: int
    partner_outbox_pending: int
    domain_outbox_pending: int
    fulfillment_tracking: int
    omnichannel: int
    fulfillment_orders: int
    allocations: int = 0
    logistics_manifests: int = 0
    integration_channels: int = 0
    marketplace_commissions: int = 0
    lifecycle_deadlines_pending: int = 0
    order_items: int = 0
    food_delivery_orders: int = 0
    timeline_events: int = 0
    sla_watches_active: int = 0
    sla_watches_breached: int = 0
    disputes_open: int = 0
    returns_open: int = 0
    payment_recon_mismatch: int = 0
    ops_holds_active: int = 0
    notifications_sent: int = 0
    substitutions_pending: int = 0
    gifts_pending_verification: int = 0
    payment_transactions: int = 0


class TimelineEventOut(BaseModel):
    id: str
    order_id: str
    event_source: str
    event_type: str
    severity: str
    title: str
    occurred_at: datetime

    model_config = {"from_attributes": True}


class TimelineCreateIn(BaseModel):
    order_id: str
    event_source: str = "ops"
    event_type: str = "NOTE"
    title: str
    severity: str = "INFO"
    detail: Optional[dict[str, Any]] = None


class TimelineListOut(BaseModel):
    items: list[TimelineEventOut]
    total: int


class Order360Out(BaseModel):
    order_id: str
    order: dict[str, Any]
    counts: dict[str, int]
    timeline: list[TimelineEventOut]
    sla: dict[str, int]
    disputes_open: int
    risk_flags: list[str]
    health_score: int
    pickups: list[dict[str, Any]]
    partner_outbox_pending: int


class SlaWatchOut(BaseModel):
    id: str
    order_id: str
    watch_type: str
    due_at: datetime
    status: str
    breached_at: Optional[datetime] = None
    breach_reason: Optional[str] = None

    model_config = {"from_attributes": True}


class SlaWatchListOut(BaseModel):
    items: list[SlaWatchOut]
    total: int


class DisputeCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    dispute_type: str = "CHARGEBACK"
    status: str = "OPEN"
    amount_cents: Optional[int] = None
    currency: str = "BRL"
    reason_code: Optional[str] = None
    notes: Optional[str] = None


class DisputeOut(BaseModel):
    id: str
    order_id: str
    dispute_type: str
    status: str
    amount_cents: Optional[int] = None
    currency: str
    reason_code: Optional[str] = None
    opened_at: datetime

    model_config = {"from_attributes": True}


class DisputeListOut(BaseModel):
    items: list[DisputeOut]
    total: int


class IntegrationHealthOut(BaseModel):
    id: str
    channel_code: str
    check_type: str
    status: str
    latency_ms: Optional[int] = None
    last_error: Optional[str] = None
    checked_at: datetime

    model_config = {"from_attributes": True}


class IntegrationHealthListOut(BaseModel):
    items: list[IntegrationHealthOut]
    total: int


class AllocationCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    locker_id: Optional[str] = None
    slot: int = Field(ge=1)
    state: str = "RESERVED_PENDING_PAYMENT"
    slot_size: Optional[str] = None
    ttl_seconds: Optional[int] = None


class AllocationUpdateIn(BaseModel):
    state: Optional[str] = None
    locker_id: Optional[str] = None
    slot: Optional[int] = Field(default=None, ge=1)
    release_reason: Optional[str] = None


class AllocationOut(BaseModel):
    id: str
    order_id: str
    locker_id: Optional[str] = None
    slot: int
    state: str
    slot_size: Optional[str] = None
    allocated_at: Optional[datetime] = None
    released_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AllocationListOut(BaseModel):
    items: list[AllocationOut]
    total: int


class ManifestCreateIn(BaseModel):
    id: Optional[str] = None
    logistics_partner_id: str
    locker_id: str
    manifest_date: date
    carrier_route_code: Optional[str] = None
    expected_parcel_count: int = 0
    status: str = "PENDING"


class ManifestUpdateIn(BaseModel):
    status: Optional[str] = None
    actual_parcel_count: Optional[int] = None
    carrier_note: Optional[str] = None


class ManifestOut(BaseModel):
    id: str
    logistics_partner_id: str
    locker_id: str
    manifest_date: date
    carrier_route_code: Optional[str] = None
    expected_parcel_count: int
    actual_parcel_count: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ManifestListOut(BaseModel):
    items: list[ManifestOut]
    total: int


class ManifestItemCreateIn(BaseModel):
    id: Optional[str] = None
    manifest_id: str
    delivery_id: Optional[str] = None
    tracking_code: str
    sequence_number: Optional[int] = None
    status: str = "EXPECTED"


class ManifestItemOut(BaseModel):
    id: str
    manifest_id: str
    tracking_code: str
    sequence_number: Optional[int] = None
    status: str

    model_config = {"from_attributes": True}


class ManifestItemListOut(BaseModel):
    items: list[ManifestItemOut]
    total: int


class ChannelCreateIn(BaseModel):
    id: Optional[str] = None
    code: str
    name: str
    player_type: str
    country: str = "BR"
    region_scope: str = "LOCAL"
    api_profile: Optional[str] = None
    active: bool = True
    metadata: Optional[dict[str, Any]] = None


class ChannelUpdateIn(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    api_profile: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ChannelPartnerLinkOut(BaseModel):
    kind: str
    code: str
    name: Optional[str] = None
    role: Optional[str] = None


class ChannelOut(BaseModel):
    id: str
    code: str
    name: str
    player_type: str
    country: str
    region_scope: str
    api_profile: Optional[str] = None
    active: bool
    created_at: datetime
    updated_at: datetime
    review_status: Optional[str] = None
    pickup_modes: Optional[list[str]] = None
    markets: Optional[list[str]] = None
    linked_partners: Optional[list[ChannelPartnerLinkOut]] = None

    model_config = {"from_attributes": True}


class PlayerReviewItem(BaseModel):
    code: str
    name: str
    player_type: str
    country: str
    region_scope: str
    review_status: str
    markets: list[str]
    pickup_modes: list[str]
    api_profile: Optional[str] = None
    ecommerce_partner_code: Optional[str] = None
    logistics_partner_code: Optional[str] = None
    channel_id: Optional[str] = None
    active: bool
    configured: bool
    prompt_group: str = "P4"


class WorldPlayersReviewOut(BaseModel):
    players: list[PlayerReviewItem]
    by_type: dict[str, int]
    prompt3_total: int
    prompt3_configured: int
    prompt3_complete: bool
    prompt4_total: int = 0
    prompt4_configured: int = 0
    prompt4_complete: bool = False
    catalog_total: int = 0
    catalog_configured: int = 0


class FoodDeliveryOrderCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    platform_code: str
    external_order_ref: Optional[str] = None
    restaurant_id: Optional[str] = None
    status: str = "PLACED"
    temperature_zone: str = "HOT"


class FoodDeliveryOrderUpdateIn(BaseModel):
    status: Optional[str] = None
    prep_ready_at: Optional[datetime] = None
    locker_handoff_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None


class FoodDeliveryOrderOut(BaseModel):
    id: str
    order_id: str
    platform_code: str
    external_order_ref: Optional[str] = None
    restaurant_id: Optional[str] = None
    status: str
    temperature_zone: str
    prep_ready_at: Optional[datetime] = None
    locker_handoff_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class FoodDeliveryOrderListOut(BaseModel):
    items: list[FoodDeliveryOrderOut]
    total: int


class ChannelListOut(BaseModel):
    items: list[ChannelOut]
    total: int


class CommissionCreateIn(BaseModel):
    id: Optional[str] = None
    seller_id: str
    order_id: str
    order_item_id: Optional[str] = None
    commission_rate_pct: float = Field(ge=0, le=100)
    commission_amount_cents: int = Field(ge=0)
    ellan_fee_cents: int = Field(ge=0)
    payment_gateway_fee_cents: int = Field(default=0, ge=0)
    net_to_seller_cents: int = Field(ge=0)
    status: str = "PENDING"


class CommissionOut(BaseModel):
    id: str
    seller_id: str
    order_id: str
    order_item_id: Optional[str] = None
    commission_rate_pct: float
    commission_amount_cents: int
    ellan_fee_cents: int
    net_to_seller_cents: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("commission_rate_pct", mode="before")
    @classmethod
    def _coerce_rate(cls, v: object) -> float:
        return float(v) if v is not None else 0.0


class CommissionListOut(BaseModel):
    items: list[CommissionOut]
    total: int


class OrderOpsAuditOut(BaseModel):
    id: str
    action: str
    result: str
    correlation_id: str
    order_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class OrderOpsAuditListOut(BaseModel):
    items: list[OrderOpsAuditOut]
    total: int


class OrderReturnCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    return_type: str = "LOCKER_DROP_OFF"
    status: str = "REQUESTED"
    reason_code: Optional[str] = None
    refund_amount_cents: Optional[int] = None
    currency: str = "BRL"
    locker_id: Optional[str] = None
    tracking_code: Optional[str] = None
    notes: Optional[str] = None


class OrderReturnUpdateIn(BaseModel):
    status: Optional[str] = None
    received_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    notes: Optional[str] = None


class OrderReturnOut(BaseModel):
    id: str
    order_id: str
    return_type: str
    status: str
    reason_code: Optional[str] = None
    refund_amount_cents: Optional[int] = None
    currency: str
    locker_id: Optional[str] = None
    tracking_code: Optional[str] = None
    requested_at: datetime

    model_config = {"from_attributes": True}


class OrderReturnListOut(BaseModel):
    items: list[OrderReturnOut]
    total: int


class NotificationLogOut(BaseModel):
    id: str
    order_id: str
    channel: str
    template_code: str
    recipient_masked: Optional[str] = None
    status: str
    sent_at: datetime

    model_config = {"from_attributes": True}


class NotificationLogListOut(BaseModel):
    items: list[NotificationLogOut]
    total: int


class PaymentReconciliationOut(BaseModel):
    id: str
    order_id: str
    payment_ref: Optional[str] = None
    expected_cents: int
    captured_cents: int
    fee_cents: int
    currency: str
    status: str
    mismatch_reason: Optional[str] = None
    reconciled_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaymentReconciliationListOut(BaseModel):
    items: list[PaymentReconciliationOut]
    total: int


class PaymentReconcileRunIn(BaseModel):
    order_id: Optional[str] = None


class OpsHoldCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    hold_type: str
    reason: Optional[str] = None
    placed_by: str = "ops"


class OpsHoldReleaseIn(BaseModel):
    released_by: str = "ops"


class OpsHoldOut(BaseModel):
    id: str
    order_id: str
    hold_type: str
    status: str
    reason: Optional[str] = None
    placed_by: str
    placed_at: datetime

    model_config = {"from_attributes": True}


class OpsHoldListOut(BaseModel):
    items: list[OpsHoldOut]
    total: int


class ItemSubstitutionCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    order_item_id: Optional[str] = None
    original_sku_id: str
    substitute_sku_id: str
    reason_code: str = "OUT_OF_STOCK"
    status: str = "REQUESTED"
    quantity: int = Field(default=1, ge=1)
    notes: Optional[str] = None


class ItemSubstitutionUpdateIn(BaseModel):
    status: Optional[str] = None
    approved_by: Optional[str] = None
    notes: Optional[str] = None


class ItemSubstitutionOut(BaseModel):
    id: str
    order_id: str
    order_item_id: Optional[str] = None
    original_sku_id: str
    substitute_sku_id: str
    reason_code: str
    status: str
    quantity: int

    model_config = {"from_attributes": True}


class ItemSubstitutionListOut(BaseModel):
    items: list[ItemSubstitutionOut]
    total: int


class GiftPickupCreateIn(BaseModel):
    id: Optional[str] = None
    order_id: str
    purchaser_name: Optional[str] = None
    recipient_name: str
    recipient_phone_masked: Optional[str] = None
    recipient_document_masked: Optional[str] = None
    pickup_authorization_code: Optional[str] = None
    id_verification_required: bool = True
    message: Optional[str] = None


class GiftPickupUpdateIn(BaseModel):
    status: Optional[str] = None
    verified_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None


class GiftPickupOut(BaseModel):
    id: str
    order_id: str
    is_gift: bool
    purchaser_name: Optional[str] = None
    recipient_name: str
    recipient_phone_masked: Optional[str] = None
    pickup_authorization_code: Optional[str] = None
    id_verification_required: bool
    status: str

    model_config = {"from_attributes": True}


class GiftPickupListOut(BaseModel):
    items: list[GiftPickupOut]
    total: int


class PaymentTransactionOut(BaseModel):
    id: str
    order_id: str
    gateway: str
    gateway_transaction_id: Optional[str] = None
    amount_cents: int
    currency: str
    payment_method: str
    status: str
    gateway_fee_cents: int
    net_amount_cents: Optional[int] = None
    reconciliation_status: str
    source: str
    approved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PaymentTransactionListOut(BaseModel):
    items: list[PaymentTransactionOut]
    total: int


class PaymentSyncIn(BaseModel):
    order_id: Optional[str] = None
