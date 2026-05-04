from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class WebhookConfigureIn(BaseModel):
    url: HttpUrl
    events: list[str] = Field(default_factory=lambda: ["*"])
    secret: str | None = Field(default=None, max_length=512)


class WebhookSubscriptionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    partner_id: str
    url: str
    events: list[str]
    is_active: bool
    created_at: datetime


class WebhookDeliveryOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    subscription_id: str
    event_type: str
    status: str
    attempts: int
    last_error: str | None
    created_at: datetime
