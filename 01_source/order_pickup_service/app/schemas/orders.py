from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class CreateOrderIn(BaseModel):
    region: str
    sku_id: str
    totem_id: str
    desired_slot: Optional[int] = None
    amount_cents: Optional[int] = None


class OrderOut(BaseModel):
    order_id: str
    channel: str
    status: str
    amount_cents: int
    payment_method: Optional[str] = None
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
    payment_method: Optional[str] = None

    allocation_id: Optional[str] = None
    slot: Optional[int] = None
    allocation_state: Optional[str] = None

    pickup_id: Optional[str] = None
    expires_at: Optional[datetime] = None

    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    pickup_deadline_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None


class OrderListOut(BaseModel):
    items: List[OrderListItemOut]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool