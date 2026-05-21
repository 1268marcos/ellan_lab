from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, HttpUrl


class WebhookConfigureIn(BaseModel):
    url: HttpUrl
    secret: Optional[str] = None
    events: List[str] = ["locker.created", "locker.updated", "locker.slot_changed"]
    active: bool = True


class WebhookOut(BaseModel):
    locker_id: str
    url: str
    events: List[str]
    active: bool
    has_secret: bool
    updated_at: datetime
