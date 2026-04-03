# 01_source/order_pickup_service/app/schemas/orders.py
# 02/04/2026 - resposta chatgpt

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OnlineRegion(str, Enum):
    SP = "SP"
    PT = "PT"


class OnlineSalesChannel(str, Enum):
    ONLINE = "online"


class OnlineFulfillmentType(str, Enum):
    RESERVATION = "reservation"


class OnlinePaymentMethod(str, Enum):
    CREDIT_CARD = "creditCard"
    DEBIT_CARD = "debitCard"
    GIFT_CARD = "giftCard"
    PIX = "pix"
    BOLETO = "boleto"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    MBWAY = "mbway"
    MULTIBANCO_REFERENCE = "multibanco_reference"
    MERCADO_PAGO_WALLET = "mercado_pago_wallet"


class OnlinePaymentInterface(str, Enum):
    NFC = "nfc"
    QR_CODE = "qr_code"
    CHIP = "chip"
    WEB_TOKEN = "web_token"
    MANUAL = "manual"


class OnlineWalletProvider(str, Enum):
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    MERCADO_PAGO = "mercadoPago"


class CreateOrderIn(BaseModel):
    region: OnlineRegion = Field(..., examples=["SP", "PT"])
    sales_channel: OnlineSalesChannel = Field(default=OnlineSalesChannel.ONLINE)
    fulfillment_type: OnlineFulfillmentType = Field(default=OnlineFulfillmentType.RESERVATION)

    sku_id: str
    totem_id: str = Field(..., description="Identificador da unidade física / locker")

    payment_method: OnlinePaymentMethod
    payment_interface: OnlinePaymentInterface

    desired_slot: Optional[int] = Field(
        default=None,
        ge=1,
        description="Slot físico do locker (validado dinamicamente no backend/runtime)",
    )
    amount_cents: Optional[int] = Field(default=None, gt=0)

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
        if self.sales_channel != OnlineSalesChannel.ONLINE:
            raise ValueError("sales_channel inválido para CreateOrderIn.")

        if self.fulfillment_type != OnlineFulfillmentType.RESERVATION:
            raise ValueError("fulfillment_type inválido para pedido ONLINE.")

        if self.payment_method == OnlinePaymentMethod.PIX and self.region != OnlineRegion.SP:
            raise ValueError("pix só pode ser utilizado na região SP.")

        if self.payment_method == OnlinePaymentMethod.BOLETO and self.region != OnlineRegion.SP:
            raise ValueError("boleto só pode ser utilizado na região SP.")

        if self.payment_method == OnlinePaymentMethod.MBWAY:
            if self.region != OnlineRegion.PT:
                raise ValueError("mbway só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone is required for mbway.")

        if self.payment_method == OnlinePaymentMethod.MULTIBANCO_REFERENCE and self.region != OnlineRegion.PT:
            raise ValueError("multibanco_reference só pode ser utilizado na região PT.")

        if self.payment_method in {
            OnlinePaymentMethod.APPLE_PAY,
            OnlinePaymentMethod.GOOGLE_PAY,
            OnlinePaymentMethod.MERCADO_PAGO_WALLET,
        }:
            if self.payment_interface not in {
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.QR_CODE,
                OnlinePaymentInterface.NFC,
            }:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.payment_method.value}."
                )

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

        if self.payment_method in {
            OnlinePaymentMethod.CREDIT_CARD,
            OnlinePaymentMethod.DEBIT_CARD,
            OnlinePaymentMethod.GIFT_CARD,
        }:
            if self.payment_interface not in {
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.MANUAL,
                OnlinePaymentInterface.CHIP,
                OnlinePaymentInterface.NFC,
            }:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.payment_method.value}."
                )

        if self.payment_method == OnlinePaymentMethod.PIX and self.payment_interface not in {
            OnlinePaymentInterface.QR_CODE,
            OnlinePaymentInterface.WEB_TOKEN,
        }:
            raise ValueError("pix exige payment_interface qr_code ou web_token.")

        if self.payment_method == OnlinePaymentMethod.BOLETO and self.payment_interface not in {
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
        }:
            raise ValueError("boleto exige payment_interface web_token ou qr_code.")

        if self.payment_method == OnlinePaymentMethod.MBWAY and self.payment_interface not in {
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
        }:
            raise ValueError("mbway exige payment_interface web_token ou qr_code.")

        if self.payment_method == OnlinePaymentMethod.MULTIBANCO_REFERENCE and self.payment_interface not in {
            OnlinePaymentInterface.WEB_TOKEN,
            OnlinePaymentInterface.QR_CODE,
        }:
            raise ValueError("multibanco_reference exige payment_interface web_token ou qr_code.")

        return self


class OrderOut(BaseModel):
    order_id: str
    channel: str
    status: str
    amount_cents: int
    payment_method: Optional[str] = None
    payment_interface: Optional[str] = None
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
    payment_interface: Optional[str] = None

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