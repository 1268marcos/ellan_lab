# 01_source/order_pickup_service/app/schemas/internal.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

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
    "PAID_PENDING_PICKUP",
]

PaymentMethod = Literal[
    "PIX",
    "CARTAO",
    "MBWAY",
    "MULTIBANCO_REFERENCE",
    "NFC",
    "APPLE_PAY",
    "GOOGLE_PAY",
    "MERCADO_PAGO_WALLET",
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

    @field_validator("event_id", "event_type", "order_id")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized

    @field_validator("totem_id")
    @classmethod
    def validate_totem_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("totem_id is required")
        return normalized

    @field_validator("channel", mode="before")
    @classmethod
    def normalize_channel(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in {"ONLINE", "KIOSK"}:
            raise ValueError("channel must be ONLINE or KIOSK")
        return normalized


class InternalPaymentApprovedIn(BaseModel):
    order_id: str
    region: Region
    totem_id: str
    channel: OrderChannel

    provider: PaymentMethod = Field(
        ...,
        description="Método de pagamento efetivamente aprovado. Ex.: PIX, CARTAO, MBWAY.",
    )
    transaction_id: str = Field(..., description="ID da transação no provedor")
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="BRL", description="Moeda informada pelo chamador")

    device_fingerprint: Optional[str] = None
    ip: Optional[str] = None

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("order_id is required")
        return normalized

    @field_validator("totem_id")
    @classmethod
    def validate_totem_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("totem_id is required")
        return normalized

    @field_validator("channel", mode="before")
    @classmethod
    def normalize_channel(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in {"ONLINE", "KIOSK"}:
            raise ValueError("channel must be ONLINE or KIOSK")
        return normalized

    @field_validator("provider", mode="before")
    @classmethod
    def normalize_provider(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("provider is required")
        return normalized

    @field_validator("transaction_id")
    @classmethod
    def validate_transaction_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("transaction_id is required")
        return normalized

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("currency is required")
        return normalized

    @field_validator("device_fingerprint", "ip")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class InternalPaymentApprovedOut(BaseModel):
    ok: bool = True
    order_id: str
    status: OrderStatus
    slot: Optional[int] = None
    message: str


class InternalSetSlotStateIn(BaseModel):
    region: Region
    totem_id: str
    slot: int = Field(..., ge=1, le=24)
    state: SlotState

    @field_validator("totem_id")
    @classmethod
    def validate_totem_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("totem_id is required")
        return normalized


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

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("order_id is required")
        return normalized

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in {"SP", "PT"}:
            raise ValueError("region must be SP or PT")
        return normalized

    @field_validator("locker_id", "gateway_id")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized


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

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in {"SP", "PT"}:
            raise ValueError("region must be SP or PT")
        return normalized

    @field_validator("gateway_id", "locker_id")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized


class GatewayEventIn(BaseModel):
    event_id: str
    event_type: str
    created_at: int
    locker_id: str
    porta: Optional[int] = None
    order_id: Optional[str] = None
    request_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_id", "event_type", "locker_id")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized

    @field_validator("order_id", "request_id")
    @classmethod
    def normalize_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class EventsBatchIn(BaseModel):
    gateway_id: str
    region: str
    events: List[GatewayEventIn]

    @field_validator("gateway_id")
    @classmethod
    def validate_gateway_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("gateway_id is required")
        return normalized

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if normalized not in {"SP", "PT"}:
            raise ValueError("region must be SP or PT")
        return normalized