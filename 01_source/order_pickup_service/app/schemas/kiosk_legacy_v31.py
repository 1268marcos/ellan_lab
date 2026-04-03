# 01_source/order_pickup_service/app/schemas/kiosk.py
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class KioskRegion(str, Enum):
    SP = "SP"
    PT = "PT"


class KioskPaymentMethod(str, Enum):
    PIX = "PIX"
    CARTAO = "CARTAO"
    MBWAY = "MBWAY"
    MULTIBANCO_REFERENCE = "MULTIBANCO_REFERENCE"
    NFC = "NFC"
    APPLE_PAY = "APPLE_PAY"
    GOOGLE_PAY = "GOOGLE_PAY"
    MERCADO_PAGO_WALLET = "MERCADO_PAGO_WALLET"


class KioskCardType(str, Enum):
    CREDIT = "creditCard"
    DEBIT = "debitCard"


class KioskWalletProvider(str, Enum):
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    MERCADO_PAGO = "mercadoPago"


class KioskOrderCreateIn(BaseModel):
    region: KioskRegion = Field(..., examples=["PT"])
    totem_id: str = Field(..., examples=["PT-MAIA-CENTRO-LK-001"])
    sku_id: str = Field(..., examples=["bolo_laranja_algarve"])
    payment_method: KioskPaymentMethod
    # desired_slot: int | None = Field(default=None, ge=1, le=24)
    desired_slot: int | None = Field(
        default=None, 
        ge=1,  # Removeu o le=24
        description="Slot físico do locker (validado dinamicamente no backend)"
    )


    # específicos por método
    card_type: Optional[KioskCardType] = None
    customer_phone: Optional[str] = Field(default=None, examples=["+351912345678"])
    wallet_provider: Optional[KioskWalletProvider] = None

    @field_validator("totem_id")
    @classmethod
    def validate_totem_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("totem_id é obrigatório.")
        return normalized

    @field_validator("sku_id")
    @classmethod
    def validate_sku_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("sku_id é obrigatório.")
        return normalized

    @field_validator("customer_phone")
    @classmethod
    def normalize_customer_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_payment_context(self) -> "KioskOrderCreateIn":
        if self.payment_method == KioskPaymentMethod.PIX and self.region != KioskRegion.SP:
            raise ValueError("PIX só pode ser utilizado na região SP.")

        if self.payment_method == KioskPaymentMethod.MBWAY:
            if self.region != KioskRegion.PT:
                raise ValueError("MBWAY só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para pagamento MBWAY.")

        if (
            self.payment_method == KioskPaymentMethod.MULTIBANCO_REFERENCE
            and self.region != KioskRegion.PT
        ):
            raise ValueError("MULTIBANCO_REFERENCE só pode ser utilizado na região PT.")

        if self.payment_method == KioskPaymentMethod.CARTAO and not self.card_type:
            raise ValueError("card_type é obrigatório para pagamento com CARTAO.")

        if self.payment_method != KioskPaymentMethod.CARTAO and self.card_type is not None:
            raise ValueError("card_type só pode ser informado quando payment_method = CARTAO.")

        if self.payment_method != KioskPaymentMethod.MBWAY and self.customer_phone is not None:
            raise ValueError("customer_phone só pode ser informado quando payment_method = MBWAY.")

        if self.payment_method in {
            KioskPaymentMethod.APPLE_PAY,
            KioskPaymentMethod.GOOGLE_PAY,
            KioskPaymentMethod.MERCADO_PAGO_WALLET,
        }:
            if not self.wallet_provider:
                raise ValueError("wallet_provider é obrigatório para carteiras digitais.")

            expected_provider = {
                KioskPaymentMethod.APPLE_PAY: KioskWalletProvider.APPLE_PAY,
                KioskPaymentMethod.GOOGLE_PAY: KioskWalletProvider.GOOGLE_PAY,
                KioskPaymentMethod.MERCADO_PAGO_WALLET: KioskWalletProvider.MERCADO_PAGO,
            }[self.payment_method]

            if self.wallet_provider != expected_provider:
                raise ValueError(
                    f"wallet_provider incompatível com o método {self.payment_method.value}."
                )

        if self.payment_method not in {
            KioskPaymentMethod.APPLE_PAY,
            KioskPaymentMethod.GOOGLE_PAY,
            KioskPaymentMethod.MERCADO_PAGO_WALLET,
        } and self.wallet_provider is not None:
            raise ValueError(
                "wallet_provider só pode ser informado para carteiras digitais."
            )

        return self


class KioskCustomerIdentifyIn(BaseModel):
    order_id: str
    phone: Optional[str] = Field(default=None, examples=["+351912345678"])
    email: Optional[EmailStr] = None

    @field_validator("order_id")
    @classmethod
    def validate_order_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("order_id é obrigatório.")
        return normalized

    @field_validator("phone")
    @classmethod
    def normalize_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class KioskOrderOut(BaseModel):
    order_id: str
    status: str
    slot: int
    amount_cents: int
    payment_method: str
    allocation_id: str
    ttl_sec: int
    message: str

    # contexto para UX do KIOSK
    payment_status: Optional[str] = None
    payment_instruction_type: Optional[str] = None
    payment_payload: Dict[str, Any] = Field(default_factory=dict)


class KioskPaymentApprovedOut(BaseModel):
    order_id: str
    slot: int
    status: str
    allocation_id: str
    payment_method: str | None = None

    receipt_code: str | None = None
    receipt_print_path: str | None = None
    receipt_json_path: str | None = None

    message: str


class KioskIdentifyOut(BaseModel):
    ok: bool
    message: str