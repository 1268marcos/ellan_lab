from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApiKeyRotateOut(BaseModel):
    partner_id: str
    partner_type: str
    api_key: str
    key_prefix: str
    created_at: datetime


class ApiKeyMetaOut(BaseModel):
    id: str
    key_prefix: str
    label: Optional[str] = None
    revoked_at: Optional[datetime] = None
    created_at: datetime


class ApiKeyListOut(BaseModel):
    partner_id: str
    partner_type: str
    keys: list[ApiKeyMetaOut]
