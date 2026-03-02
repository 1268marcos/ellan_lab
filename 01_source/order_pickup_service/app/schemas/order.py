# Compatível com:
# OrderChannel (KIOSK, APP, WEB)
# OrderStatus (CREATED, PAID, READY, PICKED_UP, EXPIRED, CANCELLED)
# Porta vinculada
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from enum import Enum


class OrderChannel(str, Enum):
    KIOSK = "KIOSK"
    APP = "APP"
    WEB = "WEB"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PAID = "PAID"
    READY = "READY"
    PICKED_UP = "PICKED_UP"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class OrderBase(BaseModel):
    amount: float
    channel: OrderChannel
    locker_port: Optional[int] = None


class OrderCreate(OrderBase):
    payment_id: Optional[str] = None


class OrderUpdateStatus(BaseModel):
    status: OrderStatus


class OrderResponse(OrderBase):
    id: int
    status: OrderStatus
    payment_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True