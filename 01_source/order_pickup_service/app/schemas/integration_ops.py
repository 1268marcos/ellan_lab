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
