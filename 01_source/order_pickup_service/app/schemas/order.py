from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class CreateOrderIn(BaseModel):
    region: str
    sku_id: str
    totem_id: str
    desired_slot: Optional[int] = None


class OrderOut(BaseModel):
    order_id: str
    channel: str
    status: str
    amount_cents: int
    allocation: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OrderListItemOut(BaseModel):
    order_id: str
    user_id: Optional[str] = None
    region: str
    channel: str
    status: str
    sku_id: str
    totem_id: str
    amount_cents: int

    allocation_id: Optional[str] = None
    slot: Optional[int] = None
    allocation_state: Optional[str] = None

    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    pickup_deadline_at: Optional[datetime] = None


class OrderListOut(BaseModel):
    items: List[OrderListItemOut]
    total: int