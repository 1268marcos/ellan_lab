from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CapabilityWebhookConfigureIn(BaseModel):
    ecosystem_player_id: str
    capability_code: str
    url: str
    secret: Optional[str] = None
    events: Optional[list[str]] = None
    active: bool = True


class CapabilityWebhookOut(BaseModel):
    id: str
    ecosystem_player_id: str
    player_code: str
    capability_code: str
    url: str
    source: str
    marketplace_webhook_id: Optional[str] = None
    active: bool
    last_http_status: Optional[int] = None
    last_delivered_at: Optional[datetime] = None
    last_error: Optional[str] = None
    event_types_json: str = "[]"

    model_config = {"from_attributes": True}


class CapabilityWebhookListOut(BaseModel):
    items: list[CapabilityWebhookOut]
    total: int


class CapabilityWebhookMirrorOut(BaseModel):
    created: int
    updated: int
    mirrored_from_marketplace: int
    total: int


class CapabilityWebhookDeliveryOut(BaseModel):
    id: str
    webhook_id: str
    event_type: str
    http_status: Optional[int] = None
    success: bool
    response_snippet: Optional[str] = None
    status: str = "DELIVERED"
    attempt_count: int = 1
    dead_lettered_at: Optional[datetime] = None
    replay_of_delivery_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CapabilityWebhookDeliveryListOut(BaseModel):
    items: list[CapabilityWebhookDeliveryOut]
    total: int


class DeadLetterReplayBatchOut(BaseModel):
    requested: int
    replayed: int
    succeeded: int
