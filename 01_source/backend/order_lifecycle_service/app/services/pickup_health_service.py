# 01_source/backend/order_lifecycle_service/app/services/pickup_health_service.py
# Deverá ser uma camada acima do executive summary (presente em intenal.py)
from __future__ import annotations

from typing import Any, Dict, List, Optional
from math import isnan


WEIGHTS = {
    "efficiency": 0.40,
    "reliability": 0.20,
    "risk": 0.25,
    "trend": 0.15,
}


ENTITY_DIMENSION_MAP = {
    "locker": "locker_id",
    "machine": "machine_id",
    "site": "site_id",
    "region": "region",
}


def supported_entity_types() -> list[str]:
    return ["locker", "machine", "site", "region", "all"]


def resolve_dimension_for_entity_type(entity_type: str) -> str:
    try:
        return ENTITY_DIMENSION_MAP[entity_type]
    except KeyError as exc:
        raise ValueError(
            f"unsupported entity_type: {entity_type}. "
            f"supported={', '.join(supported_entity_types())}"
        ) from exc


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


def _normalize_percent_to_ratio(value: float | None) -> float:
    raw = _safe(value, 0.0)
    if raw <= 0:
        return 0.0
    if raw > 1:
        return raw / 100.0
    return raw


def _derive_saturation_level(sample_size: int) -> str:
    if sample_size >= 300:
        return "high"
    if sample_size >= 100:
        return "medium"
    return "low"


def _derive_trend_direction_from_rates(
    *,
    redemption_rate: float,
    expiration_rate: float,
    cancellation_rate: float,
) -> str:
    """
    Heurística inicial, estável e auditável.
    Pode ser refinada depois com comparação entre janelas.
    """
    if redemption_rate >= 0.90 and expiration_rate <= 0.05 and cancellation_rate <= 0.03:
        return "improving"

    if redemption_rate < 0.60 or expiration_rate >= 0.20 or cancellation_rate >= 0.10:
        return "worsening"

    return "stable"


def compute_efficiency_score(signals: Dict[str, Any]) -> float:
    success_rate = _safe(signals.get("pickup_success_rate"), 0.0)
    expiration_rate = _safe(signals.get("expiration_rate"), 0.0)
    cancel_rate = _safe(signals.get("cancel_rate"), 0.0)
    avg_minutes = _safe(signals.get("avg_pickup_minutes"), 999.0)

    success_score = success_rate * 100.0
    penalty_exp = expiration_rate * 100.0
    penalty_cancel = cancel_rate * 100.0

    if avg_minutes <= 10:
        time_score = 100.0
    elif avg_minutes >= 120:
        time_score = 0.0
    else:
        time_score = 100.0 - ((avg_minutes - 10.0) / 110.0) * 100.0

    score = (
        success_score * 0.50
        + time_score * 0.30
        + (100.0 - penalty_exp) * 0.10
        + (100.0 - penalty_cancel) * 0.10
    )

    return _clamp(score)


def compute_reliability_score(signals: Dict[str, Any]) -> float:
    sample_size = int(_safe(signals.get("sample_size"), 0))

    if sample_size >= 500:
        return 100.0
    if sample_size >= 200:
        return 90.0
    if sample_size >= 100:
        return 80.0
    if sample_size >= 50:
        return 65.0
    if sample_size >= 20:
        return 45.0
    if sample_size > 0:
        return 25.0
    return 10.0


def compute_risk_score(signals: Dict[str, Any]) -> float:
    expiration = _safe(signals.get("expiration_rate"), 0.0)
    cancel = _safe(signals.get("cancel_rate"), 0.0)
    saturation = signals.get("saturation_level")

    sat_score = {
        "low": 20.0,
        "medium": 50.0,
        "high": 80.0,
    }.get(saturation, 40.0)

    score = (
        expiration * 100.0 * 0.50
        + cancel * 100.0 * 0.30
        + sat_score * 0.20
    )

    return _clamp(score)


def compute_trend_score(signals: Dict[str, Any]) -> float:
    trend = signals.get("trend_direction")
    mapping = {
        "improving": 90.0,
        "stable": 70.0,
        "worsening": 40.0,
        "critical": 10.0,
    }
    return mapping.get(trend, 60.0)


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

    if int(_safe(signals.get("sample_size"))) < 20:
        alerts.append("baixa_confiabilidade_amostral")

    if _safe(signals.get("avg_pickup_minutes")) > 90:
        alerts.append("tempo_medio_excessivo")

    return alerts


def compute_health(signals: Dict[str, Any]) -> Dict[str, Any]:
    efficiency = compute_efficiency_score(signals)
    reliability = compute_reliability_score(signals)
    risk = compute_risk_score(signals)
    trend = compute_trend_score(signals)

    score = (
        efficiency * WEIGHTS["efficiency"]
        + reliability * WEIGHTS["reliability"]
        + (100.0 - risk) * WEIGHTS["risk"]
        + trend * WEIGHTS["trend"]
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


def build_health_signals_from_ranking_item(item: Any) -> Dict[str, Any]:
    redemption_rate = _normalize_percent_to_ratio(getattr(item, "redemption_rate", 0.0))
    expiration_rate = _normalize_percent_to_ratio(getattr(item, "expiration_rate", 0.0))
    cancellation_rate = _normalize_percent_to_ratio(getattr(item, "cancellation_rate", 0.0))
    total_terminal_pickups = int(_safe(getattr(item, "total_terminal_pickups", 0), 0))
    avg_pickup_minutes = _safe(getattr(item, "avg_minutes_ready_to_redeemed", 0.0), 0.0)

    saturation_level = _derive_saturation_level(total_terminal_pickups)
    trend_direction = _derive_trend_direction_from_rates(
        redemption_rate=redemption_rate,
        expiration_rate=expiration_rate,
        cancellation_rate=cancellation_rate,
    )

    return {
        "pickup_success_rate": redemption_rate,
        "expiration_rate": expiration_rate,
        "cancel_rate": cancellation_rate,
        "avg_pickup_minutes": avg_pickup_minutes,
        "trend_direction": trend_direction,
        "saturation_level": saturation_level,
        "sample_size": total_terminal_pickups,
    }


def build_entity_context(
    *,
    entity_type: str,
    entity_id: str | None,
    tenant_id: str | None,
    operator_id: str | None,
    region: str | None,
    site_id: str | None,
    machine_id: str | None,
    locker_id: str | None,
) -> dict[str, Any]:
    row = {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "tenant_id": tenant_id,
        "operator_id": operator_id,
        "region": region,
        "site_id": site_id,
        "machine_id": machine_id,
        "locker_id": locker_id,
    }

    if entity_type == "locker":
        row["locker_id"] = entity_id
    elif entity_type == "machine":
        row["machine_id"] = entity_id
    elif entity_type == "site":
        row["site_id"] = entity_id
    elif entity_type == "region":
        row["region"] = entity_id

    return row