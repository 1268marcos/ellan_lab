# 01_source/order_pickup_service/app/core/payment_timeout_policy.py
# 02/04/2026 - Enhanced Version with Global Markets Support
# Veja no fim do arquivo - 7. Políticas Específicas
# 06/04/2026 - Deixa de ser usado no KIOSK / Em ONLINE deve causar erro
#

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Set
from enum import Enum


# Constantes globais
DEFAULT_PREPAYMENT_TIMEOUT_SECONDS = 5 * 60
DEFAULT_PIX_TIMEOUT = 5 * 60
DEFAULT_BOLETO_TIMEOUT = 15 * 60
DEFAULT_CARD_TIMEOUT = 2 * 60
DEFAULT_WALLET_TIMEOUT = 10
DEFAULT_CRYPTO_TIMEOUT = 30 * 60  # 30 minutos para criptomoedas
DEFAULT_BANK_TRANSFER_TIMEOUT = 24 * 60 * 60  # 24 horas para transferência bancária


class PaymentMethodFamily(str, Enum):
    """Famílias de métodos de pagamento para políticas consistentes"""
    CARDS = "CARDS"
    WALLETS = "WALLETS"
    PIX = "PIX"
    BOLETO = "BOLETO"
    MBWAY = "MBWAY"
    MULTIBANCO = "MULTIBANCO"
    CRYPTO = "CRYPTO"
    BANK_TRANSFER = "BANK_TRANSFER"
    BNPL = "BNPL"  # Buy Now Pay Later
    MOBILE_MONEY = "MOBILE_MONEY"  # M-PESA, Airtel Money, etc.
    QR_CODE_PAYMENTS = "QR_CODE_PAYMENTS"  # Alipay, WeChat Pay, PromptPay
    KONBINI = "KONBINI"  # Pagamento em lojas de conveniência (Japão)
    USSD = "USSD"  # Pagamentos via USSD (África)
    GIFT_CARD = "GIFT_CARD"
    PREPAID = "PREPAID"


@dataclass(frozen=True)
class TimeoutPolicyKey:
    region_code: str
    order_channel: str
    payment_method: str


def _norm_region_code(region_code: str | None) -> str:
    """Normaliza código da região com suporte a mercados globais"""
    value = (region_code or "").strip().upper()
    
    # Mapeamento de aliases de região
    aliases = {
        # Brasil
        "BRAZIL": "SP",
        "BR": "SP",
        # Portugal
        "PORTUGAL": "PT",
        # México
        "MEXICO": "MX",
        # Argentina
        "ARGENTINA": "AR",
        # Colômbia
        "COLOMBIA": "CO",
        # Chile
        "CHILE": "CL",
        # EUA
        "UNITED_STATES": "US_NY",
        "USA": "US_NY",
        # Canadá
        "CANADA": "CA_ON",
        # China
        "CHINA": "CN",
        # Japão
        "JAPAN": "JP",
        # Tailândia
        "THAILAND": "TH",
        # Indonésia
        "INDONESIA": "ID",
        # Singapura
        "SINGAPORE": "SG",
        # Filipinas
        "PHILIPPINES": "PH",
        # Emirados Árabes
        "UAE": "AE",
        "UNITED_ARAB_EMIRATES": "AE",
        # Turquia
        "TURKEY": "TR",
        # Rússia
        "RUSSIA": "RU",
        # Austrália
        "AUSTRALIA": "AU",
        # África do Sul
        "SOUTH_AFRICA": "ZA",
        # Nigéria
        "NIGERIA": "NG",
        # Quênia
        "KENYA": "KE",
    }
    
    normalized = aliases.get(value, value)
    return normalized or "DEFAULT"


def _norm_order_channel(order_channel: str | None) -> str:
    """Normaliza canal do pedido com suporte a novos canais"""
    value = (order_channel or "").strip().lower()

    aliases = {
        # Kiosk
        "kiosk": "KIOSK",
        "totem": "KIOSK",
        "presential": "KIOSK",
        "in_person": "KIOSK",
        "self_service": "KIOSK",
        "vending_machine": "KIOSK",
        "locker_station": "KIOSK",
        
        # Online
        "online": "ONLINE",
        "web": "ONLINE",
        "app": "ONLINE",
        "mobile": "ONLINE",
        "marketplace": "ONLINE",
        "social_commerce": "ONLINE",
        
        # Outros canais
        "whatsapp": "WHATSAPP",
        "instagram": "SOCIAL",
        "facebook": "SOCIAL",
        "tiktok": "SOCIAL",
        "wechat": "WECHAT",
        "line": "LINE",
    }

    return aliases.get(value, value.upper() or "DEFAULT")


def _norm_payment_method(payment_method: str | None) -> str:
    """Normaliza método de pagamento com suporte a métodos globais"""
    value = (payment_method or "").strip()

    aliases = {
        # Cartões
        "creditCard": "CREDIT_CARD",
        "debitCard": "DEBIT_CARD",
        "giftCard": "GIFT_CARD",
        "prepaidCard": "PREPAID_CARD",
        
        # Brasil
        "pix": "PIX",
        "boleto": "BOLETO",
        
        # América Latina
        "mercado_pago_wallet": "MERCADO_PAGO_WALLET",
        "oxxo": "OXXO",
        "spei": "SPEI",
        "rapipago": "RAPIPAGO",
        "pagofacil": "PAGOFACIL",
        "servipag": "SERVIPAG",
        "khipu": "KHIPU",
        "efecty": "EFECTY",
        "pse": "PSE",
        
        # América do Norte
        "ach": "ACH",
        "venmo": "VENMO",
        "cashapp": "CASHAPP",
        "zelle": "ZELLE",
        "interac": "INTERAC",
        
        # Europa
        "apple_pay": "APPLE_PAY",
        "google_pay": "GOOGLE_PAY",
        "samsung_pay": "SAMSUNG_PAY",
        "mbway": "MBWAY",
        "multibanco_reference": "MULTIBANCO_REFERENCE",
        "sofort": "SOFORT",
        "giropay": "GIROPAY",
        "klarna": "KLARNA",
        "trustly": "TRUSTLY",
        "ideal": "IDEAL",
        "bancontact": "BANCONTACT",
        "twint": "TWINT",
        "viabill": "VIABILL",
        "mobilepay": "MOBILEPAY",
        "vips": "VIPS",
        "blik": "BLIK",
        "przelewy24": "PRZELEWY24",
        "satispay": "SATISPAY",
        "sepa": "SEPA",
        "paypal": "PAYPAL",
        "revolut": "REVOLUT",
        
        # África
        "m_pesa": "M_PESA",
        "airtel_money": "AIRTEL_MONEY",
        "mtn_money": "MTN_MONEY",
        "orange_money": "ORANGE_MONEY",
        "vodafone_cash": "VODAFONE_CASH",
        "paystack": "PAYSTACK",
        "flutterwave": "FLUTTERWAVE",
        "yoco": "YOCO",
        
        # China
        "alipay": "ALIPAY",
        "wechat_pay": "WECHAT_PAY",
        "unionpay": "UNIONPAY",
        "jd_pay": "JD_PAY",
        "dcep": "DCEP",
        
        # Japão
        "paypay": "PAYPAY",
        "line_pay": "LINE_PAY",
        "rakuten_pay": "RAKUTEN_PAY",
        "merpay": "MERPAY",
        "au_pay": "AU_PAY",
        "konbini": "KONBINI",
        
        # Coreia do Sul
        "kakao_pay": "KAKAO_PAY",
        "naver_pay": "NAVER_PAY",
        "toss": "TOSS",
        
        # Tailândia
        "promptpay": "PROMPTPAY",
        "truemoney": "TRUEMONEY",
        "rabbit_line_pay": "RABBIT_LINE_PAY",
        
        # Indonésia
        "go_pay": "GO_PAY",
        "ovo": "OVO",
        "dana": "DANA",
        "linkaja": "LINKAJA",
        
        # Singapura
        "grabpay": "GRABPAY",
        "dbs_paylah": "DBS_PAYLAH",
        "singtel_dash": "SINGTEL_DASH",
        
        # Filipinas
        "gcash": "GCASH",
        "paymaya": "PAYMAYA",
        
        # Emirados Árabes
        "tabby": "TABBY",
        "payby": "PAYBY",
        
        # Turquia
        "troy": "TROY",
        "bkm_express": "BKM_EXPRESS",
        "ininal": "ININAL",
        
        # Rússia
        "mir": "MIR",
        "sberbank_online": "SBERBANK_ONLINE",
        "yoomoney": "YOOMONEY",
        "qiwi": "QIWI",
        "webmoney": "WEBMONEY",
        "tinkoff": "TINKOFF",
        
        # Austrália
        "poli": "POLI",
        "afterpay": "AFTERPAY",
        "zip": "ZIP",
        "bpay": "BPAY",
        
        # Globais
        "crypto": "CRYPTO",
        "cash_on_delivery": "CASH_ON_DELIVERY",
        "bank_transfer": "BANK_TRANSFER",
        "direct_debit": "DIRECT_DEBIT",
        
        # Aliases defensivos para valores já normalizados
        "CREDIT_CARD": "CREDIT_CARD",
        "DEBIT_CARD": "DEBIT_CARD",
        "GIFT_CARD": "GIFT_CARD",
        "PREPAID_CARD": "PREPAID_CARD",
        "PIX": "PIX",
        "BOLETO": "BOLETO",
        "APPLE_PAY": "APPLE_PAY",
        "GOOGLE_PAY": "GOOGLE_PAY",
        "SAMSUNG_PAY": "SAMSUNG_PAY",
        "MBWAY": "MBWAY",
        "MULTIBANCO_REFERENCE": "MULTIBANCO_REFERENCE",
        "MERCADO_PAGO_WALLET": "MERCADO_PAGO_WALLET",
        "ALIPAY": "ALIPAY",
        "WECHAT_PAY": "WECHAT_PAY",
        "M_PESA": "M_PESA",
        "GCASH": "GCASH",
        "PAYMAYA": "PAYMAYA",
        "AFTERPAY": "AFTERPAY",
        "ZIP": "ZIP",
        "TABBY": "TABBY",
        "KONBINI": "KONBINI",
        "CRYPTO": "CRYPTO",
        "BANK_TRANSFER": "BANK_TRANSFER",
    }

    return aliases.get(value, value.upper() or "DEFAULT")


def _get_payment_method_family(payment_method: str) -> PaymentMethodFamily:
    """Retorna a família do método de pagamento para políticas consistentes"""
    
    # Cartões
    if payment_method in {"CREDIT_CARD", "DEBIT_CARD", "PREPAID_CARD"}:
        return PaymentMethodFamily.CARDS
    
    # Gift Card
    if payment_method == "GIFT_CARD":
        return PaymentMethodFamily.GIFT_CARD
    
    # Wallets digitais
    if payment_method in {
        "APPLE_PAY", "GOOGLE_PAY", "SAMSUNG_PAY", "MERCADO_PAGO_WALLET",
        "PAYPAL", "VENMO", "CASHAPP", "ZELLE", "REVOLUT", "PAYPAY", "LINE_PAY",
        "RAKUTEN_PAY", "KAKAO_PAY", "NAVER_PAY", "GO_PAY", "OVO", "DANA",
        "GRABPAY", "DBS_PAYLAH", "GCASH", "PAYMAYA", "YOOMONEY", "QIWI"
    }:
        return PaymentMethodFamily.WALLETS
    
    # Brasil
    if payment_method == "PIX":
        return PaymentMethodFamily.PIX
    if payment_method == "BOLETO":
        return PaymentMethodFamily.BOLETO
    
    # Portugal
    if payment_method == "MBWAY":
        return PaymentMethodFamily.MBWAY
    if payment_method == "MULTIBANCO_REFERENCE":
        return PaymentMethodFamily.MULTIBANCO
    
    # Criptomoedas
    if payment_method == "CRYPTO":
        return PaymentMethodFamily.CRYPTO
    
    # Transferência bancária
    if payment_method in {"BANK_TRANSFER", "DIRECT_DEBIT", "SEPA", "ACH", "SPEI"}:
        return PaymentMethodFamily.BANK_TRANSFER
    
    # BNPL (Buy Now Pay Later)
    if payment_method in {"KLARNA", "AFTERPAY", "ZIP", "TABBY", "CLEARPAY", "AFFIRM"}:
        return PaymentMethodFamily.BNPL
    
    # Mobile Money (África)
    if payment_method in {"M_PESA", "AIRTEL_MONEY", "MTN_MONEY", "ORANGE_MONEY", "VODAFONE_CASH"}:
        return PaymentMethodFamily.MOBILE_MONEY
    
    # Pagamentos via QR Code (Ásia)
    if payment_method in {"ALIPAY", "WECHAT_PAY", "UNIONPAY", "PROMPTPAY", "TRUEMONEY"}:
        return PaymentMethodFamily.QR_CODE_PAYMENTS
    
    # Konbini (Japão)
    if payment_method == "KONBINI":
        return PaymentMethodFamily.KONBINI
    
    # USSD (África)
    if payment_method in {"USSD"}:
        return PaymentMethodFamily.USSD
    
    return PaymentMethodFamily.CARDS  # Default


def _wallet_family_timeout_seconds(payment_method: str) -> int | None:
    """Timeout específico para carteiras digitais"""
    wallet_methods = {
        "APPLE_PAY", "GOOGLE_PAY", "SAMSUNG_PAY", "MERCADO_PAGO_WALLET",
        "PAYPAL", "VENMO", "CASHAPP", "ZELLE", "REVOLUT"
    }
    
    if payment_method in wallet_methods:
        return DEFAULT_WALLET_TIMEOUT
    
    # Mobile Money tem timeout maior
    mobile_money_methods = {"M_PESA", "AIRTEL_MONEY", "MTN_MONEY"}
    if payment_method in mobile_money_methods:
        return 2 * 60  # 2 minutos para mobile money
    
    return None


def _get_region_timeout_multiplier(region_code: str) -> float:
    """Retorna multiplicador de timeout baseado na região"""
    # Regiões com maior latência bancária
    high_latency_regions = {
        "BR", "SP", "RJ", "MG", "RS", "BA",  # Brasil
        "AR",  # Argentina
        "CO",  # Colômbia
        "CL",  # Chile
        "PE",  # Peru
        "ZA",  # África do Sul
        "NG",  # Nigéria
        "KE",  # Quênia
        "RU",  # Rússia
    }
    
    # Regiões com latência muito alta
    very_high_latency_regions = {
        "ID",  # Indonésia
        "PH",  # Filipinas
        "TH",  # Tailândia
        "VN",  # Vietnã
        "AO",  # Angola
        "MZ",  # Moçambique
    }
    
    if region_code in very_high_latency_regions:
        return 1.5
    elif region_code in high_latency_regions:
        return 1.2
    
    return 1.0


# Políticas de timeout expandidas para todos os mercados
_POLICY_SECONDS: Dict[TimeoutPolicyKey, int] = {
    # ==================== BRASIL ====================
    # PIX
    TimeoutPolicyKey("SP", "KIOSK", "PIX"): 5 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "PIX"): 6 * 60,
    TimeoutPolicyKey("RJ", "KIOSK", "PIX"): 5 * 60,
    TimeoutPolicyKey("RJ", "ONLINE", "PIX"): 6 * 60,
    TimeoutPolicyKey("MG", "KIOSK", "PIX"): 5 * 60,
    TimeoutPolicyKey("MG", "ONLINE", "PIX"): 6 * 60,
    
    # Boleto
    TimeoutPolicyKey("SP", "KIOSK", "BOLETO"): 15 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "BOLETO"): 24 * 60 * 60,  # 24h para online
    TimeoutPolicyKey("RJ", "KIOSK", "BOLETO"): 15 * 60,
    TimeoutPolicyKey("RJ", "ONLINE", "BOLETO"): 24 * 60 * 60,
    
    # Cartões
    TimeoutPolicyKey("SP", "KIOSK", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "KIOSK", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "KIOSK", "GIFT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "GIFT_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "KIOSK", "PREPAID_CARD"): 2 * 60,
    TimeoutPolicyKey("SP", "ONLINE", "PREPAID_CARD"): 2 * 60,
    
    # ==================== PORTUGAL ====================
    # MB Way
    TimeoutPolicyKey("PT", "KIOSK", "MBWAY"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "MBWAY"): 6 * 60,
    
    # Multibanco
    TimeoutPolicyKey("PT", "KIOSK", "MULTIBANCO_REFERENCE"): 5 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "MULTIBANCO_REFERENCE"): 6 * 60,
    
    # Cartões
    TimeoutPolicyKey("PT", "KIOSK", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "KIOSK", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "DEBIT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "KIOSK", "GIFT_CARD"): 2 * 60,
    TimeoutPolicyKey("PT", "ONLINE", "GIFT_CARD"): 2 * 60,
    
    # ==================== MÉXICO ====================
    TimeoutPolicyKey("MX", "KIOSK", "OXXO"): 15 * 60,
    TimeoutPolicyKey("MX", "ONLINE", "OXXO"): 24 * 60 * 60,
    TimeoutPolicyKey("MX", "KIOSK", "SPEI"): 5 * 60,
    TimeoutPolicyKey("MX", "ONLINE", "SPEI"): 6 * 60,
    TimeoutPolicyKey("MX", "KIOSK", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("MX", "ONLINE", "CREDIT_CARD"): 2 * 60,
    
    # ==================== ARGENTINA ====================
    TimeoutPolicyKey("AR", "KIOSK", "RAPIPAGO"): 15 * 60,
    TimeoutPolicyKey("AR", "ONLINE", "RAPIPAGO"): 24 * 60 * 60,
    TimeoutPolicyKey("AR", "KIOSK", "PAGOFACIL"): 15 * 60,
    TimeoutPolicyKey("AR", "ONLINE", "PAGOFACIL"): 24 * 60 * 60,
    TimeoutPolicyKey("AR", "KIOSK", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("AR", "ONLINE", "CREDIT_CARD"): 2 * 60,
    
    # ==================== CHINA ====================
    TimeoutPolicyKey("CN", "KIOSK", "ALIPAY"): 1 * 60,
    TimeoutPolicyKey("CN", "ONLINE", "ALIPAY"): 2 * 60,
    TimeoutPolicyKey("CN", "KIOSK", "WECHAT_PAY"): 1 * 60,
    TimeoutPolicyKey("CN", "ONLINE", "WECHAT_PAY"): 2 * 60,
    TimeoutPolicyKey("CN", "KIOSK", "UNIONPAY"): 2 * 60,
    TimeoutPolicyKey("CN", "ONLINE", "UNIONPAY"): 2 * 60,
    TimeoutPolicyKey("CN", "KIOSK", "DCEP"): 1 * 60,  # Yuan digital
    TimeoutPolicyKey("CN", "ONLINE", "DCEP"): 2 * 60,
    
    # ==================== JAPÃO ====================
    TimeoutPolicyKey("JP", "KIOSK", "PAYPAY"): 1 * 60,
    TimeoutPolicyKey("JP", "ONLINE", "PAYPAY"): 2 * 60,
    TimeoutPolicyKey("JP", "KIOSK", "LINE_PAY"): 1 * 60,
    TimeoutPolicyKey("JP", "ONLINE", "LINE_PAY"): 2 * 60,
    TimeoutPolicyKey("JP", "KIOSK", "KONBINI"): 30 * 60,
    TimeoutPolicyKey("JP", "ONLINE", "KONBINI"): 48 * 60 * 60,  # 48h
    TimeoutPolicyKey("JP", "KIOSK", "CREDIT_CARD"): 2 * 60,
    TimeoutPolicyKey("JP", "ONLINE", "CREDIT_CARD"): 2 * 60,
    
    # ==================== TAILÂNDIA ====================
    TimeoutPolicyKey("TH", "KIOSK", "PROMPTPAY"): 2 * 60,
    TimeoutPolicyKey("TH", "ONLINE", "PROMPTPAY"): 5 * 60,
    TimeoutPolicyKey("TH", "KIOSK", "TRUEMONEY"): 1 * 60,
    TimeoutPolicyKey("TH", "ONLINE", "TRUEMONEY"): 2 * 60,
    
    # ==================== INDONÉSIA ====================
    TimeoutPolicyKey("ID", "KIOSK", "GO_PAY"): 2 * 60,
    TimeoutPolicyKey("ID", "ONLINE", "GO_PAY"): 3 * 60,
    TimeoutPolicyKey("ID", "KIOSK", "OVO"): 2 * 60,
    TimeoutPolicyKey("ID", "ONLINE", "OVO"): 3 * 60,
    TimeoutPolicyKey("ID", "KIOSK", "DANA"): 2 * 60,
    TimeoutPolicyKey("ID", "ONLINE", "DANA"): 3 * 60,
    
    # ==================== SINGAPURA ====================
    TimeoutPolicyKey("SG", "KIOSK", "GRABPAY"): 1 * 60,
    TimeoutPolicyKey("SG", "ONLINE", "GRABPAY"): 2 * 60,
    TimeoutPolicyKey("SG", "KIOSK", "DBS_PAYLAH"): 1 * 60,
    TimeoutPolicyKey("SG", "ONLINE", "DBS_PAYLAH"): 2 * 60,
    
    # ==================== FILIPINAS ====================
    TimeoutPolicyKey("PH", "KIOSK", "GCASH"): 2 * 60,
    TimeoutPolicyKey("PH", "ONLINE", "GCASH"): 3 * 60,
    TimeoutPolicyKey("PH", "KIOSK", "PAYMAYA"): 2 * 60,
    TimeoutPolicyKey("PH", "ONLINE", "PAYMAYA"): 3 * 60,
    
    # ==================== EMIRADOS ÁRABES ====================
    TimeoutPolicyKey("AE", "KIOSK", "TABBY"): 5 * 60,
    TimeoutPolicyKey("AE", "ONLINE", "TABBY"): 30 * 60,
    TimeoutPolicyKey("AE", "KIOSK", "PAYBY"): 1 * 60,
    TimeoutPolicyKey("AE", "ONLINE", "PAYBY"): 2 * 60,
    
    # ==================== TURQUIA ====================
    TimeoutPolicyKey("TR", "KIOSK", "TROY"): 2 * 60,
    TimeoutPolicyKey("TR", "ONLINE", "TROY"): 3 * 60,
    TimeoutPolicyKey("TR", "KIOSK", "BKM_EXPRESS"): 1 * 60,
    TimeoutPolicyKey("TR", "ONLINE", "BKM_EXPRESS"): 2 * 60,
    
    # ==================== RÚSSIA ====================
    TimeoutPolicyKey("RU", "KIOSK", "MIR"): 2 * 60,
    TimeoutPolicyKey("RU", "ONLINE", "MIR"): 3 * 60,
    TimeoutPolicyKey("RU", "KIOSK", "YOOMONEY"): 2 * 60,
    TimeoutPolicyKey("RU", "ONLINE", "YOOMONEY"): 3 * 60,
    
    # ==================== AUSTRÁLIA ====================
    TimeoutPolicyKey("AU", "KIOSK", "AFTERPAY"): 5 * 60,
    TimeoutPolicyKey("AU", "ONLINE", "AFTERPAY"): 30 * 60,
    TimeoutPolicyKey("AU", "KIOSK", "ZIP"): 5 * 60,
    TimeoutPolicyKey("AU", "ONLINE", "ZIP"): 30 * 60,
    TimeoutPolicyKey("AU", "KIOSK", "BPAY"): 5 * 60,
    TimeoutPolicyKey("AU", "ONLINE", "BPAY"): 24 * 60 * 60,
    
    # ==================== ÁFRICA ====================
    # M-PESA
    TimeoutPolicyKey("KE", "KIOSK", "M_PESA"): 2 * 60,
    TimeoutPolicyKey("KE", "ONLINE", "M_PESA"): 3 * 60,
    TimeoutPolicyKey("TZ", "KIOSK", "M_PESA"): 2 * 60,
    TimeoutPolicyKey("TZ", "ONLINE", "M_PESA"): 3 * 60,
    TimeoutPolicyKey("UG", "KIOSK", "M_PESA"): 2 * 60,
    TimeoutPolicyKey("UG", "ONLINE", "M_PESA"): 3 * 60,
    
    # Airtel Money
    TimeoutPolicyKey("NG", "KIOSK", "AIRTEL_MONEY"): 2 * 60,
    TimeoutPolicyKey("NG", "ONLINE", "AIRTEL_MONEY"): 3 * 60,
    
    # África do Sul
    TimeoutPolicyKey("ZA", "KIOSK", "YOCO"): 2 * 60,
    TimeoutPolicyKey("ZA", "ONLINE", "YOCO"): 3 * 60,
    TimeoutPolicyKey("ZA", "KIOSK", "PAYSTACK"): 2 * 60,
    TimeoutPolicyKey("ZA", "ONLINE", "PAYSTACK"): 3 * 60,
    
    # ==================== EUROPA OCIDENTAL ====================
    # Alemanha
    TimeoutPolicyKey("DE", "KIOSK", "SOFORT"): 2 * 60,
    TimeoutPolicyKey("DE", "ONLINE", "SOFORT"): 5 * 60,
    TimeoutPolicyKey("DE", "KIOSK", "GIROPAY"): 2 * 60,
    TimeoutPolicyKey("DE", "ONLINE", "GIROPAY"): 5 * 60,
    
    # Holanda
    TimeoutPolicyKey("NL", "KIOSK", "IDEAL"): 1 * 60,
    TimeoutPolicyKey("NL", "ONLINE", "IDEAL"): 3 * 60,
    
    # Bélgica
    TimeoutPolicyKey("BE", "KIOSK", "BANCONTACT"): 1 * 60,
    TimeoutPolicyKey("BE", "ONLINE", "BANCONTACT"): 3 * 60,
    
    # Suíça
    TimeoutPolicyKey("CH", "KIOSK", "TWINT"): 1 * 60,
    TimeoutPolicyKey("CH", "ONLINE", "TWINT"): 2 * 60,
    
    # Polônia
    TimeoutPolicyKey("PL", "KIOSK", "BLIK"): 1 * 60,
    TimeoutPolicyKey("PL", "ONLINE", "BLIK"): 2 * 60,
    
    # Finlândia
    TimeoutPolicyKey("FI", "KIOSK", "MOBILEPAY"): 1 * 60,
    TimeoutPolicyKey("FI", "ONLINE", "MOBILEPAY"): 2 * 60,
    
    # ==================== AMÉRICA DO NORTE ====================
    # EUA
    TimeoutPolicyKey("US_NY", "KIOSK", "VENMO"): 1 * 60,
    TimeoutPolicyKey("US_NY", "ONLINE", "VENMO"): 2 * 60,
    TimeoutPolicyKey("US_NY", "KIOSK", "CASHAPP"): 1 * 60,
    TimeoutPolicyKey("US_NY", "ONLINE", "CASHAPP"): 2 * 60,
    TimeoutPolicyKey("US_NY", "KIOSK", "ACH"): 5 * 60,
    TimeoutPolicyKey("US_NY", "ONLINE", "ACH"): 24 * 60 * 60,
    
    # Canadá
    TimeoutPolicyKey("CA_ON", "KIOSK", "INTERAC"): 1 * 60,
    TimeoutPolicyKey("CA_ON", "ONLINE", "INTERAC"): 3 * 60,
    
    # ==================== GLOBAIS ====================
    # Criptomoedas
    TimeoutPolicyKey("DEFAULT", "ONLINE", "CRYPTO"): DEFAULT_CRYPTO_TIMEOUT,
    TimeoutPolicyKey("DEFAULT", "KIOSK", "CRYPTO"): 15 * 60,
    
    # Transferência bancária
    TimeoutPolicyKey("DEFAULT", "ONLINE", "BANK_TRANSFER"): DEFAULT_BANK_TRANSFER_TIMEOUT,
    TimeoutPolicyKey("DEFAULT", "KIOSK", "BANK_TRANSFER"): 30 * 60,
}


def resolve_prepayment_timeout_seconds(
    *,
    region_code: str | None,
    order_channel: str,
    payment_method: str | None,
) -> int:
    """
    Resolve o timeout de pré-pagamento em segundos para um pedido.
    Suporta mercados globais com políticas específicas por região.
    """
    norm_region = _norm_region_code(region_code)
    norm_channel = _norm_order_channel(order_channel)
    norm_method = _norm_payment_method(payment_method)
    
    # Verifica se é wallet family (timeout rápido)
    wallet_timeout = _wallet_family_timeout_seconds(norm_method)
    if wallet_timeout is not None:
        return wallet_timeout
    
    # Busca política exata
    exact_key = TimeoutPolicyKey(norm_region, norm_channel, norm_method)
    exact_timeout = _POLICY_SECONDS.get(exact_key)
    if exact_timeout is not None:
        return exact_timeout
    
    # Busca política com região DEFAULT
    default_key = TimeoutPolicyKey("DEFAULT", norm_channel, norm_method)
    default_timeout = _POLICY_SECONDS.get(default_key)
    if default_timeout is not None:
        return default_timeout
    
    # Fallback baseado na família do método de pagamento
    family = _get_payment_method_family(norm_method)
    multiplier = _get_region_timeout_multiplier(norm_region)
    
    if family == PaymentMethodFamily.PIX:
        base_timeout = DEFAULT_PIX_TIMEOUT
    elif family == PaymentMethodFamily.BOLETO:
        base_timeout = DEFAULT_BOLETO_TIMEOUT
    elif family == PaymentMethodFamily.CARDS:
        base_timeout = DEFAULT_CARD_TIMEOUT
    elif family == PaymentMethodFamily.WALLETS:
        base_timeout = DEFAULT_WALLET_TIMEOUT
    elif family == PaymentMethodFamily.CRYPTO:
        base_timeout = DEFAULT_CRYPTO_TIMEOUT
    elif family == PaymentMethodFamily.BANK_TRANSFER:
        base_timeout = DEFAULT_BANK_TRANSFER_TIMEOUT
    elif family == PaymentMethodFamily.BNPL:
        base_timeout = 30 * 60  # 30 minutos para BNPL
    elif family == PaymentMethodFamily.MOBILE_MONEY:
        base_timeout = 3 * 60  # 3 minutos para mobile money
    elif family == PaymentMethodFamily.QR_CODE_PAYMENTS:
        base_timeout = 2 * 60  # 2 minutos para pagamentos via QR code
    elif family == PaymentMethodFamily.KONBINI:
        base_timeout = 30 * 60  # 30 minutos para konbini
    elif family == PaymentMethodFamily.USSD:
        base_timeout = 5 * 60  # 5 minutos para USSD
    else:
        base_timeout = DEFAULT_PREPAYMENT_TIMEOUT_SECONDS
    
    # Aplica multiplicador regional
    timeout = int(base_timeout * multiplier)
    
    # Ajusta para canal
    if norm_channel == "KIOSK":
        timeout = min(timeout, 15 * 60)  # Kiosk tem timeout máximo de 15 minutos
    
    return timeout


def get_timeout_info(
    *,
    region_code: str | None,
    order_channel: str,
    payment_method: str | None,
) -> Dict[str, any]:
    """
    Retorna informações detalhadas sobre o timeout para logging e debugging.
    """
    timeout = resolve_prepayment_timeout_seconds(
        region_code=region_code,
        order_channel=order_channel,
        payment_method=payment_method,
    )
    
    norm_method = _norm_payment_method(payment_method)
    family = _get_payment_method_family(norm_method)
    
    return {
        "timeout_seconds": timeout,
        "timeout_minutes": round(timeout / 60, 1),
        "payment_method_family": family.value,
        "normalized_region": _norm_region_code(region_code),
        "normalized_channel": _norm_order_channel(order_channel),
        "normalized_method": norm_method,
    }


# Funções de compatibilidade (mantêm a interface original)
def resolve_prepayment_timeout_seconds_legacy(
    region_code: str | None,
    order_channel: str,
    payment_method: str | None,
) -> int:
    """Versão legacy mantida para compatibilidade"""
    return resolve_prepayment_timeout_seconds(
        region_code=region_code,
        order_channel=order_channel,
        payment_method=payment_method,
    )

"""

7. Políticas Específicas:
Região	    Método	    Kiosk	Online
Brasil	    PIX	        5min	6min
Brasil	    Boleto	    15min	24h
China	    Alipay	    1min	2min
Japão	    Konbini	    30min	48h
Austrália	Afterpay	5min	30min
África	    M-PESA	    2min	3min
EUA	        ACH	        5min	24h


"""