# 01_source/backend/order_lifecycle_service/app/schemas/domain_events.py
from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class DomainEventPublishIn(BaseModel):
    event_key: str = Field(..., min_length=1, max_length=200)
    aggregate_type: str = Field(..., min_length=1, max_length=100)
    aggregate_id: str = Field(..., min_length=1, max_length=100)
    event_name: str = Field(..., min_length=1, max_length=150)
    event_version: int = Field(default=1, ge=1)
    payload: dict = Field(default_factory=dict)
    occurred_at: datetime

    @field_validator("event_key", "aggregate_type", "aggregate_id", "event_name")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized


class DomainEventPublishOut(BaseModel):
    ok: bool = True
    idempotent: bool
    event_key: str
    aggregate_type: str
    aggregate_id: str
    event_name: str
    status: str
