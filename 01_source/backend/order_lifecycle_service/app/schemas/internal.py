from datetime import datetime
from pydantic import BaseModel, Field


class CreateDeadlineRequest(BaseModel):
    deadline_key: str = Field(..., description="Idempotency key do deadline")
    order_id: str
    order_channel: str | None = None
    deadline_type: str
    due_at: datetime
    payload: dict = Field(default_factory=dict)


class CreateDeadlineResponse(BaseModel):
    id: str
    deadline_key: str
    status: str
    order_id: str
    deadline_type: str
    due_at: datetime


class CancelDeadlineRequest(BaseModel):
    deadline_key: str


class CancelDeadlineResponse(BaseModel):
    deadline_key: str
    status: str
    cancelled: bool


class PendingEventItem(BaseModel):
    id: str
    event_key: str
    aggregate_type: str
    aggregate_id: str
    event_name: str
    event_version: int
    status: str
    payload: dict = Field(default_factory=dict)
    occurred_at: datetime
    created_at: datetime


class PendingEventsResponse(BaseModel):
    items: list[PendingEventItem]


class AckEventRequest(BaseModel):
    event_key: str


class AckEventResponse(BaseModel):
    event_key: str
    status: str
    acknowledged: bool