# 01_source/payment_gateway/app/models/payment_model.py
# 02/04/2026 - Enhanced Version with Global Markets Support

from typing import Any, Dict, Literal, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


# ==================== Type Aliases Regionais ====================

# América Latina
BrasilRegionType = Literal["SP", "RJ", "MG", "RS", "BA", "BR"]
MexicoRegionType = Literal["MX"]
ArgentinaRegionType = Literal["AR"]
ColombiaRegionType = Literal["CO"]
ChileRegionType = Literal["CL"]
PeruRegionType = Literal["PE"]
EcuadorRegionType = Literal["EC"]
UruguayRegionType = Literal["UY"]
ParaguayRegionType = Literal["PY"]
BoliviaRegionType = Literal["BO"]
VenezuelaRegionType = Literal["VE"]
CostaRicaRegionType = Literal["CR"]
PanamaRegionType = Literal["PA"]
DominicanRepublicRegionType = Literal["DO"]

# América do Norte
USRegionType = Literal["US_NY", "US_CA", "US_TX", "US_FL", "US_IL"]
CanadaRegionType = Literal["CA_ON", "CA_QC", "CA_BC"]

# Europa Ocidental
PortugalRegionType = Literal["PT"]
SpainRegionType = Literal["ES"]
FranceRegionType = Literal["FR"]
GermanyRegionType = Literal["DE"]
UKRegionType = Literal["UK"]
ItalyRegionType = Literal["IT"]
NetherlandsRegionType = Literal["NL"]
BelgiumRegionType = Literal["BE"]
SwitzerlandRegionType = Literal["CH"]
SwedenRegionType = Literal["SE"]
NorwayRegionType = Literal["NO"]
DenmarkRegionType = Literal["DK"]
FinlandRegionType = Literal["FI"]
IrelandRegionType = Literal["IE"]
AustriaRegionType = Literal["AT"]

# Europa Oriental
PolandRegionType = Literal["PL"]
CzechRepublicRegionType = Literal["CZ"]
GreeceRegionType = Literal["GR"]
HungaryRegionType = Literal["HU"]
RomaniaRegionType = Literal["RO"]
RussiaRegionType = Literal["RU"]
TurkeyRegionType = Literal["TR"]

# África
SouthAfricaRegionType = Literal["ZA"]
NigeriaRegionType = Literal["NG"]
KenyaRegionType = Literal["KE"]
EgyptRegionType = Literal["EG"]
MoroccoRegionType = Literal["MA"]
GhanaRegionType = Literal["GH"]
SenegalRegionType = Literal["SN"]
IvoryCoastRegionType = Literal["CI"]
TanzaniaRegionType = Literal["TZ"]
UgandaRegionType = Literal["UG"]
RwandaRegionType = Literal["RW"]
MozambiqueRegionType = Literal["MZ"]
AngolaRegionType = Literal["AO"]
AlgeriaRegionType = Literal["DZ"]
TunisiaRegionType = Literal["TN"]

# Ásia - Leste Asiático
ChinaRegionType = Literal["CN"]
JapanRegionType = Literal["JP"]
SouthKoreaRegionType = Literal["KR"]

# Ásia - Sudeste Asiático
ThailandRegionType = Literal["TH"]
IndonesiaRegionType = Literal["ID"]
SingaporeRegionType = Literal["SG"]
PhilippinesRegionType = Literal["PH"]
VietnamRegionType = Literal["VN"]
MalaysiaRegionType = Literal["MY"]

# Oriente Médio
UAERegionType = Literal["AE"]
SaudiArabiaRegionType = Literal["SA"]
QatarRegionType = Literal["QA"]
KuwaitRegionType = Literal["KW"]
BahrainRegionType = Literal["BH"]
OmanRegionType = Literal["OM"]
JordanRegionType = Literal["JO"]

# Oceania
AustraliaRegionType = Literal["AU"]
NewZealandRegionType = Literal["NZ"]

# Tipo unificado de região
RegionType = Union[
    BrasilRegionType, MexicoRegionType, ArgentinaRegionType, ColombiaRegionType,
    ChileRegionType, PeruRegionType, EcuadorRegionType, UruguayRegionType,
    ParaguayRegionType, BoliviaRegionType, VenezuelaRegionType, CostaRicaRegionType,
    PanamaRegionType, DominicanRepublicRegionType, USRegionType, CanadaRegionType,
    PortugalRegionType, SpainRegionType, FranceRegionType, GermanyRegionType,
    UKRegionType, ItalyRegionType, NetherlandsRegionType, BelgiumRegionType,
    SwitzerlandRegionType, SwedenRegionType, NorwayRegionType, DenmarkRegionType,
    FinlandRegionType, IrelandRegionType, AustriaRegionType, PolandRegionType,
    CzechRepublicRegionType, GreeceRegionType, HungaryRegionType, RomaniaRegionType,
    RussiaRegionType, TurkeyRegionType, SouthAfricaRegionType, NigeriaRegionType,
    KenyaRegionType, EgyptRegionType, MoroccoRegionType, GhanaRegionType,
    SenegalRegionType, IvoryCoastRegionType, TanzaniaRegionType, UgandaRegionType,
    RwandaRegionType, MozambiqueRegionType, AngolaRegionType, AlgeriaRegionType,
    TunisiaRegionType, ChinaRegionType, JapanRegionType, SouthKoreaRegionType,
    ThailandRegionType, IndonesiaRegionType, SingaporeRegionType, PhilippinesRegionType,
    VietnamRegionType, MalaysiaRegionType, UAERegionType, SaudiArabiaRegionType,
    QatarRegionType, KuwaitRegionType, BahrainRegionType, OmanRegionType,
    JordanRegionType, AustraliaRegionType, NewZealandRegionType
]

# Tipo de canal
ChannelType = Literal["ONLINE", "KIOSK", "SELF_SERVICE", "VENDING_MACHINE", "LOCKER_STATION"]

# ==================== Métodos de Pagamento ====================

# Cartões
CardMethodType = Literal["creditCard", "debitCard", "giftCard", "prepaidCard"]

# Brasil
BrazilMethodType = Literal["pix", "boleto"]

# América Latina
LatinAmericaMethodType = Literal[
    "mercado_pago_wallet", "oxxo", "spei", "rapipago", "pagofacil",
    "servipag", "khipu", "efecty", "pse"
]

# América do Norte
NorthAmericaMethodType = Literal["ach", "venmo", "cashapp", "zelle", "interac"]

# Europa
EuropeMethodType = Literal[
    "apple_pay", "google_pay", "samsung_pay", "mbway", "multibanco_reference",
    "sofort", "giropay", "klarna", "trustly", "ideal", "bancontact", "twint",
    "viabill", "mobilepay", "vips", "blik", "przelewy24", "satispay", "sepa",
    "paypal", "revolut"
]

# África
AfricaMethodType = Literal[
    "m_pesa", "airtel_money", "mtn_money", "orange_money", "vodafone_cash",
    "paystack", "flutterwave", "yoco"
]

# China
ChinaMethodType = Literal["alipay", "wechat_pay", "unionpay", "jd_pay", "dcep"]

# Japão
JapanMethodType = Literal["paypay", "line_pay", "rakuten_pay", "merpay", "au_pay", "konbini"]

# Coreia do Sul
KoreaMethodType = Literal["kakao_pay", "naver_pay", "toss"]

# Tailândia
ThailandMethodType = Literal["promptpay", "truemoney", "rabbit_line_pay"]

# Indonésia
IndonesiaMethodType = Literal["go_pay", "ovo", "dana", "linkaja"]

# Singapura
SingaporeMethodType = Literal["grabpay", "dbs_paylah", "singtel_dash"]

# Filipinas
PhilippinesMethodType = Literal["gcash", "paymaya"]

# Emirados Árabes
UAEMethodType = Literal["tabby", "payby"]

# Turquia
TurkeyMethodType = Literal["troy", "bkm_express", "ininal"]

# Rússia
RussiaMethodType = Literal["mir", "sberbank_online", "yoomoney", "qiwi", "webmoney", "tinkoff"]

# Austrália
AustraliaMethodType = Literal["poli", "afterpay", "zip", "bpay"]

# Globais
GlobalMethodType = Literal["crypto", "cash_on_delivery", "bank_transfer", "direct_debit"]

# Tipo unificado de método de pagamento
PaymentMethodType = Union[
    CardMethodType, BrazilMethodType, LatinAmericaMethodType, NorthAmericaMethodType,
    EuropeMethodType, AfricaMethodType, ChinaMethodType, JapanMethodType,
    KoreaMethodType, ThailandMethodType, IndonesiaMethodType, SingaporeMethodType,
    PhilippinesMethodType, UAEMethodType, TurkeyMethodType, RussiaMethodType,
    AustraliaMethodType, GlobalMethodType
]

# ==================== Interfaces de Pagamento ====================

# Interfaces físicas
PhysicalInterfaceType = Literal["nfc", "chip", "magnetic_stripe", "contactless", "biometric"]

# Interfaces digitais
DigitalInterfaceType = Literal["qr_code", "web_token", "deep_link", "api", "sdk"]

# Interfaces manuais
ManualInterfaceType = Literal["manual", "cod", "pos"]

# Interfaces específicas por região
RegionalInterfaceType = Literal["ussd", "sms", "voice", "qr_bill", "bank_link", "face_recognition", "fingerprint", "barcode", "kiosk"]

# Tipo unificado de interface
PaymentInterfaceType = Union[PhysicalInterfaceType, DigitalInterfaceType, ManualInterfaceType, RegionalInterfaceType]

# ==================== Provedores de Wallet ====================

# Internacionais
GlobalWalletType = Literal["applePay", "googlePay", "samsungPay", "paypal"]

# América Latina
LatinAmericaWalletType = Literal["mercadoPago", "picpay", "rappi", "nequi", "yape", "plin"]

# América do Norte
NorthAmericaWalletType = Literal["venmo", "cashapp", "zelle", "chime"]

# Europa
EuropeWalletType = Literal["revolut", "n26", "monzo", "wise", "mbway", "twint", "viabill", "mobilepay", "satispay", "blik"]

# África
AfricaWalletType = Literal["mPesa", "airtelMoney", "mtnMoney", "orangeMoney", "vodafoneCash", "paystack", "flutterwave", "yoco"]

# China
ChinaWalletType = Literal["alipay", "wechatPay"]

# Japão
JapanWalletType = Literal["paypay", "linePay", "rakutenPay", "merpay", "auPay", "dPay"]

# Coreia do Sul
KoreaWalletType = Literal["kakaoPay", "naverPay", "toss", "payco"]

# Tailândia
ThailandWalletType = Literal["trueMoney", "rabbitLinePay", "scbEasy"]

# Indonésia
IndonesiaWalletType = Literal["goPay", "ovo", "dana", "linkaja", "shopeepay"]

# Singapura
SingaporeWalletType = Literal["grabpay", "dbsPaylah", "singtelDash"]

# Filipinas
PhilippinesWalletType = Literal["gcash", "paymaya"]

# Emirados Árabes
UAEWalletType = Literal["payby", "tabby"]

# Turquia
TurkeyWalletType = Literal["bkmExpress", "ininal", "turkcellPay"]

# Rússia
RussiaWalletType = Literal["yoomoney", "qiwi", "webmoney", "tinkoff"]

# Austrália
AustraliaWalletType = Literal["afterpay", "zip", "beemIt"]

# Tipo unificado de provedor de wallet
WalletProviderType = Union[
    GlobalWalletType, LatinAmericaWalletType, NorthAmericaWalletType,
    EuropeWalletType, AfricaWalletType, ChinaWalletType, JapanWalletType,
    KoreaWalletType, ThailandWalletType, IndonesiaWalletType, SingaporeWalletType,
    PhilippinesWalletType, UAEWalletType, TurkeyWalletType, RussiaWalletType,
    AustraliaWalletType
]


# ==================== Funções Utilitárias ====================

def get_currency_for_region(region: str) -> str:
    """Retorna a moeda padrão para uma região"""
    currency_map = {
        # América Latina
        "SP": "BRL", "RJ": "BRL", "MG": "BRL", "RS": "BRL", "BA": "BRL",
        "MX": "MXN", "AR": "ARS", "CO": "COP", "CL": "CLP", "PE": "PEN",
        "EC": "USD", "UY": "UYU", "PY": "PYG", "BO": "BOB", "VE": "VES",
        "CR": "CRC", "PA": "USD", "DO": "DOP",
        
        # América do Norte
        "US_NY": "USD", "US_CA": "USD", "US_TX": "USD", "US_FL": "USD", "US_IL": "USD",
        "CA_ON": "CAD", "CA_QC": "CAD", "CA_BC": "CAD",
        
        # Europa
        "PT": "EUR", "ES": "EUR", "FR": "EUR", "DE": "EUR", "IT": "EUR",
        "NL": "EUR", "BE": "EUR", "AT": "EUR", "FI": "EUR", "IE": "EUR",
        "UK": "GBP", "CH": "CHF", "SE": "SEK", "NO": "NOK", "DK": "DKK",
        "PL": "PLN", "CZ": "CZK", "HU": "HUF", "RO": "RON", "RU": "RUB",
        "TR": "TRY", "GR": "EUR",
        
        # África
        "ZA": "ZAR", "NG": "NGN", "KE": "KES", "EG": "EGP", "MA": "MAD",
        "GH": "GHS", "SN": "XOF", "CI": "XOF", "TZ": "TZS", "UG": "UGX",
        "RW": "RWF", "MZ": "MZN", "AO": "AOA", "DZ": "DZD", "TN": "TND",
        
        # Ásia
        "CN": "CNY", "JP": "JPY", "KR": "KRW", "TH": "THB", "ID": "IDR",
        "SG": "SGD", "PH": "PHP", "VN": "VND", "MY": "MYR",
        
        # Oriente Médio
        "AE": "AED", "SA": "SAR", "QA": "QAR", "KW": "KWD", "BH": "BHD",
        "OM": "OMR", "JO": "JOD",
        
        # Oceania
        "AU": "AUD", "NZ": "NZD",
    }
    return currency_map.get(region, "USD")


def requires_wallet_provider(payment_method: str) -> bool:
    """Verifica se o método de pagamento requer um provedor de wallet"""
    wallet_methods = {
        "apple_pay", "google_pay", "samsung_pay", "mercado_pago_wallet",
        "paypal", "venmo", "cashapp", "zelle", "revolut", "alipay", "wechat_pay",
        "paypay", "line_pay", "rakuten_pay", "kakao_pay", "naver_pay", "go_pay",
        "ovo", "dana", "grabpay", "gcash", "paymaya", "tabby", "afterpay", "zip",
        "m_pesa", "airtel_money", "mtn_money", "yoomoney", "qiwi"
    }
    return payment_method in wallet_methods


def get_expected_wallet_provider(payment_method: str) -> Optional[str]:
    """Retorna o provedor de wallet esperado para um método de pagamento"""
    provider_map = {
        "apple_pay": "applePay",
        "google_pay": "googlePay",
        "samsung_pay": "samsungPay",
        "mercado_pago_wallet": "mercadoPago",
        "paypal": "paypal",
        "venmo": "venmo",
        "cashapp": "cashapp",
        "alipay": "alipay",
        "wechat_pay": "wechatPay",
        "paypay": "paypay",
        "line_pay": "linePay",
        "rakuten_pay": "rakutenPay",
        "kakao_pay": "kakaoPay",
        "go_pay": "goPay",
        "ovo": "ovo",
        "dana": "dana",
        "grabpay": "grabpay",
        "gcash": "gcash",
        "paymaya": "paymaya",
        "tabby": "tabby",
        "afterpay": "afterpay",
        "zip": "zip",
        "m_pesa": "mPesa",
        "airtel_money": "airtelMoney",
        "mtn_money": "mtnMoney",
        "yoomoney": "yoomoney",
    }
    return provider_map.get(payment_method)


# ==================== Modelos Pydantic ====================

class PaymentRequest(BaseModel):
    regiao: RegionType
    canal: ChannelType = Field(default="KIOSK")

    porta: int = Field(
        ge=1,
        le=999,
        description="Porta/Número do slot (validado dinamicamente no backend)",
    )

    metodo: PaymentMethodType
    interface: PaymentInterfaceType
    valor: float = Field(gt=0, le=9999999.99)

    currency: Optional[str] = None

    locker_id: str = Field(..., description="Identificador da unidade física / locker")
    order_id: Optional[str] = None

    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    wallet_provider: Optional[WalletProviderType] = None
    
    # Campos específicos por região
    national_id: Optional[str] = Field(default=None, description="ID Nacional (China, Japão, Coreia)")
    qr_code_content: Optional[str] = Field(default=None, description="Conteúdo do QR code")
    konbini_code: Optional[str] = Field(default=None, description="Código para pagamento em konbini - Japão")
    ussd_session_id: Optional[str] = Field(default=None, description="USSD session ID - África")
    emirates_id: Optional[str] = Field(default=None, description="Emirates ID - UAE")
    turkish_id: Optional[str] = Field(default=None, description="Turkish ID number")
    inn_number: Optional[str] = Field(default=None, description="INN tax number - Rússia")
    
    # Metadados e tracking
    metadata: Dict[str, Any] = Field(default_factory=dict)
    device_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Timestamps
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
    @field_validator("locker_id")
    @classmethod
    def validate_locker_id(cls, value: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise ValueError("locker_id é obrigatório.")
        if len(normalized) > 50:
            raise ValueError("locker_id deve ter menos de 50 caracteres.")
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
        # Validação básica de formato internacional
        if normalized and not normalized.startswith('+'):
            raise ValueError("customer_phone deve estar no formato internacional (ex: +5511999999999)")
        return normalized or None

    @field_validator("customer_email")
    @classmethod
    def normalize_customer_email(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized and '@' not in normalized:
            raise ValueError("customer_email deve ser um email válido")
        return normalized or None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        normalized = value.strip().upper()
        if len(normalized) != 3:
            raise ValueError("currency deve ser um código ISO 4217 de 3 letras")
        return normalized or None

    @model_validator(mode="after")
    def validate_payment_request(self) -> "PaymentRequest":
        # Define moeda padrão se não fornecida
        if not self.currency:
            self.currency = get_currency_for_region(self.regiao)
        
        # ==================== BRASIL ====================
        brazil_regions = {"SP", "RJ", "MG", "RS", "BA", "BR"}
        
        if self.metodo == "pix":
            if self.regiao not in brazil_regions:
                raise ValueError(f"pix só pode ser utilizado nas regiões do Brasil: {', '.join(brazil_regions)}.")
        
        if self.metodo == "boleto":
            if self.regiao not in brazil_regions:
                raise ValueError(f"boleto só pode ser utilizado nas regiões do Brasil.")
        
        # ==================== PORTUGAL ====================
        if self.metodo == "mbway":
            if self.regiao != "PT":
                raise ValueError("mbway só pode ser utilizado na região PT.")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para pagamentos mbway.")
        
        if self.metodo == "multibanco_reference":
            if self.regiao != "PT":
                raise ValueError("multibanco_reference só pode ser utilizado na região PT.")
        
        # ==================== MÉXICO ====================
        if self.metodo in {"oxxo", "spei"}:
            if self.regiao != "MX":
                raise ValueError(f"{self.metodo} só pode ser utilizado no México (MX).")
        
        # ==================== ARGENTINA ====================
        if self.metodo in {"rapipago", "pagofacil"}:
            if self.regiao != "AR":
                raise ValueError(f"{self.metodo} só pode ser utilizado na Argentina (AR).")
        
        # ==================== CHINA ====================
        if self.metodo in {"alipay", "wechat_pay", "unionpay", "dcep"}:
            if self.regiao != "CN":
                raise ValueError(f"{self.metodo} só pode ser utilizado na China (CN).")
            if not self.qr_code_content:
                raise ValueError("qr_code_content é obrigatório para pagamentos na China.")
            if self.interface not in {"qr_code", "face_recognition", "fingerprint"}:
                raise ValueError(f"{self.metodo} exige interface qr_code, face_recognition ou fingerprint.")
        
        # ==================== JAPÃO ====================
        if self.metodo in {"paypay", "line_pay", "rakuten_pay", "merpay"}:
            if self.regiao != "JP":
                raise ValueError(f"{self.metodo} só pode ser utilizado no Japão (JP).")
        
        if self.metodo == "konbini":
            if self.regiao != "JP":
                raise ValueError("konbini só pode ser utilizado no Japão (JP).")
            if not self.konbini_code:
                raise ValueError("konbini_code é obrigatório para pagamentos em lojas de conveniência.")
            if self.interface != "barcode":
                raise ValueError("konbini exige interface barcode.")
        
        # ==================== TAILÂNDIA ====================
        if self.metodo == "promptpay":
            if self.regiao != "TH":
                raise ValueError("promptpay só pode ser utilizado na Tailândia (TH).")
            if not self.qr_code_content:
                raise ValueError("qr_code_content é obrigatório para PromptPay.")
            if self.interface != "qr_code":
                raise ValueError("PromptPay exige interface qr_code.")
        
        # ==================== INDONÉSIA ====================
        if self.metodo in {"go_pay", "ovo", "dana"}:
            if self.regiao != "ID":
                raise ValueError(f"{self.metodo} só pode ser utilizado na Indonésia (ID).")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para carteiras digitais da Indonésia.")
        
        # ==================== FILIPINAS ====================
        if self.metodo in {"gcash", "paymaya"}:
            if self.regiao != "PH":
                raise ValueError(f"{self.metodo} só pode ser utilizado nas Filipinas (PH).")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para GCash/PayMaya.")
        
        # ==================== EMIRADOS ÁRABES ====================
        if self.metodo in {"tabby", "payby"}:
            if self.regiao != "AE":
                raise ValueError(f"{self.metodo} só pode ser utilizado nos Emirados Árabes (AE).")
            if self.metodo == "tabby" and not self.customer_email:
                raise ValueError("customer_email é obrigatório para Tabby.")
        
        # ==================== TURQUIA ====================
        if self.metodo in {"troy", "bkm_express"}:
            if self.regiao != "TR":
                raise ValueError(f"{self.metodo} só pode ser utilizado na Turquia (TR).")
            if not self.turkish_id:
                raise ValueError("turkish_id é obrigatório para pagamentos na Turquia.")
        
        # ==================== RÚSSIA ====================
        if self.metodo in {"mir", "sberbank_online"}:
            if self.regiao != "RU":
                raise ValueError(f"{self.metodo} só pode ser utilizado na Rússia (RU).")
            if not self.national_id and not self.inn_number:
                raise ValueError("national_id ou inn_number é obrigatório para pagamentos na Rússia.")
        
        # ==================== AUSTRÁLIA ====================
        if self.metodo in {"afterpay", "zip"}:
            if self.regiao != "AU":
                raise ValueError(f"{self.metodo} só pode ser utilizado na Austrália (AU).")
        
        # ==================== ÁFRICA ====================
        african_regions = {"KE", "TZ", "UG", "RW", "ZA", "NG", "GH"}
        
        if self.metodo == "m_pesa":
            if self.regiao not in {"KE", "TZ", "UG", "RW"}:
                raise ValueError(f"m_pesa só pode ser utilizado na África Oriental: KE, TZ, UG, RW.")
            if not self.customer_phone:
                raise ValueError("customer_phone é obrigatório para m_pesa.")
            if not self.ussd_session_id:
                raise ValueError("ussd_session_id é obrigatório para m_pesa.")
            if self.interface != "ussd":
                raise ValueError("m_pesa exige interface ussd.")
        
        if self.metodo in {"airtel_money", "mtn_money"}:
            if self.regiao not in {"NG", "KE", "UG"}:
                raise ValueError(f"{self.metodo} só pode ser utilizado na Nigéria, Quênia ou Uganda.")
            if not self.customer_phone:
                raise ValueError(f"customer_phone é obrigatório para {self.metodo}.")
        
        # ==================== CARTÕES ====================
        if self.metodo in {"creditCard", "debitCard", "giftCard", "prepaidCard"}:
            valid_interfaces = {"nfc", "chip", "web_token", "manual", "contactless", "magnetic_stripe"}
            if self.interface not in valid_interfaces:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.metodo}. "
                    f"Interfaces permitidas: {', '.join(valid_interfaces)}"
                )
        
        # ==================== CARTEIRAS DIGITAIS ====================
        if requires_wallet_provider(self.metodo):
            valid_interfaces = {
                "nfc", "qr_code", "web_token", "deep_link", "api",
                "face_recognition", "fingerprint"
            }
            
            if self.interface not in valid_interfaces:
                raise ValueError(
                    f"payment_interface incompatível com o método {self.metodo}. "
                    f"Interfaces permitidas: {', '.join(valid_interfaces)}"
                )
            
            if not self.wallet_provider:
                raise ValueError("wallet_provider é obrigatório para carteiras digitais.")
            
            expected_provider = get_expected_wallet_provider(self.metodo)
            if expected_provider and self.wallet_provider != expected_provider:
                raise ValueError(
                    f"wallet_provider incompatível com o método {self.metodo}. "
                    f"Esperado: {expected_provider}"
                )
        
        # Validação para métodos que NÃO devem ter wallet_provider
        if not requires_wallet_provider(self.metodo) and self.wallet_provider is not None:
            raise ValueError("wallet_provider só pode ser informado para carteiras digitais.")
        
        # ==================== VALIDAÇÕES DE INTERFACE POR MÉTODO ====================
        
        # PIX
        if self.metodo == "pix":
            if self.interface not in {"qr_code", "web_token", "deep_link"}:
                raise ValueError("pix exige interface qr_code, web_token ou deep_link.")
        
        # Boleto
        if self.metodo == "boleto":
            if self.interface not in {"qr_code", "web_token", "manual", "deep_link"}:
                raise ValueError("boleto exige interface qr_code, web_token, deep_link ou manual.")
        
        # MB Way
        if self.metodo == "mbway":
            if self.interface not in {"qr_code", "web_token", "deep_link"}:
                raise ValueError("mbway exige interface qr_code, web_token ou deep_link.")
        
        # Multibanco
        if self.metodo == "multibanco_reference":
            if self.interface not in {"qr_code", "manual", "web_token", "bank_link"}:
                raise ValueError("multibanco_reference exige interface qr_code, manual, web_token ou bank_link.")
        
        # USSD
        if self.interface == "ussd":
            if self.regiao not in african_regions:
                raise ValueError("USSD só pode ser utilizado na África.")
            if not self.ussd_session_id:
                raise ValueError("ussd_session_id é obrigatório para interface USSD.")
        
        # Face Recognition
        if self.interface == "face_recognition":
            if self.regiao != "CN":
                raise ValueError("Face recognition só pode ser utilizado na China.")
            if not self.national_id:
                raise ValueError("national_id é obrigatório para face recognition.")
        
        return self


class PaymentResponse(BaseModel):
    """Resposta do gateway de pagamento"""
    success: bool
    transaction_id: str
    payment_method: str
    amount: float
    currency: str
    status: str
    message: str
    qr_code_url: Optional[str] = None
    payment_url: Optional[str] = None
    konbini_code: Optional[str] = None
    ussd_code: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentStatusRequest(BaseModel):
    """Requisição para consulta de status de pagamento"""
    transaction_id: str
    order_id: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Resposta de status de pagamento"""
    transaction_id: str
    order_id: Optional[str] = None
    status: str  # pending, completed, failed, refunded, expired
    payment_method: str
    amount: float
    currency: str
    paid_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentRefundRequest(BaseModel):
    """Requisição para reembolso de pagamento"""
    transaction_id: str
    amount: Optional[float] = None  # Se None, reembolsa valor total
    reason: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PaymentRefundResponse(BaseModel):
    """Resposta de reembolso"""
    success: bool
    refund_id: str
    transaction_id: str
    amount: float
    currency: str
    status: str
    message: str
    processed_at: datetime = Field(default_factory=datetime.utcnow)


# Funções de compatibilidade (mantêm a interface original)
def create_payment_request(
    regiao: str,
    canal: str,
    porta: int,
    metodo: str,
    interface: str,
    valor: float,
    locker_id: str,
    **kwargs
) -> PaymentRequest:
    """Função de compatibilidade para criar PaymentRequest"""
    return PaymentRequest(
        regiao=regiao,
        canal=canal,
        porta=porta,
        metodo=metodo,
        interface=interface,
        valor=valor,
        locker_id=locker_id,
        **kwargs
    )