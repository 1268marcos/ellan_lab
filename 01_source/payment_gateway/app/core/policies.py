# 01_source/payment_gateway/app/core/policies.py
# 02/04/2026 - Enhanced Version with Global Market Support
# veja fim do arquivos

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime, timezone
import logging

from app.core.hashing import canonical_json, sha256_prefixed

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Níveis de risco para decisões de política"""
    ALLOW = "allow"
    CHALLENGE = "challenge"
    BLOCK = "block"
    REVIEW = "review"


class PaymentMethodCategory(str, Enum):
    """Categorias de métodos de pagamento para políticas específicas"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    DIGITAL_WALLET = "digital_wallet"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    BNPL = "buy_now_pay_later"
    CRYPTO = "cryptocurrency"
    MOBILE_MONEY = "mobile_money"


class RegionRiskProfile:
    """Perfil de risco específico por região"""
    
    # Configurações de risco por região
    RISK_CONFIGS: Dict[str, Dict[str, Any]] = {
        # América Latina
        "SP": {
            "base_risk_score": 30,
            "fraud_prevalence": "medium",
            "chargeback_rate": 1.2,
            "currency_volatility": "medium",
            "regulatory_level": "high",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,  # R$ 5.000
            "daily_limit_cents": 1000000,  # R$ 10.000
            "velocity_checks": True,
        },
        "MX": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.8,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 450000,  # MXN 4,500
            "daily_limit_cents": 900000,
            "velocity_checks": True,
        },
        "AR": {
            "base_risk_score": 40,
            "fraud_prevalence": "high",
            "chargeback_rate": 2.1,
            "currency_volatility": "very_high",
            "regulatory_level": "medium",
            "allow_max": 29,
            "challenge_min": 30,
            "block_min": 60,
            "require_3ds": True,
            "max_transaction_amount_cents": 300000,
            "daily_limit_cents": 600000,
            "velocity_checks": True,
        },
        "CO": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.5,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 400000,
            "daily_limit_cents": 800000,
            "velocity_checks": True,
        },
        "CL": {
            "base_risk_score": 30,
            "fraud_prevalence": "medium",
            "chargeback_rate": 1.0,
            "currency_volatility": "medium",
            "regulatory_level": "high",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 1000000,
            "velocity_checks": True,
        },
        
        # América do Norte
        "US_NY": {
            "base_risk_score": 25,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.8,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": False,
            "max_transaction_amount_cents": 1000000,  # $10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
            "avs_required": True,
            "cvv_required": True,
        },
        "CA_ON": {
            "base_risk_score": 25,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.7,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": False,
            "max_transaction_amount_cents": 1000000,  # CAD 10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
        },
        
        # Europa Ocidental
        "PT": {
            "base_risk_score": 20,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.5,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,  # PSD2
            "max_transaction_amount_cents": 500000,  # €5,000
            "daily_limit_cents": 2500000,
            "velocity_checks": True,
            "sca_required": True,
        },
        "ES": {
            "base_risk_score": 20,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.5,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "FR": {
            "base_risk_score": 20,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.5,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "DE": {
            "base_risk_score": 20,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.4,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "UK": {
            "base_risk_score": 20,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.6,
            "currency_volatility": "medium",
            "regulatory_level": "very_high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": True,
            "max_transaction_amount_cents": 800000,  # £8,000
            "daily_limit_cents": 4000000,
            "sca_required": True,
        },
        "IT": {
            "base_risk_score": 25,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.7,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "NL": {
            "base_risk_score": 18,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.3,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "BE": {
            "base_risk_score": 18,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.3,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "CH": {
            "base_risk_score": 15,
            "fraud_prevalence": "very_low",
            "chargeback_rate": 0.2,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 54,
            "challenge_min": 55,
            "block_min": 85,
            "require_3ds": False,
            "max_transaction_amount_cents": 1000000,  # CHF 10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
        },
        "SE": {
            "base_risk_score": 18,
            "fraud_prevalence": "very_low",
            "chargeback_rate": 0.3,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "NO": {
            "base_risk_score": 18,
            "fraud_prevalence": "very_low",
            "chargeback_rate": 0.3,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "DK": {
            "base_risk_score": 18,
            "fraud_prevalence": "very_low",
            "chargeback_rate": 0.3,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        "FI": {
            "base_risk_score": 18,
            "fraud_prevalence": "very_low",
            "chargeback_rate": 0.3,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "sca_required": True,
        },
        
        # Europa Oriental
        "PL": {
            "base_risk_score": 30,
            "fraud_prevalence": "medium",
            "chargeback_rate": 1.0,
            "currency_volatility": "medium",
            "regulatory_level": "high",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 400000,  # PLN 4,000
            "daily_limit_cents": 2000000,
            "sca_required": True,
        },
        "CZ": {
            "base_risk_score": 28,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.9,
            "currency_volatility": "medium",
            "regulatory_level": "high",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 400000,
            "daily_limit_cents": 2000000,
            "sca_required": True,
        },
        "HU": {
            "base_risk_score": 30,
            "fraud_prevalence": "medium",
            "chargeback_rate": 1.1,
            "currency_volatility": "medium",
            "regulatory_level": "high",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 400000,
            "daily_limit_cents": 2000000,
            "sca_required": True,
        },
        "RO": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.3,
            "currency_volatility": "medium",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 350000,
            "daily_limit_cents": 1500000,
            "sca_required": True,
        },
        "RU": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.5,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 300000,  # RUB 3,000
            "daily_limit_cents": 1500000,
            "velocity_checks": True,
            "require_mir": True,
        },
        "TR": {
            "base_risk_score": 32,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.4,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 350000,  # TRY 3,500
            "daily_limit_cents": 1500000,
            "velocity_checks": True,
        },
        
        # África
        "ZA": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.6,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": False,
            "max_transaction_amount_cents": 500000,  # ZAR 5,000
            "daily_limit_cents": 2000000,
            "velocity_checks": True,
        },
        "NG": {
            "base_risk_score": 45,
            "fraud_prevalence": "very_high",
            "chargeback_rate": 2.5,
            "currency_volatility": "very_high",
            "regulatory_level": "low",
            "allow_max": 24,
            "challenge_min": 25,
            "block_min": 55,
            "require_3ds": False,
            "max_transaction_amount_cents": 250000,  # NGN 250,000
            "daily_limit_cents": 1000000,
            "velocity_checks": True,
            "require_bvn": True,
        },
        "KE": {
            "base_risk_score": 40,
            "fraud_prevalence": "high",
            "chargeback_rate": 2.0,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 29,
            "challenge_min": 30,
            "block_min": 60,
            "require_3ds": False,
            "max_transaction_amount_cents": 300000,  # KES 3,000
            "daily_limit_cents": 1500000,
            "velocity_checks": True,
            "require_mpesa": True,
        },
        "EG": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.7,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 400000,
            "daily_limit_cents": 2000000,
            "velocity_checks": True,
        },
        
        # Ásia - Leste Asiático
        "CN": {
            "base_risk_score": 25,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.4,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,  # CNY 5,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
            "require_real_name": True,
            "require_alipay_risk": True,
        },
        "JP": {
            "base_risk_score": 20,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.3,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 1000000,  # JPY 10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
            "require_3ds_2_0": True,
        },
        "KR": {
            "base_risk_score": 22,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.4,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,  # KRW 500,000
            "daily_limit_cents": 3000000,
            "velocity_checks": True,
        },
        
        # Ásia - Sudeste Asiático
        "TH": {
            "base_risk_score": 30,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.9,
            "currency_volatility": "medium",
            "regulatory_level": "medium",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 400000,  # THB 4,000
            "daily_limit_cents": 2000000,
            "velocity_checks": True,
            "require_promptpay": False,
        },
        "ID": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.2,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 350000,  # IDR 350,000
            "daily_limit_cents": 1500000,
            "velocity_checks": True,
        },
        "SG": {
            "base_risk_score": 18,
            "fraud_prevalence": "very_low",
            "chargeback_rate": 0.2,
            "currency_volatility": "low",
            "regulatory_level": "very_high",
            "allow_max": 54,
            "challenge_min": 55,
            "block_min": 85,
            "require_3ds": True,
            "max_transaction_amount_cents": 1000000,  # SGD 10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
        },
        "PH": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.3,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 300000,  # PHP 3,000
            "daily_limit_cents": 1500000,
            "velocity_checks": True,
        },
        "VN": {
            "base_risk_score": 35,
            "fraud_prevalence": "high",
            "chargeback_rate": 1.4,
            "currency_volatility": "high",
            "regulatory_level": "medium",
            "allow_max": 34,
            "challenge_min": 35,
            "block_min": 65,
            "require_3ds": True,
            "max_transaction_amount_cents": 300000,
            "daily_limit_cents": 1500000,
            "velocity_checks": True,
        },
        "MY": {
            "base_risk_score": 28,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.8,
            "currency_volatility": "medium",
            "regulatory_level": "high",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 400000,  # MYR 4,000
            "daily_limit_cents": 2000000,
            "velocity_checks": True,
        },
        
        # Oriente Médio
        "AE": {
            "base_risk_score": 25,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.7,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": True,
            "max_transaction_amount_cents": 1000000,  # AED 10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
        },
        "SA": {
            "base_risk_score": 28,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.9,
            "currency_volatility": "medium",
            "regulatory_level": "high",
            "allow_max": 39,
            "challenge_min": 40,
            "block_min": 70,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,  # SAR 5,000
            "daily_limit_cents": 2500000,
            "velocity_checks": True,
        },
        "QA": {
            "base_risk_score": 22,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.5,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": True,
            "max_transaction_amount_cents": 500000,
            "daily_limit_cents": 2500000,
            "velocity_checks": True,
        },
        
        # Oceania
        "AU": {
            "base_risk_score": 22,
            "fraud_prevalence": "medium",
            "chargeback_rate": 0.6,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 44,
            "challenge_min": 45,
            "block_min": 75,
            "require_3ds": True,
            "max_transaction_amount_cents": 1000000,  # AUD 10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
        },
        "NZ": {
            "base_risk_score": 20,
            "fraud_prevalence": "low",
            "chargeback_rate": 0.4,
            "currency_volatility": "low",
            "regulatory_level": "high",
            "allow_max": 49,
            "challenge_min": 50,
            "block_min": 80,
            "require_3ds": True,
            "max_transaction_amount_cents": 1000000,  # NZD 10,000
            "daily_limit_cents": 5000000,
            "velocity_checks": True,
        },
    }
    
    @classmethod
    def get_risk_config(cls, region: str) -> Dict[str, Any]:
        """Retorna configuração de risco para a região"""
        config = cls.RISK_CONFIGS.get(region.upper())
        if not config:
            # Fallback para configuração padrão
            config = cls.RISK_CONFIGS.get("US_NY", {})
            logger.warning(f"No risk config found for region {region}, using fallback")
        return config.copy()
    
    @classmethod
    def get_thresholds(cls, region: str) -> Dict[str, int]:
        """Retorna thresholds de decisão para a região"""
        config = cls.get_risk_config(region)
        return {
            "allow_max": config.get("allow_max", 39),
            "challenge_min": config.get("challenge_min", 40),
            "block_min": config.get("block_min", 70),
        }
    
    @classmethod
    def get_max_transaction_amount(cls, region: str, payment_method: Optional[str] = None) -> int:
        """Retorna valor máximo de transação em centavos"""
        config = cls.get_risk_config(region)
        base_max = config.get("max_transaction_amount_cents", 500000)
        
        # Ajustes por método de pagamento
        if payment_method:
            if payment_method in ["pix", "boleto"]:
                return base_max * 2  # Maior limite para métodos brasileiros
            elif payment_method in ["creditCard", "debitCard"]:
                return base_max
            elif payment_method in ["m_pesa", "airtel_money"]:
                return min(base_max, 200000)  # Limite menor para mobile money
            elif payment_method in ["alipay", "wechat_pay"]:
                return min(base_max, 500000)  # Limite padrão China
        
        return base_max
    
    @classmethod
    def get_daily_limit(cls, region: str) -> int:
        """Retorna limite diário em centavos"""
        config = cls.get_risk_config(region)
        return config.get("daily_limit_cents", 2500000)
    
    @classmethod
    def requires_3ds(cls, region: str, amount_cents: int) -> bool:
        """Verifica se 3DS é obrigatório para a região e valor"""
        config = cls.get_risk_config(region)
        require_3ds = config.get("require_3ds", False)
        
        # Força 3DS para transações acima do limite
        if amount_cents > config.get("max_transaction_amount_cents", 500000):
            return True
        
        return require_3ds


def _policy_hash(policy: Dict[str, Any]) -> str:
    """Gera hash estável para auditoria e cache"""
    return sha256_prefixed(canonical_json(policy))


def _create_policy(
    region: str,
    version: str = "3",
    custom_thresholds: Optional[Dict[str, int]] = None,
    **kwargs
) -> Dict[str, Any]:
    """Cria política para uma região com base nas configurações de risco"""
    risk_config = RegionRiskProfile.get_risk_config(region)
    thresholds = custom_thresholds or {
        "allow_max": risk_config.get("allow_max", 39),
        "challenge_min": risk_config.get("challenge_min", 40),
        "block_min": risk_config.get("block_min", 70),
    }
    
    policy = {
        "policy_id": f"risk_{region.lower()}_v{version}",
        "region": region,
        "version": version,
        "thresholds": thresholds,
        "notes": f"Risk policy for {region} v{version}",
        "risk_profile": {
            "base_risk_score": risk_config.get("base_risk_score", 30),
            "fraud_prevalence": risk_config.get("fraud_prevalence", "medium"),
            "chargeback_rate": risk_config.get("chargeback_rate", 1.0),
            "currency_volatility": risk_config.get("currency_volatility", "medium"),
            "regulatory_level": risk_config.get("regulatory_level", "medium"),
        },
        "limits": {
            "max_transaction_amount_cents": risk_config.get("max_transaction_amount_cents", 500000),
            "daily_limit_cents": risk_config.get("daily_limit_cents", 2500000),
        },
        "requirements": {
            "require_3ds": risk_config.get("require_3ds", False),
            "velocity_checks": risk_config.get("velocity_checks", True),
            "sca_required": risk_config.get("sca_required", False),
            "avs_required": risk_config.get("avs_required", False),
            "cvv_required": risk_config.get("cvv_required", False),
        },
        **kwargs
    }
    
    policy["policy_hash"] = _policy_hash(policy)
    return policy


def list_policies() -> List[Dict[str, Any]]:
    """
    Fonte única das policies com suporte global.
    Inclui todas as regiões suportadas.
    """
    policies = []
    
    # Lista de todas as regiões suportadas
    all_regions = [
        # América Latina
        "SP", "RJ", "MG", "RS", "BA", "BR", "MX", "AR", "CO", "CL", "PE", "EC", "UY", "PY", "BO", "VE", "CR", "PA", "DO",
        # América do Norte
        "US_NY", "US_CA", "US_TX", "US_FL", "US_IL", "CA_ON", "CA_QC", "CA_BC",
        # Europa Ocidental
        "PT", "ES", "FR", "DE", "UK", "IT", "NL", "BE", "CH", "SE", "NO", "DK", "FI", "IE", "AT",
        # Europa Oriental
        "PL", "CZ", "GR", "HU", "RO", "RU", "TR",
        # África
        "ZA", "NG", "KE", "EG", "MA", "GH", "SN", "CI", "TZ", "UG", "RW", "MZ", "AO", "DZ", "TN",
        # Ásia
        "CN", "JP", "KR", "TH", "ID", "SG", "PH", "VN", "MY",
        # Oriente Médio
        "AE", "SA", "QA", "KW", "BH", "OM", "JO",
        # Oceania
        "AU", "NZ",
    ]
    
    # Cria políticas para todas as regiões
    for region in all_regions:
        try:
            policy = _create_policy(region, version="3")
            policies.append(policy)
        except Exception as e:
            logger.error(f"Failed to create policy for region {region}: {e}")
            continue
    
    # Adiciona políticas especiais para métodos de pagamento específicos
    special_policies = [
        {
            "policy_id": "risk_mobile_money_africa_v1",
            "region": "AFRICA_MOBILE",
            "version": "1",
            "thresholds": {"allow_max": 29, "challenge_min": 30, "block_min": 60},
            "notes": "Special policy for African mobile money transactions",
            "applicable_payment_methods": ["m_pesa", "airtel_money", "mtn_money"],
        },
        {
            "policy_id": "risk_bnpl_global_v1",
            "region": "GLOBAL_BNPL",
            "version": "1",
            "thresholds": {"allow_max": 49, "challenge_min": 50, "block_min": 80},
            "notes": "Policy for Buy Now Pay Later services",
            "applicable_payment_methods": ["afterpay", "klarna", "tabby", "zip"],
        },
        {
            "policy_id": "risk_crypto_global_v1",
            "region": "GLOBAL_CRYPTO",
            "version": "1",
            "thresholds": {"allow_max": 34, "challenge_min": 35, "block_min": 65},
            "notes": "Policy for cryptocurrency payments",
            "applicable_payment_methods": ["crypto"],
        },
        {
            "policy_id": "risk_digital_wallet_asia_v1",
            "region": "ASIA_DIGITAL_WALLET",
            "version": "1",
            "thresholds": {"allow_max": 44, "challenge_min": 45, "block_min": 75},
            "notes": "Policy for Asian digital wallets",
            "applicable_payment_methods": ["alipay", "wechat_pay", "paypay", "line_pay", "kakao_pay"],
        },
    ]
    
    for special_policy in special_policies:
        special_policy["policy_hash"] = _policy_hash(special_policy)
        policies.append(special_policy)
    
    return policies


def get_policy_by_region(
    region: str,
    payment_method: Optional[str] = None,
    amount_cents: Optional[int] = None
) -> Dict[str, Any]:
    """
    Obtém política para uma região específica com contexto adicional.
    
    Args:
        region: Código da região (ex: "SP", "CN", "US_NY")
        payment_method: Método de pagamento para ajustes específicos
        amount_cents: Valor da transação para validação de limites
    
    Returns:
        Política de risco para a região
    """
    reg = (region or "").upper()
    
    # Verifica se existe política específica para a região
    for p in list_policies():
        if p["region"] == reg:
            policy = p.copy()
            
            # Adiciona informações contextuais
            risk_config = RegionRiskProfile.get_risk_config(reg)
            policy["context"] = {
                "payment_method": payment_method,
                "amount_cents": amount_cents,
                "max_allowed_amount": RegionRiskProfile.get_max_transaction_amount(reg, payment_method),
                "requires_3ds": RegionRiskProfile.requires_3ds(reg, amount_cents or 0),
                "daily_limit": RegionRiskProfile.get_daily_limit(reg),
            }
            
            return policy
    
    # Fallback seguro - cria política para região desconhecida
    logger.warning(f"No policy found for region {reg}, using fallback")
    
    fallback_policy = {
        "policy_id": f"risk_{reg.lower()}_fallback_v1",
        "region": reg,
        "version": "1",
        "thresholds": {"allow_max": 39, "challenge_min": 40, "block_min": 70},
        "notes": f"Fallback policy for region {reg}",
        "context": {
            "payment_method": payment_method,
            "amount_cents": amount_cents,
            "max_allowed_amount": 500000,
            "requires_3ds": False,
            "daily_limit": 2500000,
        },
    }
    fallback_policy["policy_hash"] = _policy_hash(fallback_policy)
    return fallback_policy


def get_policy_by_payment_method(
    payment_method: str,
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Obtém política específica para um método de pagamento.
    
    Args:
        payment_method: Método de pagamento (ex: "m_pesa", "alipay")
        region: Região para contexto adicional
    
    Returns:
        Política específica para o método de pagamento
    """
    payment_method_lower = payment_method.lower()
    
    # Mapeamento de métodos de pagamento para políticas especiais
    special_policies_map = {
        "m_pesa": "risk_mobile_money_africa_v1",
        "airtel_money": "risk_mobile_money_africa_v1",
        "mtn_money": "risk_mobile_money_africa_v1",
        "afterpay": "risk_bnpl_global_v1",
        "klarna": "risk_bnpl_global_v1",
        "tabby": "risk_bnpl_global_v1",
        "zip": "risk_bnpl_global_v1",
        "crypto": "risk_crypto_global_v1",
        "alipay": "risk_digital_wallet_asia_v1",
        "wechat_pay": "risk_digital_wallet_asia_v1",
        "paypay": "risk_digital_wallet_asia_v1",
        "line_pay": "risk_digital_wallet_asia_v1",
        "kakao_pay": "risk_digital_wallet_asia_v1",
    }
    
    policy_id = special_policies_map.get(payment_method_lower)
    
    if policy_id:
        for p in list_policies():
            if p["policy_id"] == policy_id:
                policy = p.copy()
                policy["applied_for_payment_method"] = payment_method
                if region:
                    policy["original_region"] = region
                return policy
    
    # Fallback para política baseada na região
    if region:
        return get_policy_by_region(region, payment_method=payment_method)
    
    # Fallback global
    fallback = {
        "policy_id": "risk_global_fallback_v1",
        "region": "GLOBAL",
        "version": "1",
        "thresholds": {"allow_max": 39, "challenge_min": 40, "block_min": 70},
        "notes": f"Global fallback policy for payment method {payment_method}",
        "payment_method": payment_method,
    }
    fallback["policy_hash"] = _policy_hash(fallback)
    return fallback


def evaluate_risk_score(
    region: str,
    payment_method: Optional[str] = None,
    amount_cents: Optional[int] = None,
    additional_factors: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Avalia score de risco baseado em múltiplos fatores regionais.
    
    Returns:
        Dicionário com score de risco e decisão recomendada
    """
    risk_config = RegionRiskProfile.get_risk_config(region)
    
    # Score base da região
    base_score = risk_config.get("base_risk_score", 30)
    
    # Ajustes por método de pagamento
    payment_adjustments = {
        "creditCard": -5,
        "debitCard": -3,
        "pix": -10,
        "boleto": +10,
        "m_pesa": +15,
        "airtel_money": +15,
        "cash_on_delivery": +20,
        "crypto": +25,
        "afterpay": -5,
        "alipay": -10,
        "wechat_pay": -10,
    }
    
    adjusted_score = base_score
    if payment_method and payment_method in payment_adjustments:
        adjusted_score += payment_adjustments[payment_method]
    
    # Ajuste por valor da transação
    if amount_cents:
        max_amount = RegionRiskProfile.get_max_transaction_amount(region, payment_method)
        if amount_cents > max_amount:
            adjusted_score += 20  # Penalidade por valor acima do limite
        elif amount_cents > max_amount * 0.8:
            adjusted_score += 10  # Penalidade parcial
        elif amount_cents < max_amount * 0.1:
            adjusted_score -= 5  # Bônus para valores baixos
    
    # Ajustes por fatores adicionais
    if additional_factors:
        if additional_factors.get("new_device"):
            adjusted_score += 15
        if additional_factors.get("unusual_hour"):
            adjusted_score += 10
        if additional_factors.get("high_velocity"):
            adjusted_score += 25
        if additional_factors.get("trusted_device"):
            adjusted_score -= 10
    
    # Garante que o score está dentro dos limites
    final_score = max(0, min(100, adjusted_score))
    
    # Determina decisão baseada nos thresholds
    thresholds = RegionRiskProfile.get_thresholds(region)
    
    if final_score <= thresholds["allow_max"]:
        decision = RiskLevel.ALLOW
    elif final_score <= thresholds["block_min"]:
        decision = RiskLevel.CHALLENGE
    else:
        decision = RiskLevel.BLOCK
    
    return {
        "risk_score": final_score,
        "base_score": base_score,
        "adjustments": {
            "payment_method": payment_adjustments.get(payment_method, 0) if payment_method else 0,
            "amount": (adjusted_score - base_score - (payment_adjustments.get(payment_method, 0) if payment_method else 0)),
            "additional": additional_factors if additional_factors else {},
        },
        "decision": decision.value,
        "thresholds": thresholds,
        "region": region,
    }


def validate_transaction_limits(
    region: str,
    amount_cents: int,
    daily_volume_cents: int,
    payment_method: Optional[str] = None
) -> Dict[str, bool]:
    """
    Valida limites de transação por região.
    
    Returns:
        Dicionário com resultados das validações de limite
    """
    max_transaction = RegionRiskProfile.get_max_transaction_amount(region, payment_method)
    daily_limit = RegionRiskProfile.get_daily_limit(region)
    
    return {
        "within_transaction_limit": amount_cents <= max_transaction,
        "within_daily_limit": daily_volume_cents + amount_cents <= daily_limit,
        "max_transaction_cents": max_transaction,
        "daily_limit_cents": daily_limit,
        "remaining_daily_cents": max(0, daily_limit - daily_volume_cents),
    }


"""
1. Classe RegionRiskProfile
Configurações de risco detalhadas para cada região

Perfis de fraude, chargeback, volatilidade cambial

Thresholds personalizados por região

Limites de transação e diários

2. Novos Enums
RiskLevel: Níveis de decisão (ALLOW, CHALLENGE, BLOCK, REVIEW)

PaymentMethodCategory: Categorização de métodos de pagamento

3. Configurações por Região
Região	Base Risk	Allow Max	Challenge Min	Block Min	3DS	Limite Máximo
SP (Brasil)	30	39	40	70	Sim	R$ 5.000
US_NY (EUA)	25	44	45	75	Não	$10.000
CN (China)	25	44	45	75	Sim	¥5.000
JP (Japão)	20	49	50	80	Sim	¥10.000
AE (UAE)	25	44	45	75	Sim	AED 10.000
NG (Nigéria)	45	24	25	55	Não	₦250.000
RU (Rússia)	35	34	35	65	Sim	₽3.000
4. Novas Funções
get_policy_by_payment_method()
Políticas específicas por método de pagamento

Mobile money (África)

BNPL (Afterpay, Klarna, Tabby)

Carteiras digitais asiáticas

Criptomoedas

evaluate_risk_score()
Cálculo dinâmico de score de risco

Ajustes por método de pagamento

Penalidades por valor acima do limite

Fatores contextuais (novo dispositivo, horário incomum)

validate_transaction_limits()
Validação de limites por transação

Controle de volume diário

Limites específicos por método de pagamento

5. Políticas Especiais
Mobile Money (África):

Limites mais baixos

Maior tolerância a risco

Thresholds mais rigorosos

BNPL Global:

Maior confiança (allow_max = 49)

Limites moderados

Requer validação de identidade

Carteiras Digitais Asiáticas:

Alipay, WeChat Pay, PayPay

Limites mais altos

Integração com sistemas locais

6. Requisitos Regionais
China:

Real name verification

Alipay risk integration

Limites mais baixos para segurança

Japão:

3DS 2.0 obrigatório

Limites altos para cartões

Verificação de identidade

África:

BVN (Nigéria)

M-PESA integration

Velocidade de transação monitorada

Europa (PSD2):

SCA obrigatório

3DS para todas transações

Limites moderados

7. Métricas de Risco por Região
Taxa de chargeback

Prevalência de fraude

Volatilidade cambial

Nível regulatório

8. Sistema de Fallback Robusto
Política padrão para regiões desconhecidas

Logging de warnings

Configuração segura

9. Extensibilidade
Fácil adição de novas regiões

Configurações herdáveis

Ajustes por método de pagamento

10. Auditoria e Rastreamento
Hash de política para cache

Versionamento de políticas

Logging de decisões

"""