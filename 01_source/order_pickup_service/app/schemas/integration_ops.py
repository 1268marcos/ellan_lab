from __future__ import annotations

from pydantic import BaseModel


class OrderEventOutboxItemOut(BaseModel):
    id: str
    partner_id: str
    order_id: str
    event_type: str
    status: str
    attempt_count: int
    max_attempts: int
    next_retry_at: str | None = None
    delivered_at: str | None = None
    created_at: str


class OrderEventOutboxListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[OrderEventOutboxItemOut]


class OrderEventOutboxRunOut(BaseModel):
    ok: bool
    scanned: int
    delivered: int
    failed: int
    dead_letter: int
    skipped: int


class OrderFulfillmentTrackingItemOut(BaseModel):
    id: str
    order_id: str
    fulfillment_type: str
    partner_id: str | None = None
    status: str
    last_event_type: str | None = None
    last_outbox_status: str | None = None
    updated_at: str


class OrderFulfillmentTrackingListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[OrderFulfillmentTrackingItemOut]


class OrderFulfillmentTrackingCompareOut(BaseModel):
    ok: bool
    period_from: str
    period_to: str
    previous_from: str
    previous_to: str
    current_total: int
    previous_total: int
    delta_pct: float
    current_by_status: dict[str, int]
    previous_by_status: dict[str, int]


class OrderEventOutboxReplayOut(BaseModel):
    ok: bool
    replayed: bool
    reason: str | None = None
    item: OrderEventOutboxItemOut


class OrderEventOutboxBatchReplayOut(BaseModel):
    ok: bool
    dry_run: bool
    run_after_replay: bool
    max_deliveries_after_replay: int | None = None
    total_candidates: int
    selected_count: int
    replayed_count: int
    skipped_count: int
    limit: int
    items: list[OrderEventOutboxItemOut]
    worker_run: OrderEventOutboxRunOut | None = None


class OrderPartnerLookupItemOut(BaseModel):
    order_id: str
    partner_id: str | None = None
    partner_order_ref: str | None = None
    status: str
    slot: int | None = None
    locker_id: str | None = None
    created_at: str


class OrderPartnerLookupListOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    items: list[OrderPartnerLookupItemOut]


class OrderEventOutboxDeadLetterPriorityItemOut(BaseModel):
    partner_id: str
    event_type: str
    dead_letter_count: int
    distinct_orders: int
    oldest_created_at: str
    newest_created_at: str
    latest_updated_at: str


class OrderEventOutboxDeadLetterPriorityOut(BaseModel):
    ok: bool
    total_groups: int
    total_dead_letters: int
    total_distinct_orders: int
    limit: int
    items: list[OrderEventOutboxDeadLetterPriorityItemOut]


class OrderEventOutboxPriorityReplayOut(BaseModel):
    ok: bool
    execution_id: str
    dry_run: bool
    run_after_replay: bool
    max_deliveries_after_replay: int | None = None
    top_n_groups: int
    max_items: int
    total_groups_selected: int
    total_candidates: int
    selected_count: int
    replayed_count: int
    skipped_count: int
    groups: list[OrderEventOutboxDeadLetterPriorityItemOut]
    items: list[OrderEventOutboxItemOut]
    worker_run: OrderEventOutboxRunOut | None = None


class OrderEventOutboxPriorityReplayRunItemOut(BaseModel):
    execution_id: str
    created_at: str
    dry_run: bool
    run_after_replay: bool
    top_n_groups: int
    max_items: int
    total_groups_selected: int
    total_candidates: int
    selected_count: int
    replayed_count: int
    skipped_count: int
    effectiveness_rate_pct: float


class OrderEventOutboxPriorityReplayRunTimelineOut(BaseModel):
    ok: bool
    total: int
    limit: int
    offset: int
    period_from: str | None = None
    period_to: str | None = None
    average_effectiveness_rate_pct: float
    items: list[OrderEventOutboxPriorityReplayRunItemOut]
