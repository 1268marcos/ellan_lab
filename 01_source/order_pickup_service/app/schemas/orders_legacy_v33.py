# 01_source/order_pickup_service/app/schemas/orders.py
# 02/04/2026

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OnlineRegion(str, Enum):
    # América Latina
    SP = "SP"  # São Paulo - Brasil
    RJ = "RJ"  # Rio de Janeiro - Brasil
    MG = "MG"  # Minas Gerais - Brasil
    RS = "RS"  # Rio Grande do Sul - Brasil
    BA = "BA"  # Bahia - Brasil
    MX = "MX"  # México
    AR = "AR"  # Argentina
    CO = "CO"  # Colômbia
    CL = "CL"  # Chile
    PE = "PE"  # Peru
    EC = "EC"  # Equador
    UY = "UY"  # Uruguai
    PY = "PY"  # Paraguai
    BO = "BO"  # Bolívia
    VE = "VE"  # Venezuela
    CR = "CR"  # Costa Rica
    PA = "PA"  # Panamá
    DO = "DO"  # República Dominicana
    
    # América do Norte
    US_NY = "US_NY"  # Nova York - EUA
    US_CA = "US_CA"  # Califórnia - EUA
    US_TX = "US_TX"  # Texas - EUA
    US_FL = "US_FL"  # Flórida - EUA
    US_IL = "US_IL"  # Illinois - EUA
    CA_ON = "CA_ON"  # Ontário - Canadá
    CA_QC = "CA_QC"  # Quebec - Canadá
    CA_BC = "CA_BC"  # British Columbia - Canadá
    
    # Europa
    PT = "PT"  # Portugal
    ES = "ES"  # Espanha
    FR = "FR"  # França
    DE = "DE"  # Alemanha
    UK = "UK"  # Reino Unido
    IT = "IT"  # Itália
    NL = "NL"  # Holanda
    BE = "BE"  # Bélgica
    CH = "CH"  # Suíça
    SE = "SE"  # Suécia
    NO = "NO"  # Noruega
    DK = "DK"  # Dinamarca
    FI = "FI"  # Finlândia
    IE = "IE"  # Irlanda
    AT = "AT"  # Áustria
    PL = "PL"  # Polônia
    CZ = "CZ"  # República Tcheca
    GR = "GR"  # Grécia
    HU = "HU"  # Hungria
    RO = "RO"  # Romênia
    
    # África
    ZA = "ZA"  # África do Sul
    NG = "NG"  # Nigéria
    KE = "KE"  # Quênia
    EG = "EG"  # Egito
    MA = "MA"  # Marrocos
    GH = "GH"  # Gana
    SN = "SN"  # Senegal
    CI = "CI"  # Costa do Marfim
    TZ = "TZ"  # Tanzânia
    UG = "UG"  # Uganda
    RW = "RW"  # Ruanda
    MZ = "MZ"  # Moçambique
    AO = "AO"  # Angola
    DZ = "DZ"  # Argélia
    TN = "TN"  # Tunísia


class OnlineSalesChannel(str, Enum):
    ONLINE = "online"
    MARKETPLACE = "marketplace"
    SOCIAL_COMMERCE = "social_commerce"  # Vendas via redes sociais
    APP_STORE = "app_store"              # Loja de aplicativos
    IN_APP = "in_app"                    # Compras dentro do aplicativo
    WHATSAPP = "whatsapp"                # Vendas via WhatsApp
    INSTAGRAM = "instagram"              # Vendas via Instagram
    FACEBOOK = "facebook"                # Vendas via Facebook
    TIKTOK = "tiktok"                    # Vendas via TikTok
    TELEGRAM = "telegram"                # Vendas via Telegram


class OnlineFulfillmentType(str, Enum):
    RESERVATION = "reservation"
    DIGITAL_DELIVERY = "digital_delivery"              # Entrega digital
    PHYSICAL_DELIVERY = "physical_delivery"            # Entrega física
    PICKUP_POINT = "pickup_point"                      # Retirada em ponto de coleta
    LOCKER = "locker"                                  # Retirada em lockers
    SAME_DAY = "same_day"                              # Entrega no mesmo dia
    SCHEDULED = "scheduled"                            # Entrega agendada
    INSTANT = "instant"                                # Entrega instantânea (até 2h)
    INTERNATIONAL_SHIPPING = "international_shipping"  # Envio internacional


class OnlinePaymentMethod(str, Enum):
    # Cartões
    CREDIT_CARD = "creditCard"
    DEBIT_CARD = "debitCard"
    PREPAID_CARD = "prepaidCard"
    GIFT_CARD = "giftCard"
    
    # Brasil
    PIX = "pix"
    BOLETO = "boleto"
    
    # América Latina
    MERCADO_PAGO_WALLET = "mercado_pago_wallet"
    MERCADO_CREDITO = "mercado_credito"
    OXXO = "oxxo"  # México
    SPEI = "spei"  # México - transferência bancária
    RAPIPAGO = "rapipago"  # Argentina
    PAGOFACIL = "pagofacil"  # Argentina
    SERVIPAG = "servipag"  # Chile
    KHIPU = "khipu"  # Chile
    EFECTY = "efecty"  # Colômbia
    PSE = "pse"  # Colômbia
    
    # América do Norte
    ACH = "ach"  # EUA - transferência bancária
    VENMO = "venmo"  # EUA
    CASHAPP = "cashapp"  # EUA
    ZELLE = "zelle"  # EUA
    AFTERPAY = "afterpay"  # EUA
    AFFIRM = "affirm"  # EUA
    KLARNA_US = "klarna_us"  # EUA
    INTERAC = "interac"  # Canadá
    
    # Europa
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    MBWAY = "mbway"  # Portugal
    MULTIBANCO_REFERENCE = "multibanco_reference"  # Portugal
    SOFORT = "sofort"  # Alemanha, Áustria, Bélgica
    GIROPAY = "giropay"  # Alemanha
    KLARNA = "klarna"  # Suécia, Alemanha, Holanda
    TRUSTLY = "trustly"  # Suécia
    IDEAL = "ideal"  # Holanda
    BANCONTACT = "bancontact"  # Bélgica
    TWINT = "twint"  # Suíça
    VIABILL = "viabill"  # Dinamarca
    MOBILEPAY = "mobilepay"  # Dinamarca, Finlândia
    VIPS = "vips"  # Noruega
    BLIK = "blik"  # Polônia
    PRZELEWY24 = "przelewy24"  # Polônia
    SATISPAY = "satispay"  # Itália
    SEPA = "sepa"  # União Europeia
    
    # Reino Unido
    PAYPAL = "paypal"
    GOOGLE_PAY_UK = "google_pay_uk"
    APPLE_PAY_UK = "apple_pay_uk"
    FASTER_PAYMENTS = "faster_payments"
    BACS = "bacs"
    CLEARPAY = "clearpay"
    MONZO = "monzo"
    REVOLUT = "revolut"
    
    # África
    M_PESA = "m_pesa"  # Quênia, Tanzânia, Egito
    AIRTEL_MONEY = "airtel_money"  # Nigéria, Quênia, Uganda
    MTN_MONEY = "mtn_money"  # Gana, Costa do Marfim, Uganda
    ORANGE_MONEY = "orange_money"  # Senegal, Costa do Marfim
    VODAFONE_CASH = "vodafone_cash"  # Egito, Gana
    TELECASH = "telecash"  # Moçambique
    ECONET = "econet"  # Zimbábue
    PAYSTACK = "paystack"  # Nigéria, Gana, África do Sul
    FLUTTERWAVE = "flutterwave"  # Nigéria, Quênia, África do Sul
    YOCO = "yoco"  # África do Sul
    PEACH_PAYMENTS = "peach_payments"  # África do Sul
    SNOOPY = "snoopy"  # Angola
    UNITEL_MONEY = "unitel_money"  # Angola
    MOOV_MONEY = "moov_money"  # Costa do Marfim
    
    # Wallet globais
    CRYPTO = "crypto"  # Bitcoin, Ethereum, etc.
    CASH_ON_DELIVERY = "cash_on_delivery"
    BANK_TRANSFER = "bank_transfer"
    DIRECT_DEBIT = "direct_debit"


class OnlinePaymentInterface(str, Enum):
    # Interfaces físicas
    NFC = "nfc"
    CHIP = "chip"
    MAGNETIC_STRIPE = "magnetic_stripe"
    CONTACTLESS = "contactless"
    BIOMETRIC = "biometric"
    
    # Interfaces digitais
    QR_CODE = "qr_code"
    WEB_TOKEN = "web_token"
    DEEP_LINK = "deep_link"
    API = "api"
    SDK = "sdk"
    WEBHOOK = "webhook"
    
    # Interfaces manuais
    MANUAL = "manual"
    COD = "cod"  # Cash on Delivery
    POS = "pos"  # Point of Sale
    
    # Interfaces específicas por região
    USSD = "ussd"  # África - USSD codes
    SMS = "sms"  # África - SMS payments
    VOICE = "voice"  # Voice payments
    QR_BILL = "qr_bill"  # Suíça - QR Bill
    BANK_LINK = "bank_link"  # Holanda - iDEAL link


class OnlineWalletProvider(str, Enum):
    # Internacionais
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    SAMSUNG_PAY = "samsungPay"
    PAYPAL = "paypal"
    
    # América Latina
    MERCADO_PAGO = "mercadoPago"
    PICPAY = "picpay"  # Brasil
    RAPPI = "rappi"  # México, Colômbia
    NEQUI = "nequi"  # Colômbia
    YAPE = "yape"  # Peru
    PLIN = "plin"  # Peru
    
    # América do Norte
    VENMO = "venmo"
    CASHAPP = "cashapp"
    ZELLE = "zelle"
    CHIME = "chime"
    
    # Europa
    REVOLUT = "revolut"
    N26 = "n26"
    MONZO = "monzo"
    WISE = "wise"
    MBWAY = "mbway"  # Portugal
    TWINT = "twint"  # Suíça
    VIABILL = "viabill"  # Dinamarca
    MOBILEPAY = "mobilepay"  # Países Nórdicos
    SATISPAY = "satispay"  # Itália
    BLIK = "blik"  # Polônia
    
    # África
    M_PESA = "mPesa"
    AIRTEL_MONEY = "airtelMoney"
    MTN_MONEY = "mtnMoney"
    ORANGE_MONEY = "orangeMoney"
    VODAFONE_CASH = "vodafoneCash"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    YOCO = "yoco"
    KCB_MOBILE = "kcbMobile"  # Quênia
    TIGOPESA = "tigopesa"  # Tanzânia
    
    # China/Ásia (para mercados asiáticos relevantes)
    ALIPAY = "alipay"
    WECHAT_PAY = "wechatPay"


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
    has_prev: booly