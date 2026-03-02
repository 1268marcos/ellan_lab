from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CreditBase(BaseModel):
    amount: float


class CreditCreate(CreditBase):
    user_id: int


class CreditResponse(CreditBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True