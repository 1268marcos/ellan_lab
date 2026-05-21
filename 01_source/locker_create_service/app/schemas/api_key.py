from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class ApiKeyRotateOut(BaseModel):
    locker_id: str
    api_key: str
    key_prefix: str
    rotated_at: datetime


class ApiKeyMetaOut(BaseModel):
    id: int
    key_prefix: str
    active: bool
    created_at: datetime
    rotated_at: Optional[datetime] = None


class ApiKeyListOut(BaseModel):
    locker_id: str
    keys: List[ApiKeyMetaOut]
