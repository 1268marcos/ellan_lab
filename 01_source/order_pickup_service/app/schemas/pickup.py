from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

Region = Literal["SP", "PT"]

PickupStatus = Literal[
    "ACTIVE",
    "REDEEMED",
    "EXPIRED",
    "CANCELLED",
]


class QrPayloadV1(BaseModel):
    v: Literal[1] = 1
    pickup_id: str
    token_id: str
    ctr: int = Field(ge=0)
    exp: int = Field(description="Epoch seconds (expiração total do pickup)")
    sig: str = Field(description="Assinatura gerada no servidor")


# =========================
# Compatibilidade temporária
# =========================

class InternalPaymentConfirmIn(BaseModel):
    region: Region
    sale_id: str
    paid_at: datetime


class InternalPaymentConfirmOut(BaseModel):
    ok: bool = True
    order_id: str
    pickup_id: str
    expires_at: datetime
    qr_rotate_sec: int = 600
    manual_code: str = Field(min_length=6, max_length=8)


class PickupViewOut(BaseModel):
    pickup_id: str
    order_id: str
    region: Region
    status: PickupStatus
    expires_at: datetime
    qr_rotate_sec: int = 600
    token_id: Optional[str] = None
    manual_code_hint: Optional[str] = None


class PickupQrOut(BaseModel):
    qr: QrPayloadV1
    refresh_in_sec: int = Field(ge=0, description="Segundos até a próxima rotação do QR")


class TotemRedeemIn(BaseModel):
    region: Region
    qr: QrPayloadV1


class TotemRedeemManualIn(BaseModel):
    region: Region
    manual_code: str = Field(min_length=6, max_length=8)


class TotemRedeemOut(BaseModel):
    ok: bool = True
    pickup_id: str
    order_id: str
    slot: int = Field(ge=1, le=24)
    action: Literal["OPEN_SLOT"] = "OPEN_SLOT"
    expires_at: datetime


class ApiError(BaseModel):
    ok: bool = False
    type: str
    message: str
    retryable: bool = False
    detail: Optional[dict] = None