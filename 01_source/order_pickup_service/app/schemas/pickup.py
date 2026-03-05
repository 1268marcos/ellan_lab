from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

# -----------------------------
# Shared / Enums
# -----------------------------

Region = Literal["SP", "PT"]

PickupStatus = Literal[
    "ACTIVE",
    "REDEEMED",
    "EXPIRED",
    "CANCELLED",
]

# Payload que vai dentro do QR (NUNCA coloca dados pessoais aqui)
class QrPayloadV1(BaseModel):
    v: Literal[1] = 1
    pickup_id: str
    token_id: str
    ctr: int = Field(ge=0)
    exp: int = Field(description="Epoch seconds (expiração total do pickup)")
    sig: str = Field(description="Assinatura gerada no servidor (base64url ou hex)")

# -----------------------------
# Internal: payment confirm -> cria pickup
# -----------------------------

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

# -----------------------------
# Client: view pickup & get QR
# -----------------------------

class PickupViewOut(BaseModel):
    pickup_id: str
    order_id: str
    region: Region
    status: PickupStatus
    expires_at: datetime
    qr_rotate_sec: int = 600

    # Só referência (não precisa expor sempre; deixe None se quiser esconder)
    token_id: Optional[str] = None

    # Opcional: hint do código manual sem expor completo (ex.: "***931")
    manual_code_hint: Optional[str] = Field(
        default=None,
        description="Opcional: dica parcial do código manual, sem revelar completo",
    )

class PickupQrOut(BaseModel):
    qr: QrPayloadV1
    refresh_in_sec: int = Field(ge=0, description="Segundos até a próxima rotação do QR")

# -----------------------------
# Totem: redeem via QR / manual
# -----------------------------

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

# -----------------------------
# Standard error shape (opcional)
# -----------------------------

class ApiError(BaseModel):
    ok: bool = False
    type: str
    message: str
    retryable: bool = False
    detail: Optional[dict] = None

# -----------------------------
# Backward compatibility (TEMP)
# -----------------------------
# Alguns routers antigos ainda importam RedeemIn.
# Mantenha isso só até atualizar app/routers/pickup.py para TotemRedeemIn/TotemRedeemManualIn.

# class RedeemIn(BaseModel):
#     region: Region
#     pickup_code: str = Field(min_length=6, max_length=8)
#     order_id: Optional[str] = None