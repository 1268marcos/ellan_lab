# 01_source/payment_gateway/app/models/payment_model.py
# 02/04/2026

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


RegionType = Literal["SP", "PT"]
ChannelType = Literal["ONLINE", "KIOSK"]

PaymentMethodType = Literal[
    "creditCard",
    "debitCard",
    "giftCard",
    "pix",
    "boleto",
    "apple_pay",
    "google_pay",
    "mbway",
    "multibanco_reference",
    "mercado_pago_wallet",
]

PaymentInterfaceType = Literal[
    "nfc",
    "qr_code",
    "chip",
    "web_token",
    "manual",
]

WalletProviderType = Literal["applePay", "googlePay", "mercadoPago"]


class PaymentRequest(BaseModel):
    regiao: RegionType
    canal: ChannelType

    porta: int = Field(
        ge=1,
        description="Porta/Número do slot (validado dinamicamente no backend)",
    )

    metodo: PaymentMethodType
    interface: PaymentInterfaceType
    valor: float = Field(gt=0)

    currency: Optional[str] = None

    locker_id: str = Field(..., description="Identificador da unidade física / locker")
    order_id: Optional[str] = None

    customer_phone: Optional[str] = None
    wallet_provider: Optional[WalletProviderType] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("locker_id")
    @classmethod
    def validate_locker_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("locker_id é obrigatório.")
        return normalized

    @field_validator("order_id")
    @classmethod
    def normalize_order_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("customer_phone")
    @classmethod
    def normalize_customer_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().upper()
        return normalized or None

    @model_validator(mode="after")
    def validate_payment_request(self) -> "PaymentRequest":
        if not self.currency:
            self.currency = "BRL" if self.regiao == "SP" else "EUR"

        if self.metodo == "pix" and self.regiao != "SP":
            raise ValueError("pix só pode ser utilizado na região SP.")

        if self.metodo == "boleto" and self.regiao != "SP":
            raise ValueError("boleto só pode ser utilizado na região SP.")

        if self.metodo == "mbway":
            if self.regiao != "PT":
                raise ValueError("mbway só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para pagamentos mbway.")

        if self.metodo == "multibanco_reference" and self.regiao != "PT":
            raise ValueError("multibanco_reference só pode ser utilizado na região PT.")

        if self.metodo in {"apple_pay", "google_pay", "mercado_pago_wallet"}:
            if not self.wallet_provider:
                raise ValueError("wallet_provider é obrigatório para carteiras digitais.")

            expected_provider = {
                "apple_pay": "applePay",
                "google_pay": "googlePay",
                "mercado_pago_wallet": "mercadoPago",
            }[self.metodo]

            if self.wallet_provider != expected_provider:
                raise ValueError(
                    f"wallet_provider incompatível com o método {self.metodo}."
                )

        if self.metodo not in {"apple_pay", "google_pay", "mercado_pago_wallet"} and self.wallet_provider is not None:
            raise ValueError("wallet_provider só pode ser informado para carteiras digitais.")

        if self.metodo in {"creditCard", "debitCard", "giftCard"} and self.interface not in {
            "nfc",
            "chip",
            "web_token",
            "manual",
        }:
            raise ValueError(f"payment_interface incompatível com o método {self.metodo}.")

        if self.metodo == "pix" and self.interface not in {"qr_code", "web_token"}:
            raise ValueError("pix exige interface qr_code ou web_token.")

        if self.metodo == "boleto" and self.interface not in {"qr_code", "web_token", "manual"}:
            raise ValueError("boleto exige interface qr_code, web_token ou manual.")

        if self.metodo == "mbway" and self.interface not in {"qr_code", "web_token"}:
            raise ValueError("mbway exige interface qr_code ou web_token.")

        if self.metodo == "multibanco_reference" and self.interface not in {"qr_code", "manual", "web_token"}:
            raise ValueError("multibanco_reference exige interface qr_code, manual ou web_token.")

        return self    

