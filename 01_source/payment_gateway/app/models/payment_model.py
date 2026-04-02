from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


RegionType = Literal["SP", "PT"]
ChannelType = Literal["ONLINE", "KIOSK"]

PaymentMethodType = Literal[
    "PIX",
    "CARTAO",
    "MBWAY",
    "MULTIBANCO_REFERENCE",
    "NFC",
    "APPLE_PAY",
    "GOOGLE_PAY",
    "MERCADO_PAGO_WALLET",
]

CardType = Literal["creditCard", "debitCard"]
WalletProviderType = Literal["applePay", "googlePay", "mercadoPago"]


class PaymentRequest(BaseModel):
    regiao: RegionType
    canal: ChannelType
    # porta: int = Field(ge=1, le=24)
    porta: int = Field(
        ge=1, 
        description="Porta/Número do slot (validado dinamicamente no backend)"
    )
    metodo: PaymentMethodType
    valor: float = Field(gt=0)

    # moeda padrão por região
    currency: Optional[str] = None

    # contexto operacional / correlação
    locker_id: str = Field(..., description="Identificador da unidade física / locker")
    order_id: Optional[str] = None

    # específicos de método
    card_type: Optional[CardType] = None
    customer_phone: Optional[str] = None
    wallet_provider: Optional[WalletProviderType] = None

    # espaço controlado para extensões futuras
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

        if self.metodo == "PIX" and self.regiao != "SP":
            raise ValueError("PIX só pode ser utilizado na região SP.")

        if self.metodo == "MBWAY":
            if self.regiao != "PT":
                raise ValueError("MBWAY só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para pagamentos MBWAY.")

        if self.metodo != "MBWAY" and self.customer_phone is not None:
            raise ValueError(
                "customer_phone só pode ser informado quando metodo = MBWAY."
            )

        if self.metodo == "MULTIBANCO_REFERENCE" and self.regiao != "PT":
            raise ValueError("MULTIBANCO_REFERENCE só pode ser utilizado na região PT.")

        if self.metodo == "CARTAO" and not self.card_type:
            raise ValueError("card_type é obrigatório para pagamentos com CARTAO.")

        if self.metodo != "CARTAO" and self.card_type is not None:
            raise ValueError("card_type só pode ser informado quando metodo = CARTAO.")

        if self.metodo in {"APPLE_PAY", "GOOGLE_PAY", "MERCADO_PAGO_WALLET"}:
            if not self.wallet_provider:
                raise ValueError("wallet_provider é obrigatório para carteiras digitais.")

            expected_provider = {
                "APPLE_PAY": "applePay",
                "GOOGLE_PAY": "googlePay",
                "MERCADO_PAGO_WALLET": "mercadoPago",
            }[self.metodo]

            if self.wallet_provider != expected_provider:
                raise ValueError(
                    f"wallet_provider incompatível com o método {self.metodo}."
                )

        if self.metodo not in {"APPLE_PAY", "GOOGLE_PAY", "MERCADO_PAGO_WALLET"} and self.wallet_provider is not None:
            raise ValueError(
                "wallet_provider só pode ser informado para carteiras digitais."
            )

        return self