# 01_source/order_pickup_service/app/schemas/internal.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Region = Literal["SP", "PT"]
OrderChannel = Literal["ONLINE", "KIOSK"]

OrderStatus = Literal[
    "PAYMENT_PENDING",
    "PAID_PENDING_PICKUP",
    "DISPENSED",
    "PICKED_UP",
    "EXPIRED",
]

SlotState = Literal[
    "AVAILABLE",
    "RESERVED",
    "LOCKED",
    "OUT_OF_STOCK",
]


class InternalEvent(BaseModel):
    event_id: str = Field(..., description="UUID do evento")
    event_type: str = Field(..., description="Tipo do evento")
    created_at: datetime = Field(..., description="Timestamp do evento")

    region: Region
    totem_id: str
    channel: OrderChannel
    order_id: str

    data: Dict[str, Any] = Field(default_factory=dict)


class InternalPaymentApprovedIn(BaseModel):
    order_id: str
    region: Region
    totem_id: str
    channel: OrderChannel

    provider: str = Field(..., description="Ex.: pix, card, mbway")
    transaction_id: str = Field(..., description="id do provedor")
    amount_cents: int
    currency: str = Field(default="BRL", description="Moeda informada pelo chamador")

    device_fingerprint: Optional[str] = None
    ip: Optional[str] = None


class InternalPaymentApprovedOut(BaseModel):
    ok: bool = True
    order_id: str
    status: OrderStatus
    slot: Optional[int] = None
    message: str


class InternalSetSlotStateIn(BaseModel):
    region: Region
    totem_id: str
    slot: int
    state: SlotState


class InternalSetSlotStateOut(BaseModel):
    ok: bool = True
    region: Region
    totem_id: str
    slot: int
    state: SlotState
    backend_response: Optional[Dict[str, Any]] = None


class InternalHealthOut(BaseModel):
    ok: bool = True
    service: str = "order_pickup_service"
    time: datetime
    details: Dict[str, Any] = Field(default_factory=dict)


class QRIn(BaseModel):
    step_index: int
    expires_at: int
    signature: str


class PickupVerifyIn(BaseModel):
    order_id: str
    region: str
    gateway_id: str
    locker_id: str
    porta: int
    qr: QRIn


class PickupVerifyOut(BaseModel):
    ok: bool = True
    decision: str
    reason: Optional[str] = None
    order_id: Optional[str] = None
    slot: Optional[int] = None


class DoorInfo(BaseModel):
    opened_at: Optional[int] = None
    closed_at: Optional[int] = None
    open_ok: bool = True
    close_ok: bool = True


class PickupConfirmIn(BaseModel):
    region: str
    gateway_id: str
    locker_id: str
    porta: int
    door: Optional[DoorInfo] = None


class GatewayEventIn(BaseModel):
    event_id: str
    event_type: str
    created_at: int
    locker_id: str
    porta: Optional[int] = None
    order_id: Optional[str] = None
    request_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)


class EventsBatchIn(BaseModel):
    gateway_id: str
    region: str
    events: List[GatewayEventIn]