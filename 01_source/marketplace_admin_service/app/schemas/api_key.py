from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ApiKeyRotateOut(BaseModel):
    seller_id: str
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
    seller_id: str
    keys: list[ApiKeyMetaOut]
