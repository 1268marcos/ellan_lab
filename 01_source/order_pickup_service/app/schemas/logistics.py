from __future__ import annotations

from pydantic import BaseModel, Field


class LogisticsWebhookAttemptIn(BaseModel):
    attempt_number: int | None = Field(default=None, ge=1, le=99)
    status: str = Field(..., description="SUCCESS|FAILED|RESCHEDULED|RETURNED")
    attempted_at: str | None = Field(default=None, description="ISO-8601 UTC")
    failure_reason: str | None = Field(default=None, max_length=160)
    carrier_note: str | None = Field(default=None, max_length=2000)
    carrier_agent: str | None = Field(default=None, max_length=128)
    proof_url: str | None = Field(default=None, max_length=500)


class LogisticsWebhookEventIn(BaseModel):
    delivery_id: str = Field(..., max_length=36)
    event_code: str | None = Field(default=None, max_length=40)
    event_label: str | None = Field(default=None, max_length=120)
    raw_status: str | None = Field(default=None, max_length=80)
    occurred_at: str | None = Field(default=None, description="ISO-8601 UTC")
    location_city: str | None = Field(default=None, max_length=80)
    location_state: str | None = Field(default=None, max_length=80)
    location_country: str | None = Field(default=None, min_length=2, max_length=2)
    source_ref: str | None = Field(default=None, max_length=128)
    payload: dict = Field(default_factory=dict)
    attempt: LogisticsWebhookAttemptIn | None = None


class LogisticsTrackingEventOut(BaseModel):
    id: str
    delivery_id: str
    event_code: str
    event_label: str
    raw_status: str | None = None
    location_city: str | None = None
    location_state: str | None = None
    location_country: str | None = None
    occurred_at: str
    source: str
    source_ref: str | None = None
    payload: dict
    created_at: str


class LogisticsTrackingEventListOut(BaseModel):
    ok: bool
    total: int
    items: list[LogisticsTrackingEventOut]


class LogisticsDeliveryAttemptOut(BaseModel):
    id: str
    delivery_id: str
    attempt_number: int
    status: str
    attempted_at: str
    failure_reason: str | None = None
    carrier_note: str | None = None
    carrier_agent: str | None = None
    proof_url: str | None = None
    created_at: str


class LogisticsDeliveryAttemptListOut(BaseModel):
    ok: bool
    total: int
    items: list[LogisticsDeliveryAttemptOut]


class LogisticsLabelCreateIn(BaseModel):
    carrier_code: str = Field(..., max_length=20)
    tracking_code: str | None = Field(default=None, max_length=128)
    label_format: str = Field(default="PDF", max_length=10)
    label_url: str | None = Field(default=None, max_length=500)
    label_payload: dict = Field(default_factory=dict)
    expires_at: str | None = Field(default=None, description="ISO-8601 UTC")


class LogisticsShipmentLabelOut(BaseModel):
    id: str
    delivery_id: str
    carrier_code: str
    tracking_code: str
    label_format: str
    label_url: str | None = None
    label_payload: dict
    status: str
    created_at: str
    expires_at: str | None = None


class LogisticsWebhookIngestOut(BaseModel):
    ok: bool
    carrier_code: str
    event: LogisticsTrackingEventOut
    attempt: LogisticsDeliveryAttemptOut | None = None


class LogisticsCarrierAuthConfigIn(BaseModel):
    carrier_code: str = Field(..., max_length=20)
    signature_header: str = Field(default="X-Carrier-Signature", max_length=64)
    algorithm: str = Field(default="HMAC_SHA256", max_length=20)
    secret_key: str | None = Field(default=None, max_length=256)
    required: bool = Field(default=False)
    active: bool = Field(default=True)


class LogisticsCarrierAuthConfigOut(BaseModel):
    id: str
    carrier_code: str
    signature_header: str
    algorithm: str
    required: bool
    active: bool
    created_at: str
    updated_at: str


class LogisticsCarrierStatusMapIn(BaseModel):
    carrier_code: str = Field(..., max_length=20)
    raw_status: str = Field(..., max_length=80)
    normalized_event_code: str = Field(..., max_length=40)
    normalized_event_label: str = Field(..., max_length=120)
    normalized_outcome: str | None = Field(default=None, max_length=20)
    active: bool = Field(default=True)


class LogisticsCarrierStatusMapOut(BaseModel):
    id: str
    carrier_code: str
    raw_status: str
    normalized_event_code: str
    normalized_event_label: str
    normalized_outcome: str | None = None
    active: bool
    created_at: str
    updated_at: str


class LogisticsOpsOverviewOut(BaseModel):
    ok: bool
    from_: str = Field(..., alias="from")
    to: str
    carrier_code: str | None = None
    totals: dict
    by_event_code: list[dict]
    by_attempt_status: list[dict]
    by_label_carrier: list[dict]


class LogisticsManifestOpsOverviewOut(BaseModel):
    ok: bool
    from_: str = Field(..., alias="from")
    to: str
    partner_id: str | None = None
    confidence_badge: str
    totals: dict
    by_status: list[dict]
    alerts: list[dict]


class LogisticsReturnCreateIn(BaseModel):
    order_id: str = Field(..., max_length=36)
    partner_id: str = Field(..., max_length=36)
    reason_code: str = Field(..., max_length=40)
    notes: str | None = Field(default=None, max_length=2000)


class LogisticsReturnStatusUpdateIn(BaseModel):
    to_status: str = Field(..., max_length=30)
    reason: str | None = Field(default=None, max_length=200)


class LogisticsReturnOut(BaseModel):
    id: str
    order_id: str
    partner_id: str
    reason_code: str
    status: str
    notes: str | None = None
    created_by: str | None = None
    created_at: str
    updated_at: str


class LogisticsReturnEventOut(BaseModel):
    id: str
    return_id: str
    from_status: str | None = None
    to_status: str
    reason: str | None = None
    changed_by: str | None = None
    occurred_at: str
    created_at: str


class LogisticsReturnListOut(BaseModel):
    ok: bool
    total: int
    items: list[LogisticsReturnOut]


class LogisticsReturnEventListOut(BaseModel):
    ok: bool
    total: int
    items: list[LogisticsReturnEventOut]


class LogisticsManifestCreateIn(BaseModel):
    logistics_partner_id: str = Field(..., max_length=36)
    locker_id: str = Field(..., max_length=64)
    manifest_date: str = Field(..., description="YYYY-MM-DD")
    carrier_route_code: str | None = Field(default=None, max_length=64)
    carrier_vehicle_id: str | None = Field(default=None, max_length=64)
    expected_parcel_count: int = Field(default=0, ge=0)
    carrier_note: str | None = Field(default=None, max_length=4000)


class LogisticsManifestStatusUpdateIn(BaseModel):
    status: str = Field(..., max_length=20, description="PENDING|IN_TRANSIT|DELIVERED|PARTIAL|FAILED|CANCELLED")
    actual_parcel_count: int | None = Field(default=None, ge=0)
    carrier_note: str | None = Field(default=None, max_length=4000)


class LogisticsManifestCloseIn(BaseModel):
    actual_parcel_count: int | None = Field(default=None, ge=0)
    carrier_note: str | None = Field(default=None, max_length=4000)


class LogisticsManifestItemExceptionIn(BaseModel):
    reason: str = Field(..., min_length=1, max_length=4000)


class LogisticsManifestItemOut(BaseModel):
    id: int
    manifest_id: str
    delivery_id: str | None = None
    tracking_code: str
    sequence_number: int | None = None
    status: str
    exception_note: str | None = None
    processed_at: str | None = None


class LogisticsManifestOut(BaseModel):
    id: str
    logistics_partner_id: str
    locker_id: str
    manifest_date: str
    carrier_route_code: str | None = None
    carrier_vehicle_id: str | None = None
    expected_parcel_count: int
    actual_parcel_count: int
    status: str
    dispatched_at: str | None = None
    delivered_at: str | None = None
    carrier_note: str | None = None
    created_at: str
    updated_at: str


class LogisticsManifestListOut(BaseModel):
    ok: bool
    total: int
    items: list[LogisticsManifestOut]


class LogisticsManifestItemListOut(BaseModel):
    ok: bool
    total: int
    items: list[LogisticsManifestItemOut]


class LogisticsCapacityAllocationUpsertIn(BaseModel):
    locker_id: str = Field(..., max_length=64)
    slot_size: str = Field(..., max_length=8, description="S|M|L|XL")
    reserved_slots: int = Field(..., ge=0)
    valid_from: str = Field(..., description="YYYY-MM-DD")
    valid_until: str | None = Field(default=None, description="YYYY-MM-DD")
    priority: int = Field(default=100, ge=0, le=9999)
    notes: str | None = Field(default=None, max_length=4000)
    is_active: bool = Field(default=True)


class LogisticsCapacityAllocationOut(BaseModel):
    id: str
    logistics_partner_id: str
    locker_id: str
    slot_size: str
    reserved_slots: int
    valid_from: str
    valid_until: str | None = None
    priority: int
    notes: str | None = None
    is_active: bool
    created_at: str


class LogisticsCapacityAllocationListOut(BaseModel):
    ok: bool
    total: int
    items: list[LogisticsCapacityAllocationOut]
