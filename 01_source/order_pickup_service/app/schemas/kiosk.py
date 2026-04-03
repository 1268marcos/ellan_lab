# 01_source/order_pickup_service/app/schemas/kiosk.py
# 02/04/2026 - Enhanced Version with Global Markets

from datetime import datetime
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
    
    # Reino Unido
    PAYPAL = "paypal"
    
    # África
    M_PESA = "m_pesa"
    AIRTEL_MONEY = "airtel_money"
    MTN_MONEY = "mtn_money"
    
    # China
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    UNIONPAY = "unionpay"
    
    # Japão
    PAYPAY = "paypay"
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
    
    # Interfaces digitais
    QR_CODE = "qr_code"
    WEB_TOKEN = "web_token"
    DEEP_LINK = "deep_link"
    API = "api"
    
    # Interfaces manuais
    MANUAL = "manual"
    COD = "cod"  # Cash on Delivery
    
    # Interfaces específicas por região
    USSD = "ussd"  # África
    FACE_RECOGNITION = "face_recognition"  # China
    FINGERPRINT = "fingerprint"  # China, Japão
    BARCODE = "barcode"  # Indonésia, Filipinas, Japão
    VOICE = "voice"  # Voice payments


class KioskWalletProvider(str, Enum):
    # Internacionais
    APPLE_PAY = "applePay"
    GOOGLE_PAY = "googlePay"
    SAMSUNG_PAY = "samsungPay"
    PAYPAL = "paypal"
    
    # América Latina
    MERCADO_PAGO = "mercadoPago"
    PICPAY = "picpay"
    
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
    PAYBY = "payby"
    
    # Turquia
    BKM_EXPRESS = "bkmExpress"
    
    # Rússia
    YOOMONEY = "yoomoney"
    
    # Austrália
    AFTERPAY = "afterpay"
    ZIP = "zip"


class KioskOrderCreateIn(BaseModel):
    region: KioskRegion = Field(..., examples=["PT", "BR", "CN", "JP"])
    sales_channel: KioskSalesChannel = Field(default=KioskSalesChannel.KIOSK)
    fulfillment_type: KioskFulfillmentType = Field(default=KioskFulfillmentType.INSTANT)

    totem_id: str = Field(..., examples=["PT-MAIA-CENTRO-LK-001", "CN-BJ-CBD-001"])
    sku_id: str = Field(..., examples=["bolo_laranja_algarve", "product_123"])

    payment_method: KioskPaymentMethod
    payment_interface: KioskPaymentInterface

    desired_slot: Optional[int] = Field(
        default=None,
        ge=1,
        le=999,
        description="Slot físico do locker (validado dinamicamente no backend/runtime)",
    )
    amount_cents: Optional[int] = Field(default=None, gt=0, le=999999999)

    customer_phone: Optional[str] = Field(default=None, examples=["+351912345678"])
    customer_email: Optional[EmailStr] = Field(default=None, examples=["customer@example.com"])
    wallet_provider: Optional[KioskWalletProvider] = None
    
    # Campos específicos por região
    national_id: Optional[str] = Field(default=None, description="ID Nacional (China, Japão, Coreia)")
    qr_code_content: Optional[str] = Field(default=None, description="Conteúdo do QR code")
    konbini_code: Optional[str] = Field(default=None, description="Código para pagamento em konbini - Japão")
    ussd_session_id: Optional[str] = Field(default=None, description="USSD session ID - África")
    emirates_id: Optional[str] = Field(default=None, description="Emirates ID - UAE")
    turkish_id: Optional[str] = Field(default=None, description="Turkish ID number")
    
    # Campos para validação
    device_id: Optional[str] = Field(default=None, description="Device identifier")
    language: Optional[str] = Field(default="en", description="Idioma da interface do kiosk")

    @field_validator("totem_id")
    @classmethod
    def validate_totem_id(cls, value: str) -> str:
        normalized = (value or "").strip().upper()
        if not normalized:
            raise ValueError("totem_id é obrigatório.")
        if len(normalized) > 50:
            raise ValueError("totem_id deve ter menos de 50 caracteres.")
        return normalized

    @field_validator("sku_id")
    @classmethod
    def validate_sku_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("sku_id é obrigatório.")
        if len(normalized) > 100:
            raise ValueError("sku_id deve ter menos de 100 caracteres.")
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
            raise ValueError("customer_phone deve estar no formato internacional (ex: +5511999999999)")
        return normalized or None

    @model_validator(mode="after")
    def validate_payment_context(self) -> "KioskOrderCreateIn":
        if self.sales_channel not in {KioskSalesChannel.KIOSK, KioskSalesChannel.SELF_SERVICE}:
            raise ValueError("sales_channel inválido para operação em quiosque.")

        if self.fulfillment_type not in {KioskFulfillmentType.INSTANT, KioskFulfillmentType.LOCKER_DISPENSE}:
            raise ValueError("fulfillment_type inválido para pedido KIOSK.")

        # Validações específicas por região - Brasil
        brazil_regions = {KioskRegion.SP, KioskRegion.RJ, KioskRegion.MG, 
                         KioskRegion.RS, KioskRegion.BA}
        
        if self.payment_method == KioskPaymentMethod.PIX:
            if self.region not in brazil_regions:
                raise ValueError(f"pix só pode ser utilizado nas regiões do Brasil: {', '.join([r.value for r in brazil_regions])}")

        if self.payment_method == KioskPaymentMethod.BOLETO:
            if self.region not in brazil_regions:
                raise ValueError(f"boleto só pode ser utilizado nas regiões do Brasil")

        # México
        if self.payment_method in {KioskPaymentMethod.OXXO, KioskPaymentMethod.SPEI}:
            if self.region != KioskRegion.MX:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado no México (MX).")

        # Argentina
        if self.payment_method == KioskPaymentMethod.RAPIPAGO:
            if self.region != KioskRegion.AR:
                raise ValueError("rapipago só pode ser utilizado na Argentina (AR).")

        # Portugal
        if self.payment_method == KioskPaymentMethod.MBWAY:
            if self.region != KioskRegion.PT:
                raise ValueError("mbway só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para pagamento mbway.")

        if self.payment_method == KioskPaymentMethod.MULTIBANCO_REFERENCE:
            if self.region != KioskRegion.PT:
                raise ValueError("multibanco_reference só pode ser utilizado na região PT.")

        # China
        if self.payment_method in {KioskPaymentMethod.ALIPAY, KioskPaymentMethod.WECHAT_PAY, 
                                   KioskPaymentMethod.UNIONPAY}:
            if self.region != KioskRegion.CN:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na China (CN).")
            if not self.qr_code_content:
                raise ValueError("qr_code_content é obrigatório para pagamentos na China.")
            if self.payment_interface != KioskPaymentInterface.QR_CODE:
                raise ValueError("Pagamentos na China exigem payment_interface = qr_code.")

        # Japão
        if self.payment_method in {KioskPaymentMethod.PAYPAY, KioskPaymentMethod.LINE_PAY,
                                   KioskPaymentMethod.RAKUTEN_PAY}:
            if self.region != KioskRegion.JP:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado no Japão (JP).")
            
        if self.payment_method == KioskPaymentMethod.KONBINI:
            if self.region != KioskRegion.JP:
                raise ValueError("konbini só pode ser utilizado no Japão (JP).")
            if not self.konbini_code:
                raise ValueError("konbini_code é obrigatório para pagamento em lojas de conveniência.")
            if self.payment_interface != KioskPaymentInterface.BARCODE:
                raise ValueError("konbini exige payment_interface = barcode.")

        # Tailândia
        if self.payment_method == KioskPaymentMethod.PROMPTPAY:
            if self.region != KioskRegion.TH:
                raise ValueError("promptpay só pode ser utilizado na Tailândia (TH).")
            if not self.qr_code_content:
                raise ValueError("qr_code_content é obrigatório para PromptPay.")
            if self.payment_interface != KioskPaymentInterface.QR_CODE:
                raise ValueError("PromptPay exige payment_interface = qr_code.")

        # Indonésia
        if self.payment_method in {KioskPaymentMethod.GO_PAY, KioskPaymentMethod.OVO, 
                                   KioskPaymentMethod.DANA}:
            if self.region != KioskRegion.ID:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Indonésia (ID).")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para carteiras digitais da Indonésia.")

        # Singapura
        if self.payment_method in {KioskPaymentMethod.GRABPAY, KioskPaymentMethod.DBS_PAYLAH}:
            if self.region != KioskRegion.SG:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado em Singapura (SG).")

        # Filipinas
        if self.payment_method in {KioskPaymentMethod.GCASH, KioskPaymentMethod.PAYMAYA}:
            if self.region != KioskRegion.PH:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado nas Filipinas (PH).")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para GCash/PayMaya.")

        # Emirados Árabes
        if self.payment_method in {KioskPaymentMethod.TABBY, KioskPaymentMethod.PAYBY}:
            if self.region != KioskRegion.AE:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado nos Emirados Árabes (AE).")
            if self.payment_method == KioskPaymentMethod.TABBY and not self.customer_email:
                raise ValueError("customer_email é obrigatório para Tabby.")

        # Turquia
        if self.payment_method in {KioskPaymentMethod.TROY, KioskPaymentMethod.BKM_EXPRESS}:
            if self.region != KioskRegion.TR:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Turquia (TR).")
            if not self.turkish_id:
                raise ValueError("turkish_id é obrigatório para pagamentos na Turquia.")

        # Rússia
        if self.payment_method in {KioskPaymentMethod.MIR, KioskPaymentMethod.YOOMONEY}:
            if self.region != KioskRegion.RU:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Rússia (RU).")
            if not self.national_id:
                raise ValueError("national_id é obrigatório para pagamentos na Rússia.")

        # Austrália
        if self.payment_method in {KioskPaymentMethod.AFTERPAY, KioskPaymentMethod.ZIP, 
                                   KioskPaymentMethod.BPAY}:
            if self.region != KioskRegion.AU:
                raise ValueError(f"{self.payment_method.value} só pode ser utilizado na Austrália (AU).")

        # África - M-PESA
        african_regions = {KioskRegion.KE, KioskRegion.TZ, KioskRegion.UG, KioskRegion.RW}
        if self.payment_method == KioskPaymentMethod.M_PESA:
            if self.region not in african_regions:
                raise ValueError(f"m_pesa só pode ser utilizado na África Oriental: {', '.join([r.value for r in african_regions])}")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para m_pesa.")
            if not self.ussd_session_id:
                raise ValueError("ussd_session_id é obrigatório para m_pesa.")
            if self.payment_interface != KioskPaymentInterface.USSD:
                raise ValueError("m_pesa exige payment_interface = ussd.")

        # Validações de interface para cartões
        if self.payment_method in {
            KioskPaymentMethod.CREDIT_CARD,
            KioskPaymentMethod.DEBIT_CARD,
            KioskPaymentMethod.GIFT_CARD,
            KioskPaymentMethod.PREPAID_CARD,
        }:
            valid_interfaces = {
                KioskPaymentInterface.CHIP,
                KioskPaymentInterface.NFC,
                KioskPaymentInterface.MANUAL,
                KioskPaymentInterface.CONTACTLESS,
                KioskPaymentInterface.MAGNETIC_STRIPE,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.payment_method.value}. "
                    f"Interfaces permitidas: {', '.join([i.value for i in valid_interfaces])}"
                )

        # PIX no kiosk
        if self.payment_method == KioskPaymentMethod.PIX:
            if self.payment_interface != KioskPaymentInterface.QR_CODE:
                raise ValueError("pix no kiosk exige payment_interface = qr_code.")

        # Boleto no kiosk
        if self.payment_method == KioskPaymentMethod.BOLETO:
            if self.payment_interface != KioskPaymentInterface.QR_CODE:
                raise ValueError("boleto no kiosk exige payment_interface = qr_code.")

        # MB Way
        if self.payment_method == KioskPaymentMethod.MBWAY:
            valid_interfaces = {
                KioskPaymentInterface.QR_CODE,
                KioskPaymentInterface.WEB_TOKEN,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(f"mbway exige payment_interface: {', '.join([i.value for i in valid_interfaces])}")

        # Multibanco
        if self.payment_method == KioskPaymentMethod.MULTIBANCO_REFERENCE:
            valid_interfaces = {
                KioskPaymentInterface.QR_CODE,
                KioskPaymentInterface.MANUAL,
            }
            if self.payment_interface not in valid_interfaces:
                raise ValueError(f"multibanco_reference exige payment_interface: {', '.join([i.value for i in valid_interfaces])}")

        # Carteiras digitais
        if KioskPaymentMethod.requires_wallet_provider(self.payment_method):
            valid_interfaces = {
                KioskPaymentInterface.NFC,
                KioskPaymentInterface.WEB_TOKEN,
                KioskPaymentInterface.QR_CODE,
                KioskPaymentInterface.DEEP_LINK,
                KioskPaymentInterface.FACE_RECOGNITION,
                KioskPaymentInterface.FINGERPRINT,
            }
            
            if self.payment_interface not in valid_interfaces:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.payment_method.value}. "
                    f"Interfaces permitidas: {', '.join([i.value for i in valid_interfaces])}"
                )

            if not self.wallet_provider:
                raise ValueError("wallet_provider é obrigatório para carteiras digitais.")

            # Mapeamento de provedores esperados
            expected_provider_map = {
                KioskPaymentMethod.APPLE_PAY: KioskWalletProvider.APPLE_PAY,
                KioskPaymentMethod.GOOGLE_PAY: KioskWalletProvider.GOOGLE_PAY,
                KioskPaymentMethod.SAMSUNG_PAY: KioskWalletProvider.SAMSUNG_PAY,
                KioskPaymentMethod.MERCADO_PAGO_WALLET: KioskWalletProvider.MERCADO_PAGO,
                KioskPaymentMethod.PAYPAL: KioskWalletProvider.PAYPAL,
                KioskPaymentMethod.VENMO: KioskWalletProvider.VENMO,
                KioskPaymentMethod.CASHAPP: KioskWalletProvider.CASHAPP,
                KioskPaymentMethod.M_PESA: KioskWalletProvider.M_PESA,
                KioskPaymentMethod.ALIPAY: KioskWalletProvider.ALIPAY,
                KioskPaymentMethod.WECHAT_PAY: KioskWalletProvider.WECHAT_PAY,
                KioskPaymentMethod.PAYPAY: KioskWalletProvider.PAYPAY,
                KioskPaymentMethod.LINE_PAY: KioskWalletProvider.LINE_PAY,
                KioskPaymentMethod.GO_PAY: KioskWalletProvider.GO_PAY,
                KioskPaymentMethod.OVO: KioskWalletProvider.OVO,
                KioskPaymentMethod.GRABPAY: KioskWalletProvider.GRABPAY,
                KioskPaymentMethod.GCASH: KioskWalletProvider.GCASH,
                KioskPaymentMethod.TABBY: KioskWalletProvider.TABBY,
            }
            
            expected_provider = expected_provider_map.get(self.payment_method)
            if expected_provider and self.wallet_provider != expected_provider:
                raise ValueError(
                    f"wallet_provider incompatível com o método {self.payment_method.value}. "
                    f"Esperado: {expected_provider.value}"
                )

        # Validação para métodos que NÃO devem ter wallet_provider
        if not KioskPaymentMethod.requires_wallet_provider(self.payment_method) and self.wallet_provider is not None:
            raise ValueError("wallet_provider só pode ser informado para carteiras digitais.")

        # customer_phone permitido apenas para métodos específicos
        methods_allowing_phone = {
            KioskPaymentMethod.MBWAY, KioskPaymentMethod.M_PESA, KioskPaymentMethod.AIRTEL_MONEY,
            KioskPaymentMethod.MTN_MONEY, KioskPaymentMethod.GO_PAY, KioskPaymentMethod.OVO,
            KioskPaymentMethod.DANA, KioskPaymentMethod.GCASH, KioskPaymentMethod.PAYMAYA
        }
        
        if self.customer_phone is not None and self.payment_method not in methods_allowing_phone:
            raise ValueError(f"customer_phone só pode ser informado para métodos: {', '.join([m.value for m in methods_allowing_phone])}")

        # Validação de amount_cents
        if self.payment_method not in {KioskPaymentMethod.GIFT_CARD} and self.amount_cents is None:
            if self.payment_method != KioskPaymentMethod.GIFT_CARD:
                raise ValueError(f"amount_cents é obrigatório para {self.payment_method.value}")

        # Face recognition
        if self.payment_interface == KioskPaymentInterface.FACE_RECOGNITION:
            if self.region != KioskRegion.CN:
                raise ValueError("Face recognition só pode ser utilizado na China.")
            if not self.national_id:
                raise ValueError("national_id é obrigatório para face recognition.")

        return self


class KioskCustomerIdentifyIn(BaseModel):
    order_id: str
    phone: Optional[str] = Field(default=None, examples=["+351912345678"])
    email: Optional[EmailStr] = None
    qr_code: Optional[str] = Field(default=None, description="QR code para identificação")
    national_id: Optional[str] = Field(default=None, description="ID nacional para identificação")

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
        if normalized and not re_compile(r'^\+[1-9]\d{1,14}$').match(normalized):
            raise ValueError("phone deve estar no formato internacional")
        return normalized or None

    @model_validator(mode="after")
    def validate_identification(self) -> "KioskCustomerIdentifyIn":
        if not any([self.phone, self.email, self.qr_code, self.national_id]):
            raise ValueError("É necessário fornecer pelo menos um método de identificação: phone, email, qr_code ou national_id")
        return self


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
    region: Optional[str] = None
    currency: Optional[str] = None

    payment_status: Optional[str] = None
    payment_instruction_type: Optional[str] = None
    payment_payload: Dict[str, Any] = Field(default_factory=dict)
    
    qr_code_url: Optional[str] = None
    konbini_code: Optional[str] = None
    ussd_code: Optional[str] = None


class KioskPaymentApprovedOut(BaseModel):
    order_id: str
    slot: int
    status: str
    allocation_id: str
    payment_method: Optional[str] = None
    payment_interface: Optional[str] = None
    region: Optional[str] = None

    receipt_code: Optional[str] = None
    receipt_print_path: Optional[str] = None
    receipt_json_path: Optional[str] = None
    
    digital_receipt_url: Optional[str] = None
    sms_sent: bool = False
    email_sent: bool = False

    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class KioskIdentifyOut(BaseModel):
    ok: bool
    message: str
    order_id: Optional[str] = None
    customer_name: Optional[str] = None
    slot: Optional[int] = None
    status: Optional[str] = None


class KioskHealthCheckOut(BaseModel):
    """Modelo para health check do kiosk"""
    status: str
    version: str
    region: Optional[str] = None
    totem_id: Optional[str] = None
    online: bool = True
    last_ping: datetime = Field(default_factory=datetime.utcnow)


class KioskInventoryCheckIn(BaseModel):
    """Modelo para verificar disponibilidade de produtos no kiosk"""
    totem_id: str
    sku_ids: List[str] = Field(..., min_items=1, max_items=50)
    region: KioskRegion


class KioskInventoryCheckOut(BaseModel):
    """Resposta da verificação de inventário"""
    totem_id: str
    available_products: Dict[str, int] = Field(default_factory=dict)
    unavailable_products: List[str] = Field(default_factory=list)
    last_updated: datetime