from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OnlineRegion(str, Enum):
    SP = "SP"
    PT = "PT"


class OnlinePaymentMethod(str, Enum):
    PIX = "PIX"
    CARTAO = "CARTAO"
    MBWAY = "MBWAY"
    MULTIBANCO_REFERENCE = "MULTIBANCO_REFERENCE"
    NFC = "NFC"
    APPLE_PAY = "APPLE_PAY"
    GOOGLE_PAY = "GOOGLE_PAY"
    MERCADO_PAGO_WALLET = "MERCADO_PAGO_WALLET"


class OnlineCardType(str, Enum):
    CREDIT = "creditCard"
    DEBIT = "debitCard"


class OnlineWalletProvider(str, Enum):
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    MERCADO_PAGO = "mercadoPago"


class CreateOrderIn(BaseModel):
    region: OnlineRegion = Field(..., examples=["SP", "PT"])
    sku_id: str
    totem_id: str = Field(..., description="Identificador da unidade física / locker")
    payment_method: OnlinePaymentMethod
    desired_slot: Optional[int] = Field(default=None, ge=1, le=24)
    amount_cents: Optional[int] = Field(default=None, gt=0)

    card_type: Optional[OnlineCardType] = None
    customer_phone: Optional[str] = Field(default=None, examples=["+351912345678"])
    wallet_provider: Optional[OnlineWalletProvider] = None

    @field_validator("totem_id")
    @classmethod
    def validate_totem_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("totem_id is required")
        return normalized

    @field_validator("sku_id")
    @classmethod
    def validate_sku_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("sku_id is required")
        return normalized

    @field_validator("customer_phone")
    @classmethod
    def normalize_customer_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_payment_context(self) -> "CreateOrderIn":
        if self.payment_method == OnlinePaymentMethod.PIX and self.region != OnlineRegion.SP:
            raise ValueError("PIX só pode ser utilizado na região SP.")

        if self.payment_method == OnlinePaymentMethod.MBWAY:
            if self.region != OnlineRegion.PT:
                raise ValueError("MBWAY só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone is required for MBWAY.")

        if (
            self.payment_method == OnlinePaymentMethod.MULTIBANCO_REFERENCE
            and self.region != OnlineRegion.PT
        ):
            raise ValueError("MULTIBANCO_REFERENCE só pode ser utilizado na região PT.")

        if self.payment_method == OnlinePaymentMethod.CARTAO and not self.card_type:
            raise ValueError("card_type is required when payment_method = CARTAO.")

        if self.payment_method != OnlinePaymentMethod.CARTAO and self.card_type is not None:
            raise ValueError("card_type só pode ser informado quando payment_method = CARTAO.")

        if self.payment_method != OnlinePaymentMethod.MBWAY and self.customer_phone is not None:
            raise ValueError("customer_phone só pode ser informado quando payment_method = MBWAY.")

        if self.payment_method in {
            OnlinePaymentMethod.APPLE_PAY,
            OnlinePaymentMethod.GOOGLE_PAY,
            OnlinePaymentMethod.MERCADO_PAGO_WALLET,
        }:
            if not self.wallet_provider:
                raise ValueError("wallet_provider is required for digital wallets.")

            expected_provider = {
                OnlinePaymentMethod.APPLE_PAY: OnlineWalletProvider.APPLE_PAY,
                OnlinePaymentMethod.GOOGLE_PAY: OnlineWalletProvider.GOOGLE_PAY,
                OnlinePaymentMethod.MERCADO_PAGO_WALLET: OnlineWalletProvider.MERCADO_PAGO,
            }[self.payment_method]

            if self.wallet_provider != expected_provider:
                raise ValueError(
                    f"wallet_provider incompatível com o método {self.payment_method.value}."
                )

        if self.payment_method not in {
            OnlinePaymentMethod.APPLE_PAY,
            OnlinePaymentMethod.GOOGLE_PAY,
            OnlinePaymentMethod.MERCADO_PAGO_WALLET,
        } and self.wallet_provider is not None:
            raise ValueError("wallet_provider só pode ser informado para carteiras digitais.")

        return self


class OrderOut(BaseModel):
    order_id: str
    channel: str
    status: str
    amount_cents: int
    payment_method: Optional[str] = None
    allocation: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class OrderListItemOut(BaseModel):
    order_id: str
    user_id: Optional[str] = None
    region: str
    channel: str
    status: str
    sku_id: str
    totem_id: str
    locker_id: Optional[str] = None
    amount_cents: int
    payment_method: Optional[str] = None

    allocation_id: Optional[str] = None
    slot: Optional[int] = None
    allocation_state: Optional[str] = None

    pickup_id: Optional[str] = None
    pickup_status: Optional[str] = None
    expires_at: Optional[datetime] = None

    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    pickup_deadline_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None


class OrderListOut(BaseModel):
    items: List[OrderListItemOut]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool