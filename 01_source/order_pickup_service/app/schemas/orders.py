# 01_source/order_pickup_service/app/schemas/orders.py
# 02/04/2026 - Enhanced Version with Asia, Middle East, Eastern Europe & Oceania

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from re import compile as re_compile

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
    def get_continent(cls, region: "OnlineRegion") -> str:
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

    @classmethod
    def get_currency(cls, region: "OnlineRegion") -> str:
        """Retorna a moeda padrão da região"""
        currency_map = {
            # América Latina
            cls.SP: "BRL", cls.RJ: "BRL", cls.MG: "BRL", cls.RS: "BRL", cls.BA: "BRL",
            cls.MX: "MXN", cls.AR: "ARS", cls.CO: "COP", cls.CL: "CLP", cls.PE: "PEN",
            cls.EC: "USD", cls.UY: "UYU", cls.PY: "PYG", cls.BO: "BOB", cls.VE: "VES",
            cls.CR: "CRC", cls.PA: "USD", cls.DO: "DOP",
            
            # América do Norte
            cls.US_NY: "USD", cls.US_CA: "USD", cls.US_TX: "USD", cls.US_FL: "USD", cls.US_IL: "USD",
            cls.CA_ON: "CAD", cls.CA_QC: "CAD", cls.CA_BC: "CAD",
            
            # Europa
            cls.PT: "EUR", cls.ES: "EUR", cls.FR: "EUR", cls.DE: "EUR", cls.IT: "EUR",
            cls.NL: "EUR", cls.BE: "EUR", cls.AT: "EUR", cls.FI: "EUR", cls.IE: "EUR",
            cls.UK: "GBP", cls.CH: "CHF", cls.SE: "SEK", cls.NO: "NOK", cls.DK: "DKK",
            cls.PL: "PLN", cls.CZ: "CZK", cls.HU: "HUF", cls.RO: "RON", cls.RU: "RUB",
            cls.TR: "TRY", cls.GR: "EUR",
            
            # África
            cls.ZA: "ZAR", cls.NG: "NGN", cls.KE: "KES", cls.EG: "EGP", cls.MA: "MAD",
            cls.GH: "GHS", cls.SN: "XOF", cls.CI: "XOF", cls.TZ: "TZS", cls.UG: "UGX",
            cls.RW: "RWF", cls.MZ: "MZN", cls.AO: "AOA", cls.DZ: "DZD", cls.TN: "TND",
            
            # Ásia
            cls.CN: "CNY", cls.JP: "JPY", cls.KR: "KRW", cls.TH: "THB", cls.ID: "IDR",
            cls.SG: "SGD", cls.PH: "PHP", cls.VN: "VND", cls.MY: "MYR",
            
            # Oriente Médio
            cls.AE: "AED", cls.SA: "SAR", cls.QA: "QAR", cls.KW: "KWD", cls.BH: "BHD",
            cls.OM: "OMR", cls.JO: "JOD",
            
            # Oceania
            cls.AU: "AUD", cls.NZ: "NZD",
        }
        return currency_map.get(region, "USD")


class OnlineSalesChannel(str, Enum):
    ONLINE = "online"
    MARKETPLACE = "marketplace"
    SOCIAL_COMMERCE = "social_commerce"
    APP_STORE = "app_store"
    IN_APP = "in_app"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    TIKTOK = "tiktok"
    TELEGRAM = "telegram"
    WECHAT = "wechat"  # China
    LINE = "line"      # Japão, Tailândia, Indonésia
    KAKAO = "kakao"    # Coreia do Sul
    RAKUTEN = "rakuten" # Japão
    SHOPEE = "shopee"   # Sudeste Asiático
    LAZADA = "lazada"   # Sudeste Asiático
    TOKOPEDIA = "tokopedia" # Indonésia


class OnlineFulfillmentType(str, Enum):
    RESERVATION = "reservation"
    DIGITAL_DELIVERY = "digital_delivery"
    PHYSICAL_DELIVERY = "physical_delivery"
    PICKUP_POINT = "pickup_point"
    LOCKER = "locker"
    SAME_DAY = "same_day"
    SCHEDULED = "scheduled"
    INSTANT = "instant"
    INTERNATIONAL_SHIPPING = "international_shipping"
    CONVENIENCE_STORE = "convenience_store"  # Japão - retirada em kombini
    TRAIN_STATION = "train_station"          # Japão - retirada em estações
    DRONE_DELIVERY = "drone_delivery"        # China, Dubai
    PARCEL_LOCKER = "parcel_locker"          # China, Japão, Alemanha


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
    OXXO = "oxxo"
    SPEI = "spei"
    RAPIPAGO = "rapipago"
    PAGOFACIL = "pagofacil"
    SERVIPAG = "servipag"
    KHIPU = "khipu"
    EFECTY = "efecty"
    PSE = "pse"
    
    # América do Norte
    ACH = "ach"
    VENMO = "venmo"
    CASHAPP = "cashapp"
    ZELLE = "zelle"
    AFTERPAY = "afterpay"
    AFFIRM = "affirm"
    KLARNA_US = "klarna_us"
    INTERAC = "interac"
    
    # Europa
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    MBWAY = "mbway"
    MULTIBANCO_REFERENCE = "multibanco_reference"
    SOFORT = "sofort"
    GIROPAY = "giropay"
    KLARNA = "klarna"
    TRUSTLY = "trustly"
    IDEAL = "ideal"
    BANCONTACT = "bancontact"
    TWINT = "twint"
    VIABILL = "viabill"
    MOBILEPAY = "mobilepay"
    VIPS = "vips"
    BLIK = "blik"
    PRZELEWY24 = "przelewy24"
    SATISPAY = "satispay"
    SEPA = "sepa"
    
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
    M_PESA = "m_pesa"
    AIRTEL_MONEY = "airtel_money"
    MTN_MONEY = "mtn_money"
    ORANGE_MONEY = "orange_money"
    VODAFONE_CASH = "vodafone_cash"
    TELECASH = "telecash"
    ECONET = "econet"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    YOCO = "yoco"
    PEACH_PAYMENTS = "peach_payments"
    SNOOPY = "snoopy"
    UNITEL_MONEY = "unitel_money"
    MOOV_MONEY = "moov_money"
    
    # China
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    UNIONPAY = "unionpay"
    JD_PAY = "jd_pay"
    BAIDU_WALLET = "baidu_wallet"
    DCEP = "dcep"  # Digital Currency Electronic Payment (Yuan digital)
    
    # Japão
    PAYPAY = "paypay"
    LINE_PAY = "line_pay"
    RAKUTEN_PAY = "rakuten_pay"
    MERPAY = "merpay"
    AU_PAY = "au_pay"
    D_PAY = "d_pay"
    JCB_PREPAID = "jcb_prepaid"
    KONBINI = "konbini"  # Pagamento em lojas de conveniência
    BANK_TRANSFER_JP = "bank_transfer_jp"
    
    # Coreia do Sul
    KAKAO_PAY = "kakao_pay"
    NAVER_PAY = "naver_pay"
    SAMSUNG_PAY = "samsung_pay_kr"
    TOSS = "toss"
    PAYCO = "payco"
    
    # Tailândia
    PROMPTPAY = "promptpay"
    TRUEMONEY = "truemoney"
    RABBIT_LINE_PAY = "rabbit_line_pay"
    SCB_EASY = "scb_easy"
    KPLUS = "kplus"
    
    # Indonésia
    GO_PAY = "go_pay"
    OVO = "ovo"
    DANA = "dana"
    LINKAJA = "linkaja"
    SHOPEEPAY_ID = "shopeepay_id"
    DOKU = "doku"
    MANDIRI_BILLS = "mandiri_bills"
    
    # Singapura
    GRABPAY = "grabpay"
    DBS_PAYLAH = "dbs_paylah"
    OCBC_PAY_ANYONE = "ocbc_pay_anyone"
    SINGTEL_DASH = "singtel_dash"
    NETSPAY = "netspay"
    
    # Filipinas
    GCASH = "gcash"
    PAYMAYA = "paymaya"
    GRABPAY_PH = "grabpay_ph"
    LANDBANK = "landbank"
    PESONET = "pesonet"
    
    # Emirados Árabes Unidos
    APPLE_PAY_AE = "apple_pay_ae"
    SAMSUNG_PAY_AE = "samsung_pay_ae"
    PAYBY = "payby"
    DP_WORLD = "dp_world"
    TABBY = "tabby"  # Compre agora, pague depois
    
    # Turquia
    TROY = "troy"
    BKM_EXPRESS = "bkm_express"
    ININAL = "ininal"
    TURKCELL_PAY = "turkcell_pay"
    VODAFONE_PAY_TR = "vodafone_pay_tr"
    
    # Rússia
    MIR = "mir"
    SBERBANK_ONLINE = "sberbank_online"
    YOOMONEY = "yoomoney"
    QIWI = "qiwi"
    WEBMONEY = "webmoney"
    TINKOFF = "tinkoff"
    
    # Austrália
    POLI = "poli"
    AFTERPAY_AU = "afterpay_au"
    ZIP = "zip"
    BPAY = "bpay"
    OPAY = "opay"
    BEEM_IT = "beem_it"
    
    # Wallet globais
    CRYPTO = "crypto"
    CASH_ON_DELIVERY = "cash_on_delivery"
    BANK_TRANSFER = "bank_transfer"
    DIRECT_DEBIT = "direct_debit"

    @classmethod
    def requires_wallet_provider(cls, method: "OnlinePaymentMethod") -> bool:
        """Verifica se o método de pagamento requer um provedor de carteira digital"""
        digital_wallets = {
            cls.APPLE_PAY, cls.GOOGLE_PAY, cls.MERCADO_PAGO_WALLET, cls.PAYPAL,
            cls.VENMO, cls.CASHAPP, cls.M_PESA, cls.AIRTEL_MONEY, cls.MTN_MONEY,
            cls.ALIPAY, cls.WECHAT_PAY, cls.PAYPAY, cls.LINE_PAY, cls.RAKUTEN_PAY,
            cls.KAKAO_PAY, cls.NAVER_PAY, cls.SAMSUNG_PAY, cls.GO_PAY, cls.OVO,
            cls.DANA, cls.GRABPAY, cls.GCASH, cls.PAYMAYA, cls.TABBY, cls.TROY,
            cls.MIR, cls.YOOMONEY, cls.AFTERPAY_AU, cls.ZIP
        }
        return method in digital_wallets

    @classmethod
    def get_region_for_method(cls, method: "OnlinePaymentMethod") -> str:
        """Retorna a região principal para um método de pagamento"""
        region_map = {
            # Brasil
            cls.PIX: "Brazil", cls.BOLETO: "Brazil",
            # México
            cls.OXXO: "Mexico", cls.SPEI: "Mexico",
            # Argentina
            cls.RAPIPAGO: "Argentina", cls.PAGOFACIL: "Argentina",
            # Chile
            cls.SERVIPAG: "Chile", cls.KHIPU: "Chile",
            # Colômbia
            cls.EFECTY: "Colombia", cls.PSE: "Colombia",
            # China
            cls.ALIPAY: "China", cls.WECHAT_PAY: "China", cls.UNIONPAY: "China",
            # Japão
            cls.PAYPAY: "Japan", cls.LINE_PAY: "Japan", cls.RAKUTEN_PAY: "Japan",
            cls.KONBINI: "Japan",
            # Tailândia
            cls.PROMPTPAY: "Thailand", cls.TRUEMONEY: "Thailand",
            # Indonésia
            cls.GO_PAY: "Indonesia", cls.OVO: "Indonesia", cls.DANA: "Indonesia",
            # Singapura
            cls.GRABPAY: "Singapore", cls.DBS_PAYLAH: "Singapore",
            # Filipinas
            cls.GCASH: "Philippines", cls.PAYMAYA: "Philippines",
            # Emirados Árabes
            cls.TABBY: "UAE", cls.PAYBY: "UAE",
            # Turquia
            cls.TROY: "Turkey", cls.BKM_EXPRESS: "Turkey",
            # Rússia
            cls.MIR: "Russia", cls.SBERBANK_ONLINE: "Russia",
            # Austrália
            cls.AFTERPAY_AU: "Australia", cls.ZIP: "Australia", cls.BPAY: "Australia",
        }
        return region_map.get(method, "Global")


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
    COD = "cod"
    POS = "pos"
    
    # Interfaces específicas por região
    USSD = "ussd"  # África
    SMS = "sms"  # África
    VOICE = "voice"  # Voice payments
    QR_BILL = "qr_bill"  # Suíça
    BANK_LINK = "bank_link"  # Holanda, Singapura
    FACE_RECOGNITION = "face_recognition"  # China
    FINGERPRINT = "fingerprint"  # China, Japão
    KIOSK = "kiosk"  # Japão, Tailândia
    BARCODE = "barcode"  # Indonésia, Filipinas


class OnlineWalletProvider(str, Enum):
    # Internacionais
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    SAMSUNG_PAY = "samsungPay"
    PAYPAL = "paypal"
    
    # América Latina
    MERCADO_PAGO = "mercadoPago"
    PICPAY = "picpay"
    RAPPI = "rappi"
    NEQUI = "nequi"
    YAPE = "yape"
    PLIN = "plin"
    
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
    MBWAY = "mbway"
    TWINT = "twint"
    VIABILL = "viabill"
    MOBILEPAY = "mobilepay"
    SATISPAY = "satispay"
    BLIK = "blik"
    
    # África
    M_PESA = "mPesa"
    AIRTEL_MONEY = "airtelMoney"
    MTN_MONEY = "mtnMoney"
    ORANGE_MONEY = "orangeMoney"
    VODAFONE_CASH = "vodafoneCash"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    YOCO = "yoco"
    KCB_MOBILE = "kcbMobile"
    TIGOPESA = "tigopesa"
    
    # China
    ALIPAY = "alipay"
    WECHAT_PAY = "wechatPay"
    
    # Japão
    PAYPAY = "paypay"
    LINE_PAY = "linePay"
    RAKUTEN_PAY = "rakutenPay"
    MERPAY = "merpay"
    AU_PAY = "auPay"
    D_PAY = "dPay"
    
    # Coreia do Sul
    KAKAO_PAY = "kakaoPay"
    NAVER_PAY = "naverPay"
    TOSS = "toss"
    PAYCO = "payco"
    
    # Tailândia
    TRUEMONEY = "trueMoney"
    RABBIT_LINE_PAY = "rabbitLinePay"
    SCB_EASY = "scbEasy"
    
    # Indonésia
    GO_PAY = "goPay"
    OVO = "ovo"
    DANA = "dana"
    LINKAJA = "linkaja"
    SHOPEEPAY = "shopeepay"
    
    # Singapura
    GRABPAY = "grabpay"
    DBS_PAYLAH = "dbsPaylah"
    SINGTEL_DASH = "singtelDash"
    
    # Filipinas
    GCASH = "gcash"
    PAYMAYA = "paymaya"
    
    # Emirados Árabes
    PAYBY = "payby"
    TABBY = "tabby"
    
    # Turquia
    BKM_EXPRESS = "bkmExpress"
    ININAL = "ininal"
    TURKCELL_PAY = "turkcellPay"
    
    # Rússia
    YOOMONEY = "yoomoney"
    QIWI = "qiwi"
    WEBMONEY = "webmoney"
    TINKOFF = "tinkoff"
    
    # Austrália
    AFTERPAY = "afterpay"
    ZIP = "zip"
    BEEM_IT = "beemIt"


class CreateOrderIn(BaseModel):
    region: OnlineRegion = Field(..., examples=["SP", "PT", "CN", "JP", "TH", "AE", "AU"])
    sales_channel: OnlineSalesChannel = Field(default=OnlineSalesChannel.ONLINE)
    fulfillment_type: OnlineFulfillmentType = Field(default=OnlineFulfillmentType.RESERVATION)

    sku_id: str
    totem_id: str = Field(..., description="Identificador da unidade física / locker")

    payment_method: OnlinePaymentMethod
    payment_interface: OnlinePaymentInterface

    desired_slot: Optional[int] = Field(
        default=None,
        ge=1,
        le=999,
        description="Slot físico do locker (validado dinamicamente no backend/runtime)",
    )
    amount_cents: Optional[int] = Field(default=None, gt=0, le=999999999)

    customer_phone: Optional[str] = Field(default=None, examples=["+351912345678"])
    customer_email: Optional[str] = Field(default=None, examples=["customer@example.com"])
    wallet_provider: Optional[OnlineWalletProvider] = None
    
    # Campos adicionais para África
    ussd_session_id: Optional[str] = Field(default=None, description="USSD session ID for African payments")
    
    # Campos para Ásia
    national_id: Optional[str] = Field(default=None, description="National ID for China/Japan/South Korea")
    qr_code_content: Optional[str] = Field(default=None, description="QR code content for Alipay/WeChat Pay/PromptPay")
    konbini_code: Optional[str] = Field(default=None, description="Convenience store payment code for Japan")
    
    # Campos para validação
    device_id: Optional[str] = Field(default=None, description="Device identifier for fraud prevention")
    ip_address: Optional[str] = Field(default=None, description="Customer IP address")
    
    # Campos para Emirados Árabes
    emirates_id: Optional[str] = Field(default=None, description="Emirates ID for UAE customers")
    
    # Campos para Turquia
    turkish_id: Optional[str] = Field(default=None, description="Turkish ID number")
    
    # Campos para Rússia
    inn_number: Optional[str] = Field(default=None, description="INN tax number for Russia")
    
    # Campos para Austrália
    australian_tfn: Optional[str] = Field(default=None, description="Australian Tax File Number")

    @field_validator("totem_id")
    @classmethod
    def validate_totem_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("totem_id is required")
        if len(normalized) > 50:
            raise ValueError("totem_id must be less than 50 characters")
        return normalized

    @field_validator("sku_id")
    @classmethod
    def validate_sku_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("sku_id is required")
        if len(normalized) > 100:
            raise ValueError("sku_id must be less than 100 characters")
        return normalized

    @field_validator("customer_phone")
    @classmethod
    def normalize_customer_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        # Validação de formato internacional
        phone_pattern = re_compile(r'^\+[1-9]\d{1,14}$')
        if normalized and not phone_pattern.match(normalized):
            raise ValueError("customer_phone must be in international format (e.g., +5511999999999)")
        return normalized or None

    @field_validator("customer_email")
    @classmethod
    def validate_customer_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        email_pattern = re_compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if normalized and not email_pattern.match(normalized):
            raise ValueError("customer_email must be a valid email address")
        return normalized or None

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip()
        ip_pattern = re_compile(r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')
        if normalized and not ip_pattern.match(normalized):
            raise ValueError("ip_address must be a valid IPv4 address")
        return normalized or None

    @model_validator(mode="after")
    def validate_payment_context(self) -> "CreateOrderIn":
        if self.sales_channel != OnlineSalesChannel.ONLINE:
            raise ValueError("sales_channel inválido para CreateOrderIn.")

        if self.fulfillment_type != OnlineFulfillmentType.RESERVATION:
            raise ValueError("fulfillment_type inválido para pedido ONLINE.")

        # Validações específicas por região - Brasil
        brazil_regions = {OnlineRegion.SP, OnlineRegion.RJ, OnlineRegion.MG, OnlineRegion.RS, OnlineRegion.BA}
        
        if self.payment_method == OnlinePaymentMethod.PIX:
            if self.region not in brazil_regions:
                raise ValueError(f"pix só pode ser utilizado nas regiões do Brasil: {', '.join([r.value for r in brazil_regions])}")
        
        if self.payment_method == OnlinePaymentMethod.BOLETO:
            if self.region not in brazil_regions:
                raise ValueError(f"boleto só pode ser utilizado nas regiões do Brasil: {', '.join([r.value for r in brazil_regions])}")

        # Portugal
        if self.payment_method == OnlinePaymentMethod.MBWAY:
            if self.region != OnlineRegion.PT:
                raise ValueError("mbway só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone is required for mbway.")

        if self.payment_method == OnlinePaymentMethod.MULTIBANCO_REFERENCE:
            if self.region != OnlineRegion.PT:
                raise ValueError("multibanco_reference só pode ser utilizado na região PT.")

        # México
        mexican_methods = {OnlinePaymentMethod.OXXO, OnlinePaymentMethod.SPEI}
        if self.payment_method in mexican_methods and self.region != OnlineRegion.MX:
            raise ValueError(f"{self.payment_method.value} só pode ser utilizado na região MX.")

        # Argentina
        argentinian_methods = {OnlinePaymentMethod.RAPIPAGO, OnlinePaymentMethod.PAGOFACIL}
        if self.payment_method in argentinian_methods and self.region != OnlineRegion.AR:
            raise ValueError(f"{self.payment_method.value} só pode ser utilizado na região AR.")

        # Chile
        chilean_methods = {OnlinePaymentMethod.SERVIPAG, OnlinePaymentMethod.KHIPU}
        if self.payment_method in chilean_methods and self.region != OnlineRegion.CL:
            raise ValueError(f"{self.payment_method.value} só pode ser utilizado na região CL.")

        # Colômbia
        colombian_methods = {OnlinePaymentMethod.EFECTY, OnlinePaymentMethod.PSE}
        if self.payment_method in colombian_methods and self.region != OnlineRegion.CO:
            raise ValueError(f"{self.payment_method.value} só pode ser utilizado na região CO.")

        # África - M-PESA
        african_regions = {OnlineRegion.KE, OnlineRegion.TZ, OnlineRegion.EG, OnlineRegion.UG, OnlineRegion.RW}
        if self.payment_method == OnlinePaymentMethod.M_PESA:
            if self.region not in african_regions:
                raise ValueError(f"m_pesa só pode ser utilizado nas regiões da África Oriental: {', '.join([r.value for r in african_regions])}")
            if not self.customer_phone:
                raise ValueError("customer_phone is required for m_pesa.")
            if not self.ussd_session_id:
                raise ValueError("ussd_session_id is required for m_pesa.")

        # China
        chinese_methods = {OnlinePaymentMethod.ALIPAY, OnlinePaymentMethod.WECHAT_PAY, 
                          OnlinePaymentMethod.UNIONPAY, OnlinePaymentMethod.JD_PAY,
                          OnlinePaymentMethod.DCEP}
        if self.payment_method in chinese_methods:
            if self.region != OnlineRegion.CN:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na China (CN).")
            if not self.qr_code_content:
                raise ValueError("qr_code_content is required for Chinese payment methods.")
            if self.payment_interface != OnlinePaymentInterface.QR_CODE:
                raise ValueError(f"{self.payment_method.value} exige payment_interface qr_code.")

        # Japão
        japanese_methods = {OnlinePaymentMethod.PAYPAY, OnlinePaymentMethod.LINE_PAY,
                           OnlinePaymentMethod.RAKUTEN_PAY, OnlinePaymentMethod.MERPAY,
                           OnlinePaymentMethod.KONBINI}
        if self.payment_method in japanese_methods:
            if self.region != OnlineRegion.JP:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado no Japão (JP).")
            
            if self.payment_method == OnlinePaymentMethod.KONBINI:
                if not self.konbini_code:
                    raise ValueError("konbini_code is required for konbini payments.")
                if self.payment_interface not in {OnlinePaymentInterface.BARCODE, OnlinePaymentInterface.KIOSK}:
                    raise ValueError("konbini exige payment_interface barcode ou kiosk.")

        # Tailândia
        thai_methods = {OnlinePaymentMethod.PROMPTPAY, OnlinePaymentMethod.TRUEMONEY,
                        OnlinePaymentMethod.RABBIT_LINE_PAY}
        if self.payment_method in thai_methods:
            if self.region != OnlineRegion.TH:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Tailândia (TH).")
            if self.payment_method == OnlinePaymentMethod.PROMPTPAY:
                if not self.qr_code_content:
                    raise ValueError("qr_code_content is required for PromptPay.")
                if self.payment_interface != OnlinePaymentInterface.QR_CODE:
                    raise ValueError("PromptPay exige payment_interface qr_code.")

        # Indonésia
        indonesian_methods = {OnlinePaymentMethod.GO_PAY, OnlinePaymentMethod.OVO,
                             OnlinePaymentMethod.DANA, OnlinePaymentMethod.LINKAJA}
        if self.payment_method in indonesian_methods:
            if self.region != OnlineRegion.ID:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Indonésia (ID).")
            if not self.customer_phone:
                raise ValueError("customer_phone is required for Indonesian mobile wallets.")

        # Singapura
        singapore_methods = {OnlinePaymentMethod.GRABPAY, OnlinePaymentMethod.DBS_PAYLAH,
                            OnlinePaymentMethod.SINGTEL_DASH, OnlinePaymentMethod.NETSPAY}
        if self.payment_method in singapore_methods:
            if self.region != OnlineRegion.SG:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado em Singapura (SG).")

        # Filipinas
        philippine_methods = {OnlinePaymentMethod.GCASH, OnlinePaymentMethod.PAYMAYA}
        if self.payment_method in philippine_methods:
            if self.region != OnlineRegion.PH:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado nas Filipinas (PH).")
            if not self.customer_phone:
                raise ValueError("customer_phone is required for GCash/PayMaya.")

        # Emirados Árabes Unidos
        uae_methods = {OnlinePaymentMethod.TABBY, OnlinePaymentMethod.PAYBY,
                       OnlinePaymentMethod.APPLE_PAY_AE, OnlinePaymentMethod.SAMSUNG_PAY_AE}
        if self.payment_method in uae_methods:
            if self.region != OnlineRegion.AE:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado nos Emirados Árabes Unidos (AE).")
            if self.payment_method == OnlinePaymentMethod.TABBY and not self.customer_email:
                raise ValueError("customer_email is required for Tabby payments.")

        # Turquia
        turkish_methods = {OnlinePaymentMethod.TROY, OnlinePaymentMethod.BKM_EXPRESS,
                          OnlinePaymentMethod.ININAL, OnlinePaymentMethod.TURKCELL_PAY}
        if self.payment_method in turkish_methods:
            if self.region != OnlineRegion.TR:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Turquia (TR).")
            if self.payment_method == OnlinePaymentMethod.TROY and not self.turkish_id:
                raise ValueError("turkish_id is required for Troy payments.")

        # Rússia
        russian_methods = {OnlinePaymentMethod.MIR, OnlinePaymentMethod.SBERBANK_ONLINE,
                          OnlinePaymentMethod.YOOMONEY, OnlinePaymentMethod.QIWI,
                          OnlinePaymentMethod.TINKOFF}
        if self.payment_method in russian_methods:
            if self.region != OnlineRegion.RU:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Rússia (RU).")
            if self.payment_method == OnlinePaymentMethod.MIR and not self.national_id:
                raise ValueError("national_id is required for MIR payments.")

        # Austrália
        australian_methods = {OnlinePaymentMethod.POLI, OnlinePaymentMethod.AFTERPAY_AU,
                             OnlinePaymentMethod.ZIP, OnlinePaymentMethod.BPAY}
        if self.payment_method in australian_methods:
            if self.region != OnlineRegion.AU:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Austrália (AU).")
            if self.payment_method == OnlinePaymentMethod.BPAY:
                if not self.customer_phone and not self.customer_email:
                    raise ValueError("customer_phone or customer_email is required for BPAY.")

        # Validações de carteiras digitais
        if OnlinePaymentMethod.requires_wallet_provider(self.payment_method):
            valid_interfaces = {
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.QR_CODE,
                OnlinePaymentInterface.NFC,
                OnlinePaymentInterface.DEEP_LINK,
                OnlinePaymentInterface.API,
                OnlinePaymentInterface.FACE_RECOGNITION,
                OnlinePaymentInterface.FINGERPRINT,
            }
            
            if self.payment_interface not in valid_interfaces:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.payment_method.value}. "
                    f"Interfaces permitidas: {', '.join([i.value for i in valid_interfaces])}"
                )

            if not self.wallet_provider:
                raise ValueError("wallet_provider is required for digital wallets.")

            # Mapeamento de provedores esperados
            expected_provider_map = {
                OnlinePaymentMethod.APPLE_PAY: OnlineWalletProvider.APPLE_PAY,
                OnlinePaymentMethod.GOOGLE_PAY: OnlineWalletProvider.GOOGLE_PAY,
                OnlinePaymentMethod.MERCADO_PAGO_WALLET: OnlineWalletProvider.MERCADO_PAGO,
                OnlinePaymentMethod.PAYPAL: OnlineWalletProvider.PAYPAL,
                OnlinePaymentMethod.VENMO: OnlineWalletProvider.VENMO,
                OnlinePaymentMethod.CASHAPP: OnlineWalletProvider.CASHAPP,
                OnlinePaymentMethod.M_PESA: OnlineWalletProvider.M_PESA,
                OnlinePaymentMethod.AIRTEL_MONEY: OnlineWalletProvider.AIRTEL_MONEY,
                OnlinePaymentMethod.MTN_MONEY: OnlineWalletProvider.MTN_MONEY,
                OnlinePaymentMethod.ALIPAY: OnlineWalletProvider.ALIPAY,
                OnlinePaymentMethod.WECHAT_PAY: OnlineWalletProvider.WECHAT_PAY,
                OnlinePaymentMethod.PAYPAY: OnlineWalletProvider.PAYPAY,
                OnlinePaymentMethod.LINE_PAY: OnlineWalletProvider.LINE_PAY,
                OnlinePaymentMethod.RAKUTEN_PAY: OnlineWalletProvider.RAKUTEN_PAY,
                OnlinePaymentMethod.KAKAO_PAY: OnlineWalletProvider.KAKAO_PAY,
                OnlinePaymentMethod.GO_PAY: OnlineWalletProvider.GO_PAY,
                OnlinePaymentMethod.OVO: OnlineWalletProvider.OVO,
                OnlinePaymentMethod.DANA: OnlineWalletProvider.DANA,
                OnlinePaymentMethod.GRABPAY: OnlineWalletProvider.GRABPAY,
                OnlinePaymentMethod.GCASH: OnlineWalletProvider.GCASH,
                OnlinePaymentMethod.PAYMAYA: OnlineWalletProvider.PAYMAYA,
                OnlinePaymentMethod.TABBY: OnlineWalletProvider.TABBY,
                OnlinePaymentMethod.AFTERPAY_AU: OnlineWalletProvider.AFTERPAY,
                OnlinePaymentMethod.ZIP: OnlineWalletProvider.ZIP,
            }
            
            expected_provider = expected_provider_map.get(self.payment_method)
            if expected_provider and self.wallet_provider != expected_provider:
                raise ValueError(
                    f"wallet_provider incompatível com o método {self.payment_method.value}. "
                    f"Esperado: {expected_provider.value}"
                )

        # Validação para métodos que NÃO devem ter wallet_provider
        if not OnlinePaymentMethod.requires_wallet_provider(self.payment_method) and self.wallet_provider is not None:
            raise ValueError("wallet_provider só pode ser informado para carteiras digitais.")

        # Validações específicas por método de pagamento - Cartões
        if self.payment_method in {
            OnlinePaymentMethod.CREDIT_CARD,
            OnlinePaymentMethod.DEBIT_CARD,
            OnlinePaymentMethod.PREPAID_CARD,
            OnlinePaymentMethod.GIFT_CARD,
        }:
            valid_interfaces = {
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.MANUAL,
                OnlinePaymentInterface.CHIP,
                OnlinePaymentInterface.NFC,
                OnlinePaymentInterface.CONTACTLESS,
                OnlinePaymentInterface.API,
                OnlinePaymentInterface.FACE_RECOGNITION,
                OnlinePaymentInterface.FINGERPRINT,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.payment_method.value}. "
                    f"Interfaces permitidas: {', '.join([i.value for i in valid_interfaces])}"
                )

        # PIX
        if self.payment_method == OnlinePaymentMethod.PIX:
            valid_interfaces = {
                OnlinePaymentInterface.QR_CODE,
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.DEEP_LINK,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(f"pix exige payment_interface: {', '.join([i.value for i in valid_interfaces])}")

        # Boleto
        if self.payment_method == OnlinePaymentMethod.BOLETO:
            valid_interfaces = {
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.QR_CODE,
                OnlinePaymentInterface.DEEP_LINK,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(f"boleto exige payment_interface: {', '.join([i.value for i in valid_interfaces])}")

        # MB Way
        if self.payment_method == OnlinePaymentMethod.MBWAY:
            valid_interfaces = {
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.QR_CODE,
                OnlinePaymentInterface.DEEP_LINK,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(f"mbway exige payment_interface: {', '.join([i.value for i in valid_interfaces])}")

        # Multibanco
        if self.payment_method == OnlinePaymentMethod.MULTIBANCO_REFERENCE:
            valid_interfaces = {
                OnlinePaymentInterface.WEB_TOKEN,
                OnlinePaymentInterface.QR_CODE,
                OnlinePaymentInterface.BANK_LINK,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(f"multibanco_reference exige payment_interface: {', '.join([i.value for i in valid_interfaces])}")

        # USSD para África
        if self.payment_interface == OnlinePaymentInterface.USSD:
            african_regions_all = {OnlineRegion.ZA, OnlineRegion.NG, OnlineRegion.KE, OnlineRegion.EG,
                                  OnlineRegion.GH, OnlineRegion.TZ, OnlineRegion.UG, OnlineRegion.RW,
                                  OnlineRegion.MZ, OnlineRegion.AO}
            if self.region not in african_regions_all:
                raise ValueError("USSD payment interface só pode ser utilizado na África.")
            if not self.ussd_session_id:
                raise ValueError("ussd_session_id is required for USSD payments.")

        # Face Recognition para China
        if self.payment_interface == OnlinePaymentInterface.FACE_RECOGNITION:
            if self.region != OnlineRegion.CN:
                raise ValueError("Face recognition payment só pode ser utilizado na China.")
            if not self.national_id:
                raise ValueError("national_id is required for face recognition payments.")

        # Validação de amount_cents para métodos que exigem valor
        if self.payment_method in {
            OnlinePaymentMethod.PIX, OnlinePaymentMethod.BOLETO, OnlinePaymentMethod.MBWAY,
            OnlinePaymentMethod.MULTIBANCO_REFERENCE, OnlinePaymentMethod.CREDIT_CARD,
            OnlinePaymentMethod.DEBIT_CARD, OnlinePaymentMethod.PREPAID_CARD,
            OnlinePaymentMethod.AFTERPAY_AU, OnlinePaymentMethod.ZIP, OnlinePaymentMethod.TABBY
        } and self.amount_cents is None:
            raise ValueError(f"amount_cents is required for {self.payment_method.value}")

        return self


class OrderOut(BaseModel):
    order_id: str
    channel: str
    status: str
    amount_cents: int
    payment_method: Optional[str] = None
    payment_interface: Optional[str] = None
    allocation: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    currency: Optional[str] = None  # Moeda do pedido

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


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
    currency: Optional[str] = None

    class Config:
        from_attributes = True


class OrderListOut(BaseModel):
    items: List[OrderListItemOut]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


# Classes adicionais para suporte a webhooks e notificações
class OrderPaymentWebhook(BaseModel):
    """Webhook para notificações de pagamento"""
    order_id: str
    payment_method: OnlinePaymentMethod
    payment_status: str
    transaction_id: Optional[str] = None
    amount_cents: int
    paid_at: datetime
    signature: Optional[str] = Field(None, description="Webhook signature for verification")
    currency: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    """Modelo para atualização de status do pedido"""
    order_id: str
    status: str
    previous_status: Optional[str] = None
    updated_by: Optional[str] = None
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    region: Optional[OnlineRegion] = None