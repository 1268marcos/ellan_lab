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
