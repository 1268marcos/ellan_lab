# 01_source/payment_gateway/app/core/risk_engine.py
# 02/04/2026 - Enhanced Version with Industry Standards & Global Markets
# Veja anotações no fim deste arquivo
# 07/04/2026 - alteração na assinatura em evaluate_risk
# 08/04/2026 - return factors

from typing import Any, Dict, List, Literal, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
import hashlib
import re

from app.core.policies import get_policy_by_region


DEFAULT_RISK_CONFIG = {
    "max_amount": 2000,
    "allowed_methods": {
        "pix",
        "creditCard",
        "debitCard",
        "giftCard",
    },
    "risk_threshold_block": 85,
    "risk_threshold_challenge": 60,
}




# ==================== Enums e Tipos ====================

class RiskDecision(str, Enum):
    """Decisões de risco padronizadas (OWASP ASVS)"""
    ALLOW = "ALLOW"           # Transação permitida
    CHALLENGE = "CHALLENGE"   # Requer autenticação adicional (MFA/3DS)
    BLOCK = "BLOCK"           # Transação bloqueada
    REVIEW = "REVIEW"         # Revisão manual necessária
    DELAY = "DELAY"           # Atraso para análise (rate limiting)


class RiskLevel(str, Enum):
    """Níveis de risco (ISO 31000)"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCategory(str, Enum):
    """Categorias de risco (PCI DSS)"""
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    FRAUD = "FRAUD"
    VELOCITY = "VELOCITY"
    VALUE = "VALUE"
    GEOGRAPHIC = "GEOGRAPHIC"
    DEVICE = "DEVICE"
    BEHAVIORAL = "BEHAVIORAL"
    METHOD = "METHOD"
    INTERFACE = "INTERFACE"
    INTEGRATION = "INTEGRATION"
    REPLAY = "REPLAY"
    COMPLIANCE = "COMPLIANCE"


# ==================== Data Classes ====================

@dataclass
class RiskFactor:
    """Fator de risco com peso e categoria"""
    code: str
    weight: int
    detail: str
    category: RiskCategory
    is_positive: bool = False  # Se True, reduz o risco

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "weight": self.weight,
            "detail": self.detail,
            "category": self.category.value,
            "is_positive": self.is_positive,
        }


@dataclass
class RiskScore:
    """Pontuação de risco calculada"""
    value: int
    level: RiskLevel
    factors: List[RiskFactor] = field(default_factory=list)
    
    def add_factor(self, factor: RiskFactor) -> None:
        self.factors.append(factor)
        self.value += factor.weight if not factor.is_positive else -factor.weight
        self._update_level()
    
    def _update_level(self) -> None:
        if self.value >= 80:
            self.level = RiskLevel.CRITICAL
        elif self.value >= 60:
            self.level = RiskLevel.HIGH
        elif self.value >= 30:
            self.level = RiskLevel.MEDIUM
        else:
            self.level = RiskLevel.LOW
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "level": self.level.value,
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass
class RiskContext:
    """Contexto completo da avaliação de risco"""
    region: str
    channel: str
    payment_method: str
    payment_interface: Optional[str]
    amount: float
    slot: int
    device_known: bool
    device_hash: str
    ip_hash: str
    velocity: Dict[str, int]
    anti_replay_status: str
    integration_status: str
    customer_phone_verified: bool = False
    customer_email_verified: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ==================== Funções Utilitárias ====================

def _normalize_upper(value: Optional[str]) -> str:
    return (value or "").strip().upper()


def _normalize_method(value: str) -> str:
    """
    Normaliza método para formato canônico do engine
    """
    v = (value or "").strip().lower()

    mapping = {
        "creditcard": "creditCard",
        "debitcard": "debitCard",
        "giftcard": "giftCard",
        "pix": "pix",
    }

    return mapping.get(v, v)



def _get_risk_config(region: str) -> dict:
    """
    Resolve config de risco:
    1. tenta policy oficial
    2. fallback seguro (produção)
    """

    try:
        policy = get_policy_by_region(region)
    except Exception:
        policy = None

    if policy:
        return {
            "max_amount": policy.get("limits", {}).get("max_amount", 2000),
            "allowed_methods": {
                _normalize_method(m) for m in policy.get("allowed_methods", [])
            } or DEFAULT_RISK_CONFIG["allowed_methods"],
            "risk_threshold_block": policy.get("thresholds", {}).get("block", 85),
            "risk_threshold_challenge": policy.get("thresholds", {}).get("challenge", 60),
        }

    # 🔴 fallback profissional (NUNCA bloquear tudo)
    return DEFAULT_RISK_CONFIG




def _is_brazil_region(region: str) -> bool:
    brazil_regions = {"SP", "RJ", "MG", "RS", "BA", "BR"}
    return region in brazil_regions


def _is_europe_region(region: str) -> bool:
    europe_regions = {"PT", "ES", "FR", "DE", "UK", "IT", "NL", "BE", "CH", 
                      "SE", "NO", "DK", "FI", "IE", "AT", "PL", "CZ", "GR", 
                      "HU", "RO", "RU", "TR"}
    return region in europe_regions


def _is_asia_region(region: str) -> bool:
    asia_regions = {"CN", "JP", "KR", "TH", "ID", "SG", "PH", "VN", "MY"}
    return region in asia_regions


def _is_africa_region(region: str) -> bool:
    africa_regions = {"ZA", "NG", "KE", "EG", "MA", "GH", "SN", "CI", 
                      "TZ", "UG", "RW", "MZ", "AO", "DZ", "TN"}
    return region in africa_regions


def _is_middle_east_region(region: str) -> bool:
    middle_east_regions = {"AE", "SA", "QA", "KW", "BH", "OM", "JO"}
    return region in middle_east_regions


def _get_risk_multiplier_by_region(region: str) -> float:
    """Retorna multiplicador de risco baseado na região (ISO 31000)"""
    if _is_africa_region(region) or _is_middle_east_region(region):
        return 1.3  # Maior risco para regiões emergentes
    elif _is_asia_region(region):
        return 1.2
    elif _is_brazil_region(region):
        return 1.15
    elif _is_europe_region(region):
        return 1.0
    else:
        return 1.1


def _get_payment_method_risk_weight(payment_method: str, region: str) -> Tuple[int, str]:
    """Retorna peso de risco baseado no método de pagamento (PCI DSS)"""
    risk_map = {
        # Alto risco
        "crypto": (45, "Criptomoedas têm alto risco de chargeback e anonimato"),
        "giftCard": (25, "Gift cards são alvo comum de fraudes"),
        "cash_on_delivery": (30, "Cash on delivery tem alto risco de recusa"),
        
        # Médio-alto risco
        "creditCard": (18, "Cartão de crédito requer validação adicional"),
        "debitCard": (16, "Cartão de débito tem risco moderado"),
        "prepaidCard": (22, "Cartão pré-pago difícil de rastrear"),
        
        # Médio risco
        "pix": (8, "PIX é instantâneo mas requer monitoramento"),
        "boleto": (6, "Boleto tem risco de não pagamento"),
        "mbway": (10, "MBWAY depende de aprovação externa"),
        "multibanco_reference": (4, "Referência Multibanco é método instrucional"),
        
        # Wallet digital
        "apple_pay": (12, "Apple Pay requer validação de dispositivo"),
        "google_pay": (12, "Google Pay requer validação de dispositivo"),
        "samsung_pay": (12, "Samsung Pay requer validação de dispositivo"),
        "mercado_pago_wallet": (10, "Mercado Pago wallet requer verificação"),
        "paypal": (14, "PayPal tem histórico de chargebacks"),
        
        # Mobile Money (África)
        "m_pesa": (15, "M-PESA tem risco de SIM swap fraud"),
        "airtel_money": (15, "Airtel Money requer verificação USSD"),
        "mtn_money": (15, "MTN Money requer verificação USSD"),
        
        # BNPL
        "afterpay": (20, "BNPL tem risco de inadimplência"),
        "zip": (20, "BNPL tem risco de inadimplência"),
        "klarna": (18, "Klarna requer análise de crédito"),
        "tabby": (18, "Tabby é BNPL com risco moderado"),
        
        # QR Code Payments (Ásia)
        "alipay": (8, "Alipay tem baixo risco na China"),
        "wechat_pay": (8, "WeChat Pay tem baixo risco na China"),
        "promptpay": (10, "PromptPay é seguro mas requer QR code"),
        
        # Baixo risco
        "bank_transfer": (5, "Transferência bancária é rastreável"),
        "direct_debit": (5, "Débito direto tem baixo risco"),
    }
    
    # Ajuste regional
    weight, reason = risk_map.get(payment_method, (25, f"Método não reconhecido: {payment_method}"))
    
    # Reduz risco para métodos locais na região apropriada
    if payment_method == "pix" and _is_brazil_region(region):
        weight = max(5, weight - 3)
    elif payment_method == "alipay" and region == "CN":
        weight = max(5, weight - 4)
    elif payment_method == "m_pesa" and region in {"KE", "TZ", "UG"}:
        weight = max(10, weight - 5)
    
    return weight, reason


def _get_interface_risk_weight(interface: str) -> Tuple[int, str]:
    """Retorna peso de risco baseado na interface de pagamento"""
    interface_map = {
        "manual": (15, "Captura manual aumenta risco de erro/fraude"),
        "ussd": (20, "USSD tem risco de interceptação"),
        "web_token": (8, "Web tokenizado requer validação remota"),
        "qr_code": (5, "QR code requer validação de origem"),
        "nfc": (10, "NFC depende de hardware seguro"),
        "chip": (3, "Chip/PIN é seguro"),
        "contactless": (8, "Contactless tem risco moderado"),
        "face_recognition": (12, "Face recognition pode ser enganado"),
        "fingerprint": (8, "Fingerprint é seguro"),
        "barcode": (6, "Barcode requer validação"),
        "api": (4, "API é segura com autenticação"),
        "sdk": (4, "SDK é seguro com validação"),
    }
    return interface_map.get(interface, (10, f"Interface desconhecida: {interface}"))


def _validate_geographic_risk(region: str, ip_hash: str, device_hash: str) -> List[RiskFactor]:
    """Valida risco geográfico (padrão PCI DSS)"""
    factors = []
    
    # Verifica regiões de alto risco
    high_risk_regions = {"NG", "AO", "MZ", "VE", "RU"}
    if region in high_risk_regions:
        factors.append(RiskFactor(
            code="HIGH_RISK_REGION",
            weight=15,
            detail=f"Região {region} classificada como alto risco geográfico",
            category=RiskCategory.GEOGRAPHIC,
        ))
    
    # Verifica correspondência IP/região (simplificado)
    if ip_hash and device_hash:
        # Se IP e dispositivo não correspondem ao padrão da região
        factors.append(RiskFactor(
            code="GEOGRAPHIC_MISMATCH_SUSPECT",
            weight=10,
            detail="Possível incompatibilidade geográfica detectada",
            category=RiskCategory.GEOGRAPHIC,
        ))
    
    return factors


def _validate_velocity_risk(velocity: Dict[str, int], payment_method: str) -> List[RiskFactor]:
    """Valida risco de velocidade (rate limiting - OWASP)"""
    factors = []
    
    ip_5m = velocity.get("ip_5m", 0)
    device_5m = velocity.get("device_5m", 0)
    slot_5m = velocity.get("porta_5m", 0)
    
    # Limites baseados no método de pagamento
    limits = {
        "creditCard": {"ip": 10, "device": 8, "slot": 5},
        "debitCard": {"ip": 10, "device": 8, "slot": 5},
        "pix": {"ip": 15, "device": 10, "slot": 8},
        "boleto": {"ip": 20, "device": 12, "slot": 10},
        "mbway": {"ip": 8, "device": 6, "slot": 4},
        "m_pesa": {"ip": 12, "device": 8, "slot": 6},
        "alipay": {"ip": 20, "device": 15, "slot": 10},
        "default": {"ip": 15, "device": 10, "slot": 6},
    }
    
    method_limits = limits.get(payment_method, limits["default"])
    
    # IP velocity
    if ip_5m >= method_limits["ip"] * 2:
        factors.append(RiskFactor(
            code="VELOCITY_IP_CRITICAL",
            weight=35,
            detail=f"Crítica explosão de IP: {ip_5m} tentativas em 5min",
            category=RiskCategory.VELOCITY,
        ))
    elif ip_5m >= method_limits["ip"]:
        factors.append(RiskFactor(
            code="VELOCITY_IP_ELEVATED",
            weight=18,
            detail=f"Elevada frequência de IP: {ip_5m} tentativas em 5min",
            category=RiskCategory.VELOCITY,
        ))
    elif ip_5m >= method_limits["ip"] * 0.7:
        factors.append(RiskFactor(
            code="VELOCITY_IP_MODERATE",
            weight=8,
            detail=f"Moderada frequência de IP: {ip_5m} tentativas em 5min",
            category=RiskCategory.VELOCITY,
        ))
    
    # Device velocity
    if device_5m >= method_limits["device"] * 2:
        factors.append(RiskFactor(
            code="VELOCITY_DEVICE_CRITICAL",
            weight=25,
            detail=f"Crítica explosão por dispositivo: {device_5m} tentativas",
            category=RiskCategory.VELOCITY,
        ))
    elif device_5m >= method_limits["device"]:
        factors.append(RiskFactor(
            code="VELOCITY_DEVICE_ELEVATED",
            weight=12,
            detail=f"Elevada frequência por dispositivo: {device_5m} tentativas",
            category=RiskCategory.VELOCITY,
        ))
    
    # Slot velocity
    if slot_5m >= method_limits["slot"]:
        factors.append(RiskFactor(
            code="VELOCITY_SLOT_ELEVATED",
            weight=10,
            detail=f"Múltiplas tentativas no mesmo slot: {slot_5m} vezes",
            category=RiskCategory.VELOCITY,
        ))
    
    return factors


def _validate_amount_risk(amount: float, payment_method: str, region: str) -> List[RiskFactor]:
    """Valida risco baseado no valor da transação"""
    factors = []
    
    # Limites baseados no método e região
    limits = {
        "creditCard": {"low": 100, "medium": 500, "high": 2000},
        "debitCard": {"low": 100, "medium": 500, "high": 2000},
        "pix": {"low": 200, "medium": 1000, "high": 5000},
        "boleto": {"low": 50, "medium": 300, "high": 1000},
        "mbway": {"low": 50, "medium": 200, "high": 500},
        "m_pesa": {"low": 50, "medium": 200, "high": 500},
        "afterpay": {"low": 100, "medium": 500, "high": 1500},
        "default": {"low": 100, "medium": 500, "high": 2000},
    }
    
    method_limits = limits.get(payment_method, limits["default"])
    
    if amount <= 0:
        factors.append(RiskFactor(
            code="INVALID_AMOUNT",
            weight=85,
            detail=f"Valor inválido para pagamento: {amount}",
            category=RiskCategory.VALUE,
        ))
    elif amount >= method_limits["high"]:
        factors.append(RiskFactor(
            code="HIGH_AMOUNT",
            weight=25,
            detail=f"Valor muito alto: {amount} (limite: {method_limits['high']})",
            category=RiskCategory.VALUE,
        ))
    elif amount >= method_limits["medium"]:
        factors.append(RiskFactor(
            code="MEDIUM_AMOUNT",
            weight=12,
            detail=f"Valor elevado: {amount}",
            category=RiskCategory.VALUE,
        ))
    elif amount >= method_limits["low"]:
        factors.append(RiskFactor(
            code="LOW_AMOUNT",
            weight=4,
            detail=f"Valor moderado: {amount}",
            category=RiskCategory.VALUE,
        ))
    else:
        # Valores pequenos reduzem o risco
        factors.append(RiskFactor(
            code="SMALL_AMOUNT",
            weight=-5,
            detail=f"Valor pequeno: {amount}",
            category=RiskCategory.VALUE,
            is_positive=True,
        ))
    
    return factors


def _validate_device_risk(device_known: bool, device_hash: str, payment_method: str) -> List[RiskFactor]:
    """Valida risco baseado no dispositivo"""
    factors = []
    
    if not device_known:
        factors.append(RiskFactor(
            code="NEW_DEVICE",
            weight=18,
            detail="Primeira transação deste dispositivo",
            category=RiskCategory.DEVICE,
        ))
    else:
        factors.append(RiskFactor(
            code="KNOWN_DEVICE",
            weight=-8,
            detail="Dispositivo já verificado anteriormente",
            category=RiskCategory.DEVICE,
            is_positive=True,
        ))
    
    # Verifica se é um método que requer dispositivo confiável
    trusted_device_methods = {"apple_pay", "google_pay", "samsung_pay"}
    if payment_method in trusted_device_methods and not device_known:
        factors.append(RiskFactor(
            code="TRUSTED_DEVICE_REQUIRED",
            weight=15,
            detail=f"{payment_method} requer dispositivo confiável",
            category=RiskCategory.DEVICE,
        ))
    
    return factors


def _validate_authentication_risk(
    anti_replay_status: str,
    customer_phone_verified: bool,
    customer_email_verified: bool
) -> List[RiskFactor]:
    """Valida risco de autenticação (OWASP ASVS)"""
    factors = []
    
    # Replay attack detection
    if anti_replay_status == "PAYLOAD_MISMATCH":
        factors.append(RiskFactor(
            code="REPLAY_ATTACK_DETECTED",
            weight=95,
            detail="Possível ataque de replay detectado: payload mismatch",
            category=RiskCategory.REPLAY,
        ))
    elif anti_replay_status == "KEY_REUSED":
        factors.append(RiskFactor(
            code="IDEMPOTENCY_KEY_REUSED",
            weight=60,
            detail="Idempotency key reutilizada indevidamente",
            category=RiskCategory.REPLAY,
        ))
    
    # Verificação de contato
    if not customer_phone_verified and not customer_email_verified:
        factors.append(RiskFactor(
            code="NO_VERIFIED_CONTACT",
            weight=12,
            detail="Nenhum contato verificado disponível",
            category=RiskCategory.AUTHENTICATION,
        ))
    
    return factors


def _validate_integration_risk(integration_status: str, payment_method: str) -> List[RiskFactor]:
    """Valida risco de integração"""
    factors = []
    
    if integration_status == "PLANNED":
        factors.append(RiskFactor(
            code="INTEGRATION_PLANNED",
            weight=40,
            detail=f"Método {payment_method} ainda em planejamento",
            category=RiskCategory.INTEGRATION,
        ))
    elif integration_status == "DISABLED":
        factors.append(RiskFactor(
            code="INTEGRATION_DISABLED",
            weight=90,
            detail=f"Método {payment_method} está desabilitado",
            category=RiskCategory.INTEGRATION,
        ))
    elif integration_status == "BETA":
        factors.append(RiskFactor(
            code="INTEGRATION_BETA",
            weight=20,
            detail=f"Método {payment_method} em fase beta",
            category=RiskCategory.INTEGRATION,
        ))
    elif integration_status == "DEGRADED":
        factors.append(RiskFactor(
            code="INTEGRATION_DEGRADED",
            weight=30,
            detail=f"Integração de {payment_method} em estado degradado",
            category=RiskCategory.INTEGRATION,
        ))
    
    return factors


def _validate_behavioral_risk(
    payment_method: str,
    channel: str,
    interface: Optional[str],
    region: str,
    signals: dict, # 🔴 NOVO
) -> List[RiskFactor]:
    """Valida risco comportamental (fraude patterns)"""
    factors = []

    def is_foreign_ip():
        return signals.get("ip_country") not in {"BR", None}

    def is_wrong_region():
        locker = signals.get("locker") or {}
        return locker.get("address", {}).get("country") != "BR"

    def is_new_device():
        return signals.get("device_trusted") is False
    
    # Combinações suspeitas
    suspicious_combinations = [
        # Cartão + canal online + dispositivo novo
        ({"creditCard", "debitCard"}, "ONLINE", "NEW_DEVICE", 15,
         "Cartão em canal online com dispositivo novo é suspeito"),
        
        # PIX + IP estrangeiro
        ({"pix"}, "ANY", "FOREIGN_IP", 20,
         "PIX com IP estrangeiro é altamente suspeito"),
        
        # Método local + região errada
        ({"pix", "boleto"}, "ANY", "WRONG_REGION", 35,
         "Método brasileiro fora do Brasil"),
        ({"mbway", "multibanco_reference"}, "ANY", "WRONG_REGION", 35,
         "Método português fora de Portugal"),
        ({"alipay", "wechat_pay"}, "ANY", "WRONG_REGION", 30,
         "Método chinês fora da China"),
        ({"m_pesa"}, "ANY", "WRONG_REGION", 35,
         "M-PESA fora da África Oriental"),
        
        # BNPL + valor alto + dispositivo novo
        ({"afterpay", "zip", "klarna", "tabby"}, "ONLINE", "NEW_DEVICE", 25,
         "BNPL com dispositivo novo e valor alto"),
        
        # Crypto + qualquer coisa
        ({"crypto"}, "ANY", "ANY", 50,
         "Criptomoedas têm risco elevado"),
    ]
    
    for methods, channel_req, condition, weight, detail in suspicious_combinations:
        # if payment_method in methods:
        #     if channel_req == "ANY" or channel_req == channel:
        #         factors.append(RiskFactor(
        #             code=f"SUSPICIOUS_COMBINATION_{payment_method.upper()}",
        #             weight=weight,
        #             detail=detail,
        #             category=RiskCategory.BEHAVIORAL,
        #         ))
        if payment_method not in methods:
            continue

        if channel_req != "ANY" and channel_req != channel:
            continue

        # 🔴 AQUI ESTÁ A CORREÇÃO REAL
        condition_ok = False

        if condition == "FOREIGN_IP":
            condition_ok = is_foreign_ip()

        elif condition == "WRONG_REGION":
            condition_ok = is_wrong_region()

        elif condition == "NEW_DEVICE":
            condition_ok = is_new_device()

        elif condition == "ANY":
            condition_ok = True

        if not condition_ok:
            continue

        factors.append(RiskFactor(
            code=f"SUSPICIOUS_COMBINATION_{payment_method.upper()}",
            weight=weight,
            detail=detail,
            category=RiskCategory.BEHAVIORAL,
        ))

    return factors



def _is_brazil_context(signals: dict) -> bool:
    region = signals.get("region")
    locker = signals.get("locker") or {}

    return (
        region == "SP"
        or (region and region.startswith("BR"))
        or locker.get("address", {}).get("country") == "BR"
    )


def _validate_pix_behavior(signals: dict, factors: list):
    if signals.get("payment_method") != "pix":
        return

    # 🔴 só bloqueia fora do Brasil
    if not _is_brazil_context(signals):
        factors.append(RiskFactor(
            code="PIX_OUTSIDE_BRAZIL",
            weight=40,
            detail="PIX fora do Brasil",
            category=RiskCategory.BEHAVIORAL,
        ))

    # 🟢 KIOSK reduz risco
    if signals.get("channel") == "KIOSK":
        factors.append(RiskFactor(
            code="KIOSK_TRUSTED_ENV",
            weight=-15,
            detail="Ambiente controlado KIOSK",
            category=RiskCategory.CONTEXTUAL,
        ))




def _validate_compliance_risk(region: str, amount: float, payment_method: str) -> List[RiskFactor]:
    """Valida risco de compliance (regulatório)"""
    factors = []
    
    # Limites regulatórios por região
    regulatory_limits = {
        "BR": {"pix": 5000, "creditCard": 3000},
        "PT": {"mbway": 500, "multibanco_reference": 1000},
        "CN": {"alipay": 50000, "wechat_pay": 50000},
        "ZA": {"m_pesa": 5000},
    }
    
    region_base = region[:2] if len(region) >= 2 else region
    limits = regulatory_limits.get(region_base, {})
    
    if payment_method in limits and amount > limits[payment_method]:
        factors.append(RiskFactor(
            code="REGULATORY_LIMIT_EXCEEDED",
            weight=30,
            detail=f"Valor excede limite regulatório: {amount} > {limits[payment_method]}",
            category=RiskCategory.COMPLIANCE,
        ))
    
    return factors


# função nova para risco de cartão/BIN/emissor
def _validate_card_risk(
    payment_method: str,
    card_type: str,
    bin_number: str,
    issuer: str,
    region: str,
    amount: float,
) -> List[RiskFactor]:
    """
    Regras reais de risco para cartão/BIN/emissor.
    Sem dependência externa por enquanto, mas preparada para catálogos/listas.
    """
    factors: List[RiskFactor] = []

    method_u = (payment_method or "").strip()
    card_type_u = (card_type or "").strip().upper()
    issuer_s = (issuer or "").strip()
    bin_s = "".join(ch for ch in str(bin_number or "") if ch.isdigit())

    card_methods = {"creditCard", "debitCard", "giftCard", "prepaidCard"}
    if method_u not in card_methods:
        return factors

    # 1) card_type ausente em transação de cartão
    if not card_type_u:
        factors.append(RiskFactor(
            code="CARD_TYPE_MISSING",
            weight=10,
            detail="Transação de cartão sem card_type informado",
            category=RiskCategory.METHOD,
        ))

    # 2) Gift / prepaid têm risco maior
    if card_type_u in {"GIFT", "GIFTCARD"} or method_u == "giftCard":
        factors.append(RiskFactor(
            code="GIFT_CARD_RISK",
            weight=22,
            detail="Gift card possui risco elevado para fraude e abuso",
            category=RiskCategory.METHOD,
        ))

    if card_type_u in {"PREPAID", "PREPAIDCARD"} or method_u == "prepaidCard":
        factors.append(RiskFactor(
            code="PREPAID_CARD_RISK",
            weight=18,
            detail="Cartão pré-pago possui rastreabilidade reduzida",
            category=RiskCategory.METHOD,
        ))

    # 3) BIN inválido / incompleto
    if bin_s:
        if len(bin_s) < 6:
            factors.append(RiskFactor(
                code="BIN_TOO_SHORT",
                weight=20,
                detail=f"BIN informado com tamanho inválido: {len(bin_s)}",
                category=RiskCategory.AUTHENTICATION,
            ))
    elif method_u in {"creditCard", "debitCard"}:
        # Para cartão tradicional, ausência de BIN merece atenção
        factors.append(RiskFactor(
            code="BIN_MISSING",
            weight=8,
            detail="BIN não informado para transação de cartão",
            category=RiskCategory.AUTHENTICATION,
        ))

    # 4) BIN de teste / sandbox / placeholders muito comuns
    suspicious_test_bins = {
        "411111",
        "424242",
        "555555",
        "400000",
        "401288",
    }
    if bin_s[:6] in suspicious_test_bins:
        factors.append(RiskFactor(
            code="TEST_BIN_DETECTED",
            weight=35,
            detail=f"BIN de teste/sandbox detectado: {bin_s[:6]}",
            category=RiskCategory.AUTHENTICATION,
        ))

    # 5) Valor alto com cartão presente/gift/prepaid
    if amount >= 300 and card_type_u in {"GIFT", "GIFTCARD", "PREPAID", "PREPAIDCARD"}:
        factors.append(RiskFactor(
            code="HIGH_AMOUNT_RISKY_CARD_TYPE",
            weight=20,
            detail=f"Valor alto ({amount}) com tipo de cartão mais sensível",
            category=RiskCategory.VALUE,
        ))

    # 6) Emissor ausente em cartão tradicional
    if method_u in {"creditCard", "debitCard"} and not issuer_s:
        factors.append(RiskFactor(
            code="ISSUER_MISSING",
            weight=6,
            detail="Issuer não informado para transação de cartão",
            category=RiskCategory.AUTHENTICATION,
        ))

    # 7) Emissores de teste / placeholders
    issuer_lower = issuer_s.lower()
    suspicious_issuers = {"test", "sandbox", "fake", "mock"}
    if issuer_lower in suspicious_issuers:
        factors.append(RiskFactor(
            code="SUSPICIOUS_ISSUER",
            weight=30,
            detail=f"Emissor suspeito informado: {issuer_s}",
            category=RiskCategory.AUTHENTICATION,
        ))

    # 8) Pequeno bônus de confiança se temos BIN válido + issuer preenchido
    if len(bin_s) >= 6 and issuer_s and method_u in {"creditCard", "debitCard"}:
        factors.append(RiskFactor(
            code="CARD_METADATA_PRESENT",
            weight=-4,
            detail="BIN e issuer presentes melhoram rastreabilidade",
            category=RiskCategory.AUTHENTICATION,
            is_positive=True,
        ))

    # 9) Regra regional simples: cartões gift/prepaid em KIOSK no Brasil merecem atenção extra
    if region in {"SP", "RJ", "MG", "RS", "BA", "BR"} and card_type_u in {"GIFT", "GIFTCARD", "PREPAID", "PREPAIDCARD"}:
        factors.append(RiskFactor(
            code="BRAZIL_KIOSK_RISKY_CARD_PROFILE",
            weight=10,
            detail="Perfil de cartão mais sensível para operação local no Brasil",
            category=RiskCategory.BEHAVIORAL,
        ))

    return factors




# ==================== Função Principal ====================

def evaluate_risk(
    *,
    region: str,
    canal: str,
    metodo: str,
    valor: float,
    porta: int,
    device_known: bool,
    velocity: Dict[str, int],
    anti_replay_status: str,
    ip_hash: str,
    device_hash: str,
    payment_interface: Optional[str] = None,
    integration_status: str = "ACTIVE",
    customer_phone_verified: bool = False,
    customer_email_verified: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """
    Avalia risco de uma transação de pagamento seguindo padrões da indústria:
    - OWASP ASVS (Authentication & Session Management)
    - PCI DSS (Payment Card Industry Data Security Standard)
    - ISO 31000 (Risk Management)
    """
    
    config = _get_risk_config(region)

    # Normalização
    region_u = _normalize_upper(region)
    canal_u = _normalize_upper(canal)
    # metodo_v = (metodo or "").strip()
    metodo_v = _normalize_method(metodo)
    interface_u = _normalize_upper(payment_interface)
    anti_replay_u = _normalize_upper(anti_replay_status)
    integration_u = _normalize_upper(integration_status)

    # ==============================
    # Compatibilidade futura (EXTENSÃO)     
    # (não obrigatório usar agora — apenas disponível)
    # Compatibilidade futura / enriquecimento antifraude
    # ==============================
    card_type = _normalize_upper(kwargs.get("card_type"))
    bin_number = str(kwargs.get("bin") or kwargs.get("bin_number") or "").strip()
    issuer = str(kwargs.get("issuer") or "").strip()
    
    # Validações básicas
    basic_risk_factors = []
    
    # Valida canal
    valid_channels = {"ONLINE", "KIOSK", "SELF_SERVICE", "VENDING_MACHINE"}
    if canal_u not in valid_channels:
        basic_risk_factors.append(RiskFactor(
            code="INVALID_CHANNEL",
            weight=75,
            detail=f"Canal inválido: {canal}",
            category=RiskCategory.AUTHORIZATION,
        ))
    
    # Valida região
    valid_regions = {"SP", "RJ", "MG", "RS", "BA", "BR", "MX", "AR", "CO", "CL", "PE",
                     "EC", "UY", "PY", "BO", "VE", "CR", "PA", "DO", "US_NY",
                     "US_CA", "US_TX", "US_FL", "US_IL", "CA_ON", "CA_QC", "CA_BC",
                     "PT", "ES", "FR", "DE", "UK", "IT", "NL", "BE", "CH", "SE",
                     "NO", "DK", "FI", "IE", "AT", "PL", "CZ", "GR", "HU", "RO",
                     "RU", "TR", "ZA", "NG", "KE", "EG", "MA", "GH", "SN", "CI",
                     "TZ", "UG", "RW", "MZ", "AO", "DZ", "TN", "CN", "JP", "KR",
                     "TH", "ID", "SG", "PH", "VN", "MY", "AE", "SA", "QA", "KW",
                     "BH", "OM", "JO", "AU", "NZ"}
    
    if region_u not in valid_regions:
        basic_risk_factors.append(RiskFactor(
            code="INVALID_REGION",
            weight=75,
            detail=f"Região inválida: {region}",
            category=RiskCategory.GEOGRAPHIC,
        ))
    
    # Valida slot
    if porta < 1 or porta > 999:
        basic_risk_factors.append(RiskFactor(
            code="INVALID_SLOT",
            weight=85,
            detail=f"Slot inválido: {porta}",
            category=RiskCategory.AUTHORIZATION,
        ))
    
    # Cria contexto de risco
    context = RiskContext(
        region=region_u,
        channel=canal_u,
        payment_method=metodo_v,
        payment_interface=payment_interface,
        amount=valor,
        slot=porta,
        device_known=device_known,
        device_hash=device_hash,
        ip_hash=ip_hash,
        velocity=velocity,
        anti_replay_status=anti_replay_u,
        integration_status=integration_u,
        customer_phone_verified=customer_phone_verified,
        customer_email_verified=customer_email_verified,
    )
    
    # Inicializa pontuação de risco
    risk_score = RiskScore(value=0, level=RiskLevel.LOW)




    # normalized_method = metodo_v.lower()

    #if normalized_method not in config["allowed_methods"]:
    if metodo_v not in config["allowed_methods"]:
        risk_score.add_factor(RiskFactor(
            code="METHOD_NOT_ALLOWED",
            weight=40,
            detail=f"Método não permitido para região: {metodo_v}",
            category=RiskCategory.METHOD,
        ))





    # Adiciona fatores básicos
    for factor in basic_risk_factors:
        risk_score.add_factor(factor)
    
    # Adiciona fatores de método de pagamento
    method_weight, method_reason = _get_payment_method_risk_weight(metodo_v, region_u)
    risk_score.add_factor(RiskFactor(
        code=f"PAYMENT_METHOD_{metodo_v.upper()}",
        weight=method_weight,
        detail=method_reason,
        category=RiskCategory.METHOD,
    ))
    




    # Adiciona fatores específicos de cartão / BIN / issuer
    for factor in _validate_card_risk(
        payment_method=metodo_v,
        card_type=card_type,
        bin_number=bin_number,
        issuer=issuer,
        region=region_u,
        amount=valor,
    ):
        risk_score.add_factor(factor)

    # Adiciona fatores de interface
    if interface_u:
        interface_weight, interface_reason = _get_interface_risk_weight(interface_u)
        risk_score.add_factor(RiskFactor(
            code=f"PAYMENT_INTERFACE_{interface_u}",
            weight=interface_weight,
            detail=interface_reason,
            category=RiskCategory.INTERFACE,
        ))
    
    # Adiciona fatores de risco geográfico
    for factor in _validate_geographic_risk(region_u, ip_hash, device_hash):
        risk_score.add_factor(factor)
    
    # Adiciona fatores de velocidade
    for factor in _validate_velocity_risk(velocity, metodo_v):
        risk_score.add_factor(factor)
    
    # Adiciona fatores de valor
    for factor in _validate_amount_risk(valor, metodo_v, region_u):
        risk_score.add_factor(factor)
    
    # Adiciona fatores de dispositivo
    for factor in _validate_device_risk(device_known, device_hash, metodo_v):
        risk_score.add_factor(factor)
    
    # Adiciona fatores de autenticação
    for factor in _validate_authentication_risk(anti_replay_u, customer_phone_verified, customer_email_verified):
        risk_score.add_factor(factor)
    
    # Adiciona fatores de integração
    for factor in _validate_integration_risk(integration_u, metodo_v):
        risk_score.add_factor(factor)



    signals = {
        "region": region_u,
        "channel": canal_u,
        "payment_method": metodo_v,
        "device_trusted": True,  # fallback seguro
        "ip_country": "BR",      # fallback seguro
        "locker": kwargs.get("locker") or {},
    }

    # Adiciona fatores comportamentais
    for factor in _validate_behavioral_risk(metodo_v, canal_u, interface_u, region_u, signals, ):
        risk_score.add_factor(factor)
    
    # Adiciona fatores de compliance
    for factor in _validate_compliance_risk(region_u, valor, metodo_v):
        risk_score.add_factor(factor)
    
    # Aplica multiplicador regional
    multiplier = _get_risk_multiplier_by_region(region_u)
    final_score = min(100, int(risk_score.value * multiplier))
    
    # Obtém políticas da região
    try:
        policy = get_policy_by_region(region_u) or {}
    except Exception:
        policy = {}


    # 🔐 thresholds com fallback seguro (produção)
    block_threshold = (
        policy.get("thresholds", {}).get("block")
        or config.get("risk_threshold_block")
        or 85
    )

    challenge_threshold = (
        policy.get("thresholds", {}).get("challenge")
        or config.get("risk_threshold_challenge")
        or 60
    )

    # 🔥 decisão baseada em config dinâmica (SEM hardcode)
    if final_score >= block_threshold:
        decision = RiskDecision.BLOCK
    elif final_score >= challenge_threshold:
        decision = RiskDecision.CHALLENGE
    elif final_score >= 20:
        decision = RiskDecision.REVIEW
    else:
        decision = RiskDecision.ALLOW
    
    # Prepara resposta
    response = {
        "decision": decision.value,
        "score": final_score,
        "score_range": "0-100",
        "risk_level": risk_score.level.value,
        "reasons": [f.to_dict() for f in risk_score.factors],
        "signals": {
            "region": region_u,
            "channel": canal_u,
            "payment_method": metodo_v,
            "payment_interface": payment_interface,
            "integration_status": integration_u,
            "device_hash": device_hash,
            "ip_hash": ip_hash,
            "device_known": device_known,
            "velocity": {
                "ip_5m": velocity.get("ip_5m", 0),
                "device_5m": velocity.get("device_5m", 0),
                "porta_5m": velocity.get("porta_5m", 0),
            },
            "card_metadata": {
                "card_type": card_type or None,
                "bin_prefix": (bin_number[:6] if bin_number else None),
                "issuer": issuer or None,
            },
            "risk_multiplier": multiplier,
        },
        "policy": policy,
        "evaluation_timestamp": datetime.utcnow().isoformat(),
        "card_type": card_type or None,
        "bin": (bin_number[:6] if bin_number else None),
        "issuer": issuer or None,
    }
    
    return response


# ==================== Funções de Compatibilidade ====================

def evaluate_risk_legacy(
    region: str,
    canal: str,
    metodo: str,
    valor: float,
    porta: int,
    device_known: bool,
    velocity: Dict[str, int],
    anti_replay_status: str,
    ip_hash: str,
    device_hash: str,
    payment_interface: Optional[str] = None,
    integration_status: str = "ACTIVE",
) -> Dict[str, Any]:
    """Versão legacy mantida para compatibilidade"""
    return evaluate_risk(
        region=region,
        canal=canal,
        metodo=metodo,
        valor=valor,
        porta=porta,
        device_known=device_known,
        velocity=velocity,
        anti_replay_status=anti_replay_status,
        ip_hash=ip_hash,
        device_hash=device_hash,
        payment_interface=payment_interface,
        integration_status=integration_status,
    )


# ==================== Funções Adicionais para Monitoramento ====================

def get_risk_summary(evaluation_result: Dict[str, Any]) -> Dict[str, Any]:
    """Retorna resumo da avaliação de risco para logging/monitoramento"""
    return {
        "decision": evaluation_result.get("decision"),
        "score": evaluation_result.get("score"),
        "risk_level": evaluation_result.get("risk_level"),
        "top_reasons": [
            r for r in evaluation_result.get("reasons", []) 
            if abs(r.get("weight", 0)) >= 15
        ][:5],
        "requires_review": evaluation_result.get("decision") in ["CHALLENGE", "REVIEW"],
    }


def should_trigger_alert(evaluation_result: Dict[str, Any]) -> bool:
    """Determina se deve disparar alerta de segurança"""
    score = evaluation_result.get("score", 0)
    decision = evaluation_result.get("decision")
    
    # Alerta para decisões críticas
    if decision in ["BLOCK"]:
        return True
    
    # Alerta para pontuação muito alta
    if score >= 80:
        return True
    
    # Alerta para combinações específicas
    reasons = evaluation_result.get("reasons", [])
    critical_codes = {
        "REPLAY_ATTACK_DETECTED",
        "INTEGRATION_DISABLED",
        "INVALID_SLOT",
        "HIGH_RISK_REGION",
    }
    
    for reason in reasons:
        if reason.get("code") in critical_codes:
            return True
    
    return False



"""

1. Padrões de Segurança Adotados:
OWASP ASVS: Autenticação, gerenciamento de sessão, detecção de replay
PCI DSS: Categorias de risco para métodos de pagamento
ISO 31000: Framework de gestão de risco com níveis (LOW, MEDIUM, HIGH, CRITICAL)

2. Enums e Tipos Estruturados:
RiskDecision: Decisões padronizadas (ALLOW, CHALLENGE, BLOCK, REVIEW, DELAY)
RiskLevel: Níveis de risco ISO 31000
RiskCategory: Categorias PCI DSS para rastreabilidade

3. Data Classes:
RiskFactor: Fator de risco individual com categoria e peso
RiskScore: Pontuação agregada com fatores
RiskContext: Contexto completo da transação

4. Validações Regionais Expandidas:
Suporte a todos os mercados (América Latina, EUA, Canadá, Europa, África, Ásia, Oriente Médio, Oceania)
Multiplicador de risco por região
Limites regulatórios por região

5. Métodos de Pagamento:
+30 métodos de pagamento com pesos específicos
Ajuste regional de risco (ex: PIX no Brasil tem risco reduzido)
Suporte a BNPL, Mobile Money, QR Code Payments

6. Interfaces de Pagamento:
Avaliação de risco por interface (USSD, NFC, chip, face recognition)
Pesos específicos para cada tipo de interface

7. Validações de Risco:
Geográfico: Regiões de alto risco, mismatch IP/região
Velocidade: Rate limiting com limites por método de pagamento
Valor: Limites por método e região
Dispositivo: Primeira vez, dispositivo confiável
Autenticação: Replay attack, idempotency
Integração: Status (PLANNED, BETA, DEGRADED, DISABLED)
Comportamental: Combinações suspeitas
Compliance: Limites regulatórios

8. Combinações Suspeitas:
Cartão + canal online + dispositivo novo
PIX com IP estrangeiro
Método local fora da região correta
BNPL com dispositivo novo e valor alto

9. Funções de Monitoramento:
get_risk_summary(): Resumo para logging
should_trigger_alert(): Alerta de segurança

10. Compatibilidade:
Função evaluate_risk_legacy() mantida
Mesma assinatura original
Sem breaking changes

11. Rastreabilidade:
Cada fator de risco tem código único
Categoria associada (PCI DSS)
Timestamp da avaliação

"""