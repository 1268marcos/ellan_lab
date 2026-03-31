# 01_source/order_pickup_service/app/schemas/pickup.py

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

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

    @field_validator("pickup_id", "token_id", "sig")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized


class QrPayloadV2(BaseModel):
    v: Literal[2] = 2
    pickup_id: str
    token_id: str
    locker_id: str
    region: Region
    ctr: int = Field(ge=0)
    exp: int = Field(description="Epoch seconds (expiração total do pickup)")
    sig: str = Field(description="Assinatura gerada no servidor")

    @field_validator("pickup_id", "token_id", "sig")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("field is required")
        return normalized

    @field_validator("locker_id")
    @classmethod
    def validate_locker_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("locker_id is required")
        return normalized


QrPayload = QrPayloadV1 | QrPayloadV2


# =========================
# Compatibilidade temporária
# =========================

class InternalPaymentConfirmIn(BaseModel):
    region: Region
    sale_id: str
    paid_at: datetime

    @field_validator("sale_id")
    @classmethod
    def validate_sale_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("sale_id is required")
        return normalized


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
    qr: QrPayload
    refresh_in_sec: int = Field(ge=0, description="Segundos até a próxima rotação do QR")


class TotemRedeemIn(BaseModel):
    region: Region
    locker_id: str = Field(..., min_length=1)
    qr: QrPayload

    @field_validator("locker_id")
    @classmethod
    def validate_locker_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("locker_id is required")
        return normalized


class TotemRedeemManualIn(BaseModel):
    region: Region
    locker_id: str = Field(..., min_length=1)
    manual_code: str = Field(min_length=6, max_length=8)

    @field_validator("locker_id")
    @classmethod
    def validate_locker_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("locker_id is required")
        return normalized

    @field_validator("manual_code")
    @classmethod
    def normalize_manual_code(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("manual_code is required")
        return normalized


class TotemRedeemOut(BaseModel):
    ok: bool = True
    pickup_id: str
    order_id: str
    locker_id: str
    slot: int = Field(ge=1, le=24)
    action: Literal["OPEN_SLOT"] = "OPEN_SLOT"
    expires_at: datetime


class ApiError(BaseModel):
    ok: bool = False
    type: str
    message: str
    retryable: bool = False
    detail: Optional[dict] = None