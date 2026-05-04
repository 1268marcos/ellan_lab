from __future__ import annotations

from pydantic import BaseModel, HttpUrl


class WebhookConfigureIn(BaseModel):
    url: HttpUrl
    secret: str | None = None
    events: list[str] | None = None


class WebhookConfigureOut(BaseModel):
    partner_id: str
    url: str
    ok: bool


class ReplayIn(BaseModel):
    start_id: str = "0"
    count: int = 100
