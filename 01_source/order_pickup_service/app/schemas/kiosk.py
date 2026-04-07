# 01_source/order_pickup_service/app/schemas/kiosk.py
# Corrigido para aceitar UI_CODE no backend
# Corrigido para normalizar automaticamente payment_method/payment_interface
# Corrigido para não quebrar o router atual
# 06/04/2026 - Remoção dicionários hardcoded do schema

from __future__ import annotations

# from enum import Enum
# from typing import Any, Dict, Optional
from enum import Enum
from typing import Any, Dict, Optional, List
from re import compile as re_compile

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class KioskRegion(str, Enum):
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
    
    # Europa Ocidental
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
    
    # Europa Oriental
    PL = "PL"  # Polônia
    CZ = "CZ"  # República Tcheca
    GR = "GR"  # Grécia
    HU = "HU"  # Hungria
    RO = "RO"  # Romênia
    RU = "RU"  # Rússia
    TR = "TR"  # Turquia
    
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
    
    # Ásia - Leste Asiático
    CN = "CN"  # China
    JP = "JP"  # Japão
    KR = "KR"  # Coreia do Sul
    
    # Ásia - Sudeste Asiático
    TH = "TH"  # Tailândia
    ID = "ID"  # Indonésia
    SG = "SG"  # Singapura
    PH = "PH"  # Filipinas
    VN = "VN"  # Vietnã
    MY = "MY"  # Malásia
    
    # Oriente Médio
    AE = "AE"  # Emirados Árabes Unidos
    SA = "SA"  # Arábia Saudita
    QA = "QA"  # Qatar
    KW = "KW"  # Kuwait
    BH = "BH"  # Bahrein
    OM = "OM"  # Omã
    JO = "JO"  # Jordânia
    
    # Oceania
    AU = "AU"  # Austrália
    NZ = "NZ"  # Nova Zelândia

    @classmethod
    def get_continent(cls, region: "KioskRegion") -> str:
        """Retorna o continente baseado na região"""
        latin_america = {cls.SP, cls.RJ, cls.MG, cls.RS, cls.BA, cls.MX, cls.AR, 
                        cls.CO, cls.CL, cls.PE, cls.EC, cls.UY, cls.PY, cls.BO, 
                        cls.VE, cls.CR, cls.PA, cls.DO}
        north_america = {cls.US_NY, cls.US_CA, cls.US_TX, cls.US_FL, cls.US_IL,
                        cls.CA_ON, cls.CA_QC, cls.CA_BC}
        western_europe = {cls.PT, cls.ES, cls.FR, cls.DE, cls.UK, cls.IT, cls.NL, 
                         cls.BE, cls.CH, cls.SE, cls.NO, cls.DK, cls.FI, cls.IE, cls.AT}
        eastern_europe = {cls.PL, cls.CZ, cls.GR, cls.HU, cls.RO, cls.RU, cls.TR}
        africa = {cls.ZA, cls.NG, cls.KE, cls.EG, cls.MA, cls.GH, cls.SN, cls.CI,
                 cls.TZ, cls.UG, cls.RW, cls.MZ, cls.AO, cls.DZ, cls.TN}
        east_asia = {cls.CN, cls.JP, cls.KR}
        southeast_asia = {cls.TH, cls.ID, cls.SG, cls.PH, cls.VN, cls.MY}
        middle_east = {cls.AE, cls.SA, cls.QA, cls.KW, cls.BH, cls.OM, cls.JO}
        oceania = {cls.AU, cls.NZ}
        
        if region in latin_america:
            return "Latin America"
        elif region in north_america:
            return "North America"
        elif region in western_europe:
            return "Western Europe"
        elif region in eastern_europe:
            return "Eastern Europe"
        elif region in africa:
            return "Africa"
        elif region in east_asia:
            return "East Asia"
        elif region in southeast_asia:
            return "Southeast Asia"
        elif region in middle_east:
            return "Middle East"
        elif region in oceania:
            return "Oceania"
        return "Unknown"


class KioskSalesChannel(str, Enum):
    KIOSK = "kiosk"
    SELF_SERVICE = "self_service"  # Quiosque de autoatendimento
    VENDING_MACHINE = "vending_machine"  # Máquina de venda automática
    LOCKER_STATION = "locker_station"  # Estação de lockers


class KioskFulfillmentType(str, Enum):
    INSTANT = "instant"
    PICKUP = "pickup"  # Retirada imediata
    LOCKER_DISPENSE = "locker_dispense"  # Dispensa de locker
    VENDING = "vending"  # Venda direta


class KioskPaymentMethod(str, Enum):
    # Cartões
    CREDIT_CARD = "creditCard"
    DEBIT_CARD = "debitCard"
    GIFT_CARD = "giftCard"
    PREPAID_CARD = "prepaidCard"

    # Brasil
    PIX = "pix"
    BOLETO = "boleto"

    # América Latina
    MERCADO_PAGO_WALLET = "mercado_pago_wallet"
    OXXO = "oxxo"  # México
    SPEI = "spei"  # México
    RAPIPAGO = "rapipago"  # Argentina
    
    # América do Norte
    VENMO = "venmo"
    CASHAPP = "cashapp"
    INTERAC = "interac"  # Canadá

    # Europa
    MBWAY = "mbway"  # Portugal
    MULTIBANCO_REFERENCE = "multibanco_reference"  # Portugal
    SOFORT = "sofort"  # Alemanha
    IDEAL = "ideal"  # Holanda
    BANCONTACT = "bancontact"  # Bélgica
    TWINT = "twint"  # Suíça
    MOBILEPAY = "mobilepay"  # Dinamarca, Finlândia
    BLIK = "blik"  # Polônia
    PAYPAL = "paypal"  # Reino Unido

    # África
    M_PESA = "m_pesa"
    AIRTEL_MONEY = "airtel_money"
    MTN_MONEY = "mtn_money"

    # China
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    UNIONPAY = "unionpay"

    # Japão
    # PAYPAY = "paypay"
    LINE_PAY = "line_pay"
    RAKUTEN_PAY = "rakuten_pay"
    KONBINI = "konbini"  # Pagamento em lojas de conveniência

    # Tailândia
    PROMPTPAY = "promptpay"
    TRUEMONEY = "truemoney"

    # Indonésia
    GO_PAY = "go_pay"
    OVO = "ovo"
    DANA = "dana"

    # Singapura
    GRABPAY = "grabpay"
    DBS_PAYLAH = "dbs_paylah"

    # Filipinas
    GCASH = "gcash"
    PAYMAYA = "paymaya"

    # Emirados Árabes
    TABBY = "tabby"  # BNPL
    PAYBY = "payby"
    
    # Turquia
    TROY = "troy"
    BKM_EXPRESS = "bkm_express"
    
    # Rússia
    MIR = "mir"
    YOOMONEY = "yoomoney"

    # Austrália
    AFTERPAY = "afterpay"
    ZIP = "zip"
    BPAY = "bpay"

    # Wallets globais
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    SAMSUNG_PAY = "samsung_pay"

    CRYPTO = "crypto"

    @classmethod
    def requires_wallet_provider(cls, method: "KioskPaymentMethod") -> bool:
        """Verifica se o método de pagamento requer um provedor de carteira digital"""
        digital_wallets = {
            cls.APPLE_PAY, cls.GOOGLE_PAY, cls.SAMSUNG_PAY, cls.MERCADO_PAGO_WALLET,
            cls.PAYPAL, cls.VENMO, cls.CASHAPP, cls.M_PESA, cls.AIRTEL_MONEY,
            cls.MTN_MONEY, cls.ALIPAY, cls.WECHAT_PAY, cls.PAYPAY, cls.LINE_PAY,
            cls.RAKUTEN_PAY, cls.GO_PAY, cls.OVO, cls.DANA, cls.GRABPAY, cls.GCASH,
            cls.PAYMAYA, cls.TABBY, cls.YOOMONEY
        }
        return method in digital_wallets


class KioskPaymentInterface(str, Enum):
    # Interfaces físicas
    NFC = "nfc"
    CHIP = "chip"
    MAGNETIC_STRIPE = "magnetic_stripe"
    CONTACTLESS = "contactless"
    BIOMETRIC = "biometric"
    PHONE_APP = "phone_app"

    # Interfaces digitais
    QR_CODE = "qr_code"
    WEB_TOKEN = "web_token"
    DEEP_LINK = "deep_link"
    API = "api"
    WEB_REDIRECT = "web_redirect"
    
    # Interfaces manuais
    MANUAL = "manual"
    COD = "cod"  # Cash on Delivery
    
    # Interfaces específicas por região
    USSD = "ussd"  # África
    FACE_RECOGNITION = "face_recognition"  # China
    FINGERPRINT = "fingerprint"  # China, Japão
    BARCODE = "barcode"  # Indonésia, Filipinas, Japão
    VOICE = "voice"  # Voice payments

    REFERENCE = "reference"


class KioskCardType(str, Enum):
    CREDIT = "creditCard"
    DEBIT = "debitCard"
    GIFT = "giftCard"
    PREPAID = "prepaidCard"


class KioskWalletProvider(str, Enum):
    # Internacionais
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    SAMSUNG_PAY = "samsungPay"
    PAYPAL = "paypal"

    # América Latina
    MERCADO_PAGO = "mercadoPago"
    PIC_PAY = "picpay"

    # América do Norte
    VENMO = "venmo"
    CASHAPP = "cashapp"
    ZELLE = "zelle"

    # Europa
    REVOLUT = "revolut"
    MBWAY = "mbway"
    TWINT = "twint"
    MOBILEPAY = "mobilepay"
    BLIK = "blik"

    # África
    M_PESA = "mPesa"
    AIRTEL_MONEY = "airtelMoney"
    MTN_MONEY = "mtnMoney"
    
    # China
    ALIPAY = "alipay"
    WECHAT_PAY = "wechatPay"

    # Japão
    PAYPAY = "paypay"
    LINE_PAY = "linePay"
    RAKUTEN_PAY = "rakutenPay"
    
    # Tailândia
    TRUEMONEY = "trueMoney"
    
    # Indonésia
    GO_PAY = "goPay"
    OVO = "ovo"
    DANA = "dana"

    # Singapura
    GRABPAY = "grabpay"
    DBS_PAYLAH = "dbsPaylah"

    # Filipinas
    GCASH = "gcash"
    PAYMAYA = "paymaya"

    # Emirados Árabes
    TABBY = "tabby"

    # Turquia
    BKM_EXPRESS = "bkmExpress"
    
    # Rússia
    YOOMONEY = "yoomoney"
    
    # Austrália
    AFTERPAY = "afterpay"
    ZIP = "zip"


UI_CODE_TO_CANONICAL_METHOD: dict[str, str] = {
    "PIX": "pix",
    "CARTAO_CREDITO": "creditCard",
    "CARTAO_DEBITO": "debitCard",
    "CARTAO_PRESENTE": "giftCard",
    "CARTAO_PRE_PAGO": "prepaidCard",
    "MBWAY": "mbway",
    "MULTIBANCO_REFERENCE": "multibanco_reference",
    "NFC": "nfc",
    "APPLE_PAY": "apple_pay",
    "GOOGLE_PAY": "google_pay",
    "SAMSUNG_PAY": "samsung_pay",
    "MERCADO_PAGO_WALLET": "mercado_pago_wallet",
    "PAYPAL": "paypal",
    "M_PESA": "m_pesa",
    "AIRTEL_MONEY": "airtel_money",
    "MTN_MONEY": "mtn_money",
    "ALIPAY": "alipay",
    "WECHAT_PAY": "wechat_pay",
    "PAYPAY": "paypay",
    "LINE_PAY": "line_pay",
    "RAKUTEN_PAY": "rakuten_pay",
    "KONBINI": "konbini",
    "GO_PAY": "go_pay",
    "OVO": "ovo",
    "DANA": "dana",
    "GRABPAY": "grabpay",
    "GCASH": "gcash",
    "PAYMAYA": "paymaya",
    "TABBY": "tabby",
    "YOOMONEY": "yoomoney",
    "AFTERPAY": "afterpay",
    "ZIP": "zip",
    "BPAY": "bpay",
    "BOLETO": "boleto",
    "CRYPTO": "crypto",
}

DEFAULT_INTERFACE_BY_METHOD: dict[str, str] = {
    "creditCard": "chip",
    "debitCard": "chip",
    "giftCard": "manual",
    "prepaidCard": "manual",
    "pix": "qr_code",
    "boleto": "barcode",
    "mercado_pago_wallet": "qr_code",
    "oxxo": "barcode",
    "spei": "web_token",
    "rapipago": "barcode",
    "venmo": "web_token",
    "cashapp": "web_token",
    "interac": "web_token",
    "mbway": "phone_app",
    "multibanco_reference": "reference",
    "sofort": "web_redirect",
    "ideal": "web_redirect",
    "bancontact": "web_redirect",
    "twint": "web_token",
    "mobilepay": "web_token",
    "blik": "web_token",
    "paypal": "web_redirect",
    "m_pesa": "ussd",
    "airtel_money": "ussd",
    "mtn_money": "ussd",
    "alipay": "qr_code",
    "wechat_pay": "qr_code",
    "unionpay": "chip",
    "paypay": "qr_code",
    "line_pay": "qr_code",
    "rakuten_pay": "qr_code",
    "konbini": "barcode",
    "promptpay": "qr_code",
    "truemoney": "qr_code",
    "go_pay": "qr_code",
    "ovo": "qr_code",
    "dana": "qr_code",
    "grabpay": "qr_code",
    "dbs_paylah": "qr_code",
    "gcash": "qr_code",
    "paymaya": "qr_code",
    "tabby": "web_redirect",
    "payby": "web_redirect",
    "troy": "chip",
    "bkm_express": "web_redirect",
    "mir": "chip",
    "yoomoney": "web_redirect",
    "afterpay": "web_redirect",
    "zip": "web_redirect",
    "bpay": "reference",
    "apple_pay": "nfc",
    "google_pay": "nfc",
    "samsung_pay": "nfc",
    "crypto": "qr_code",
}

DEFAULT_WALLET_PROVIDER_BY_METHOD: dict[str, str] = {
    "apple_pay": "applePay",
    "google_pay": "googlePay",
    "samsung_pay": "samsungPay",
    "mercado_pago_wallet": "mercadoPago",
    "paypal": "paypal",
    "venmo": "venmo",
    "cashapp": "cashapp",
    "m_pesa": "mPesa",
    "airtel_money": "airtelMoney",
    "mtn_money": "mtnMoney",
    "alipay": "alipay",
    "wechat_pay": "wechatPay",
    "paypay": "paypay",
    "line_pay": "linePay",
    "rakuten_pay": "rakutenPay",
    "go_pay": "goPay",
    "ovo": "ovo",
    "dana": "dana",
    "grabpay": "grabpay",
    "gcash": "gcash",
    "paymaya": "paymaya",
    "tabby": "tabby",
    "yoomoney": "yoomoney",
}

PHONE_REQUIRED_METHODS = {
    "mbway",
    "m_pesa",
    "airtel_money",
    "mtn_money",
    "go_pay",
    "ovo",
    "dana",
    "gcash",
    "paymaya",
}

WALLET_PROVIDER_REQUIRED_METHODS = set(DEFAULT_WALLET_PROVIDER_BY_METHOD.keys())


def _normalize_method_input(value: Any) -> Any:
    if value is None:
        return value

    raw = str(value).strip()
    if not raw:
        return raw

    if raw in UI_CODE_TO_CANONICAL_METHOD:
        return UI_CODE_TO_CANONICAL_METHOD[raw]

    upper = raw.upper()
    if upper in UI_CODE_TO_CANONICAL_METHOD:
        return UI_CODE_TO_CANONICAL_METHOD[upper]

    return raw


def _normalize_interface_input(value: Any) -> Any:
    if value is None:
        return value
    raw = str(value).strip()
    return raw or None


def _normalize_wallet_provider_input(value: Any) -> Any:
    if value is None:
        return value
    raw = str(value).strip()
    return raw or None


class KioskOrderCreateIn(BaseModel):
    region: KioskRegion = Field(..., examples=["SP", "PT", "CN", "JP"])
    totem_id: str = Field(..., examples=["SP-CARAPICUIBA-JDMARILU-LK-001"])
    sku_id: str = Field(..., examples=["cookie_laranja"])

    payment_method: str
    payment_interface: Optional[str] = None
    desired_slot: int | None = Field(default=None, ge=1)

    card_type: Optional[str] = None
    customer_phone: Optional[str] = Field(default=None, examples=["+5511999999999", "+351912345678"])
    wallet_provider: Optional[str] = None

    sales_channel: Optional[str] = None
    fulfillment_type: Optional[str] = None
    amount_cents: Optional[int] = Field(default=None, gt=0)

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

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("payment_method é obrigatório.")
        return normalized

    @field_validator("payment_interface")
    @classmethod
    def normalize_payment_interface(cls, value: Optional[str]) -> Optional[str]:
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

    @field_validator("wallet_provider")
    @classmethod
    def normalize_wallet_provider(cls, value: Optional[str]) -> Optional[str]:
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
    ttl_sec: int | None = None
    message: str
    payment_status: Optional[str] = None
    payment_instruction_type: Optional[str] = None
    payment_payload: Dict[str, Any] = Field(default_factory=dict)


class KioskPaymentApprovedOut(BaseModel):
    order_id: str
    slot: int
    status: str
    allocation_id: str
    payment_method: Optional[str] = None
    receipt_code: Optional[str] = None
    receipt_print_path: Optional[str] = None
    receipt_json_path: Optional[str] = None
    message: str


class KioskCustomerIdentifyIn(BaseModel):
    order_id: str
    phone: Optional[str] = None
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


class KioskIdentifyOut(BaseModel):
    ok: bool
    message: str