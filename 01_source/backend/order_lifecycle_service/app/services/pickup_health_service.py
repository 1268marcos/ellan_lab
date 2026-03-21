# 01_source/backend/order_lifecycle_service/app/services/pickup_health_service.py
# Deverá ser uma camada acima do executive summary (presente em intenal.py)
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from math import isnan


# =========================
# CONFIGURAÇÃO DE PESOS
# =========================

WEIGHTS = {
    "efficiency": 0.40,
    "reliability": 0.20,
    "risk": 0.25,
    "trend": 0.15,
}


# =========================
# HELPERS
# =========================

def _clamp(v: float, min_v: float = 0.0, max_v: float = 100.0) -> float:
    return max(min_v, min(max_v, v))


def _safe(v: Optional[float], default: float = 0.0) -> float:
    if v is None:
        return default
    try:
        if isnan(v):
            return default
        return float(v)
    except Exception:
        return default


# =========================
# COMPONENTES
# =========================

def compute_efficiency_score(signals: Dict[str, Any]) -> float:
    """
    Mede quão bem o fluxo está funcionando.
    """
    success_rate = _safe(signals.get("pickup_success_rate"), 0.0)  # 0..1
    expiration_rate = _safe(signals.get("expiration_rate"), 0.0)   # 0..1
    cancel_rate = _safe(signals.get("cancel_rate"), 0.0)           # 0..1
    avg_minutes = _safe(signals.get("avg_pickup_minutes"), 999.0)

    success_score = success_rate * 100
    penalty_exp = expiration_rate * 100
    penalty_cancel = cancel_rate * 100

    # tempo: ideal < 30 min, ruim > 120 min
    if avg_minutes <= 30:
        time_score = 100
    elif avg_minutes >= 120:
        time_score = 0
    else:
        time_score = 100 - ((avg_minutes - 30) / 90) * 100

    score = (
        success_score * 0.5 +
        time_score * 0.3 +
        (100 - penalty_exp) * 0.1 +
        (100 - penalty_cancel) * 0.1
    )

    return _clamp(score)


def compute_reliability_score(signals: Dict[str, Any]) -> float:
    """
    Mede confiança estatística.
    """
    sample_size = _safe(signals.get("sample_size"), 0)

    if sample_size >= 200:
        return 100
    if sample_size >= 100:
        return 85
    if sample_size >= 50:
        return 70
    if sample_size >= 20:
        return 50
    if sample_size > 0:
        return 30
    return 10


def compute_risk_score(signals: Dict[str, Any]) -> float:
    """
    Quanto maior, pior.
    """
    expiration = _safe(signals.get("expiration_rate"), 0.0)
    cancel = _safe(signals.get("cancel_rate"), 0.0)

    saturation = signals.get("saturation_level")

    sat_score = {
        "low": 20,
        "medium": 50,
        "high": 80,
    }.get(saturation, 40)

    score = (
        expiration * 100 * 0.5 +
        cancel * 100 * 0.3 +
        sat_score * 0.2
    )

    return _clamp(score)


def compute_trend_score(signals: Dict[str, Any]) -> float:
    """
    Tendência operacional.
    """
    trend = signals.get("trend_direction")

    mapping = {
        "improving": 90,
        "stable": 70,
        "worsening": 40,
        "critical": 10,
    }

    return mapping.get(trend, 60)


# =========================
# CLASSIFICAÇÃO
# =========================

def classify(score: float) -> str:
    if score >= 90:
        return "healthy"
    if score >= 75:
        return "attention"
    if score >= 50:
        return "warning"
    if score >= 25:
        return "critical"
    return "collapsed"


def recommended_action(classification: str) -> str:
    return {
        "healthy": "manter_monitoramento",
        "attention": "acompanhar_de_perto",
        "warning": "intervencao_planejada",
        "critical": "inspecao_imediata",
        "collapsed": "bloqueio_operacional_ou_escalonamento",
    }.get(classification, "avaliar_manual")


# =========================
# ALERTAS
# =========================

def generate_alerts(signals: Dict[str, Any]) -> List[str]:
    alerts: List[str] = []

    if _safe(signals.get("expiration_rate")) > 0.15:
        alerts.append("expiracao_acima_do_normal")

    if _safe(signals.get("cancel_rate")) > 0.10:
        alerts.append("cancelamento_acima_do_normal")

    if signals.get("trend_direction") == "worsening":
        alerts.append("tendencia_negativa")

    if signals.get("saturation_level") == "high":
        alerts.append("saturacao_elevada")

    if _safe(signals.get("sample_size")) < 20:
        alerts.append("baixa_confiabilidade_amostral")

    if _safe(signals.get("avg_pickup_minutes")) > 90:
        alerts.append("tempo_medio_excessivo")

    return alerts


# =========================
# ENGINE PRINCIPAL
# =========================

def compute_health(signals: Dict[str, Any]) -> Dict[str, Any]:
    efficiency = compute_efficiency_score(signals)
    reliability = compute_reliability_score(signals)
    risk = compute_risk_score(signals)
    trend = compute_trend_score(signals)

    score = (
        efficiency * WEIGHTS["efficiency"] +
        reliability * WEIGHTS["reliability"] +
        (100 - risk) * WEIGHTS["risk"] +
        trend * WEIGHTS["trend"]
    )

    score = round(_clamp(score), 2)

    classification_value = classify(score)

    return {
        "health_score": score,
        "classification": classification_value,
        "recommended_action": recommended_action(classification_value),
        "components": {
            "efficiency_score": round(efficiency, 2),
            "reliability_score": round(reliability, 2),
            "risk_score": round(risk, 2),
            "trend_score": round(trend, 2),
        },
        "alerts": generate_alerts(signals),
    }