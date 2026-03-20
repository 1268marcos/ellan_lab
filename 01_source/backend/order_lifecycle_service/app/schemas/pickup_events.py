# 01_source/backend/order_lifecycle_service/app/schemas/pickup_events.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PickupEventIn(BaseModel):
    event_key: str
    event_type: str

    occurred_at: datetime

    order_id: str
    pickup_id: str

    channel: Optional[str] = None
    region: Optional[str] = None

    locker_id: Optional[str] = None
    machine_id: Optional[str] = None
    slot: Optional[str] = None

    operator_id: Optional[str] = None
    tenant_id: Optional[str] = None
    site_id: Optional[str] = None

    correlation_id: Optional[str] = None
    source_service: str

    payload: Optional[dict] = None


class PickupEventResponse(BaseModel):
    ok: bool
    event_key: str
    stored: bool