# 01_source/order_pickup_service/app/schemas/kiosk.py
# 02/04/2026
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class KioskRegion(str, Enum):
    SP = "SP"
    PT = "PT"


class KioskSalesChannel(str, Enum):
    KIOSK = "kiosk"


class KioskFulfillmentType(str, Enum):
    INSTANT = "instant"


class KioskPaymentMethod(str, Enum):
    CREDIT_CARD = "creditCard"
    DEBIT_CARD = "debitCard"
    GIFT_CARD = "giftCard"
    PIX = "pix"
    MBWAY = "mbway"
    MULTIBANCO_REFERENCE = "multibanco_reference"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    MERCADO_PAGO_WALLET = "mercado_pago_wallet"


class KioskPaymentInterface(str, Enum):
    NFC = "nfc"
    QR_CODE = "qr_code"
    CHIP = "chip"
    WEB_TOKEN = "web_token"
    MANUAL = "manual"


class KioskWalletProvider(str, Enum):
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    MERCADO_PAGO = "mercadoPago"


class KioskOrderCreateIn(BaseModel):
    region: KioskRegion = Field(..., examples=["PT"])
    sales_channel: KioskSalesChannel = Field(default=KioskSalesChannel.KIOSK)
    fulfillment_type: KioskFulfillmentType = Field(default=KioskFulfillmentType.INSTANT)

    totem_id: str = Field(..., examples=["PT-MAIA-CENTRO-LK-001"])
    sku_id: str = Field(..., examples=["bolo_laranja_algarve"])

    payment_method: KioskPaymentMethod
    payment_interface: KioskPaymentInterface

    desired_slot: int | None = Field(
        default=None,
        ge=1,
        description="Slot físico do locker (validado dinamicamente no backend/runtime)",
    )

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
        if self.sales_channel != KioskSalesChannel.KIOSK:
            raise ValueError("sales_channel inválido para KIOSK.")

        if self.fulfillment_type != KioskFulfillmentType.INSTANT:
            raise ValueError("fulfillment_type inválido para pedido KIOSK.")

        if self.payment_method == KioskPaymentMethod.PIX and self.region != KioskRegion.SP:
            raise ValueError("pix só pode ser utilizado na região SP.")

        if self.payment_method == KioskPaymentMethod.MBWAY:
            if self.region != KioskRegion.PT:
                raise ValueError("mbway só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para pagamento mbway.")

        if self.payment_method == KioskPaymentMethod.MULTIBANCO_REFERENCE and self.region != KioskRegion.PT:
            raise ValueError("multibanco_reference só pode ser utilizado na região PT.")

        if self.payment_method in {
            KioskPaymentMethod.CREDIT_CARD,
            KioskPaymentMethod.DEBIT_CARD,
            KioskPaymentMethod.GIFT_CARD,
        } and self.payment_interface not in {
            KioskPaymentInterface.CHIP,
            KioskPaymentInterface.NFC,
            KioskPaymentInterface.MANUAL,
        }:
            raise ValueError(
                f"payment_interface incompatível com o método {self.payment_method.value}."
            )

        if self.payment_method == KioskPaymentMethod.PIX and self.payment_interface != KioskPaymentInterface.QR_CODE:
            raise ValueError("pix no kiosk exige payment_interface = qr_code.")

        if self.payment_method == KioskPaymentMethod.MBWAY and self.payment_interface not in {
            KioskPaymentInterface.QR_CODE,
            KioskPaymentInterface.WEB_TOKEN,
        }:
            raise ValueError("mbway exige payment_interface qr_code ou web_token.")

        if self.payment_method == KioskPaymentMethod.MULTIBANCO_REFERENCE and self.payment_interface not in {
            KioskPaymentInterface.QR_CODE,
            KioskPaymentInterface.MANUAL,
        }:
            raise ValueError("multibanco_reference exige payment_interface qr_code ou manual.")

        if self.payment_method in {
            KioskPaymentMethod.APPLE_PAY,
            KioskPaymentMethod.GOOGLE_PAY,
            KioskPaymentMethod.MERCADO_PAGO_WALLET,
        }:
            if self.payment_interface not in {
                KioskPaymentInterface.NFC,
                KioskPaymentInterface.WEB_TOKEN,
                KioskPaymentInterface.QR_CODE,
            }:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.payment_method.value}."
                )

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
            raise ValueError("wallet_provider só pode ser informado para carteiras digitais.")

        if self.payment_method != KioskPaymentMethod.MBWAY and self.customer_phone is not None:
            raise ValueError("customer_phone só pode ser informado quando payment_method = mbway.")

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
    payment_interface: Optional[str] = None
    allocation_id: str
    ttl_sec: int
    message: str

    payment_status: Optional[str] = None
    payment_instruction_type: Optional[str] = None
    payment_payload: Dict[str, Any] = Field(default_factory=dict)


class KioskPaymentApprovedOut(BaseModel):
    order_id: str
    slot: int
    status: str
    allocation_id: str
    payment_method: str | None = None
    payment_interface: str | None = None

    receipt_code: str | None = None
    receipt_print_path: str | None = None
    receipt_json_path: str | None = None

    message: str


class KioskIdentifyOut(BaseModel):
    ok: bool
    message: str