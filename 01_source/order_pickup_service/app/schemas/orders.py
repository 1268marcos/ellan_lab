from pydantic import BaseModel
from typing import Optional, Dict, Any

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