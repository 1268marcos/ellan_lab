from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BiCapabilityWebhookIn(BaseModel):
    network_player_code: str
    capability_code: str
    url: str
    secret: str | None = None
    event_types: list[str] = Field(default_factory=lambda: ["mart.refreshed", "kpi.threshold"])


class BiCapabilityWebhookOut(BaseModel):
    id: str
    network_player_code: str
    capability_code: str
    url: str
    event_types: list[str]
    active: bool
    last_http_status: int | None = None
    last_delivered_at: datetime | None = None
    last_error: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class BiCapabilityWebhookListOut(BaseModel):
    webhooks: list[BiCapabilityWebhookOut]
    total: int
