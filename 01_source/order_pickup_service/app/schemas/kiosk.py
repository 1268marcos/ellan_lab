from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from enum import Enum


# =========================
# ENUMS
# =========================

class KioskPaymentMethod(str, Enum):
    PIX = "PIX"
    CARTAO = "CARTAO"
    MBWAY = "MBWAY"
    NFC = "NFC"


# =========================
# INPUT – CRIAR PEDIDO PRESENCIAL
# =========================

class KioskOrderCreateIn(BaseModel):
    region: str = Field(..., example="PT")
    totem_id: str = Field(..., example="CACIFO-PT-001")
    sku_id: str = Field(..., example="BOLO_LARANJA")
    payment_method: KioskPaymentMethod


# =========================
# INPUT – IDENTIFICAÇÃO OPCIONAL (pós pagamento)
# =========================

class KioskCustomerIdentifyIn(BaseModel):
    order_id: str
    phone: Optional[str] = Field(None, example="+351912345678")
    email: Optional[EmailStr] = None


# =========================
# OUTPUT – PEDIDO PRESENCIAL
# =========================

class KioskOrderOut(BaseModel):
    order_id: str
    status: str
    slot: int
    amount_cents: int
    message: str


# =========================
# OUTPUT – PAGAMENTO APROVADO
# =========================

class KioskPaymentApprovedOut(BaseModel):
    order_id: str
    slot: int
    status: str
    message: str


# =========================
# OUTPUT – IDENTIFICAÇÃO OK
# =========================

class KioskIdentifyOut(BaseModel):
    ok: bool
    message: str