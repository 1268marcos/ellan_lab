from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class KioskPaymentMethod(str, Enum):
    PIX = "PIX"
    CARTAO = "CARTAO"
    MBWAY = "MBWAY"
    NFC = "NFC"


class KioskOrderCreateIn(BaseModel):
    region: str = Field(..., example="PT")
    totem_id: str = Field(..., example="CACIFO-PT-001")
    sku_id: str = Field(..., example="bolo_laranja_algarve")
    payment_method: KioskPaymentMethod
    desired_slot: int | None = Field(default=None, ge=1, le=24)


class KioskCustomerIdentifyIn(BaseModel):
    order_id: str
    phone: Optional[str] = Field(None, example="+351912345678")
    email: Optional[EmailStr] = None


class KioskOrderOut(BaseModel):
    order_id: str
    status: str
    slot: int
    amount_cents: int
    payment_method: str
    allocation_id: str
    ttl_sec: int
    message: str


class KioskPaymentApprovedOut(BaseModel):
    order_id: str
    slot: int
    status: str
    allocation_id: str
    payment_method: Optional[str] = None
    message: str


class KioskIdentifyOut(BaseModel):
    ok: bool
    message: str