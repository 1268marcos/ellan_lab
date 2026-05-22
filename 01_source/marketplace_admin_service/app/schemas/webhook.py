from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class WebhookConfigureIn(BaseModel):
    url: str
    secret: Optional[str] = None
    events: list[str] = Field(default_factory=lambda: ["order.created", "commission.settled"])
    active: bool = True
    api_version: str = "v1"


class WebhookOut(BaseModel):
    id: str
    seller_id: str
    url: str
    events_json: str
    api_version: str
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
