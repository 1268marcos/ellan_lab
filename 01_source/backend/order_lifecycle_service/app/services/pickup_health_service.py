# 01_source/backend/order_lifecycle_service/app/services/pickup_health_service.py
# Deverá ser uma camada acima do executive summary (presente em intenal.py)
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from math import isnan
from typing import Any, Dict, List, Optional

from app.services.pickup_ranking_service import build_pickup_ranking


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
        "slight_improving": 80.0,
        "stable": 70.0,
        "slight_worsening": 55.0,
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

    if signals.get("trend_direction") in {"slight_worsening", "worsening", "critical"}:
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


def compute_trend_from_ranking(
    *,
    db,
    dimension: str,
    start_at: datetime | None,
    end_at: datetime | None,
    region: str | None,
    channel: str | None,
    slot: str | None,
    locker_id: str | None,
    machine_id: str | None,
    operator_id: str | None,
    tenant_id: str | None,
    site_id: str | None,
    days_window: int,
    limit: int,
) -> dict[str | None, dict[str, Any]]:
    now = end_at or datetime.now(timezone.utc)

    current_start = start_at or (now - timedelta(days=days_window))
    previous_end = current_start
    previous_start = previous_end - timedelta(days=days_window)

    current = build_pickup_ranking(
        db,
        category="trend",
        metric="redemption_rate",
        dimension=dimension,
        direction="desc",
        limit=limit,
        start_at=current_start,
        end_at=now,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
    )

    previous = build_pickup_ranking(
        db,
        category="trend",
        metric="redemption_rate",
        dimension=dimension,
        direction="desc",
        limit=limit,
        start_at=previous_start,
        end_at=previous_end,
        region=region,
        channel=channel,
        slot=slot,
        locker_id=locker_id,
        machine_id=machine_id,
        operator_id=operator_id,
        tenant_id=tenant_id,
        site_id=site_id,
    )

    previous_map = {item.dimension_value: item for item in previous.items}
    trend_map: dict[str | None, dict[str, Any]] = {}

    for item in current.items:
        previous_item = previous_map.get(item.dimension_value)

        previous_rate = float(previous_item.redemption_rate) if previous_item else 0.0
        current_rate = float(item.redemption_rate)
        delta = round(current_rate - previous_rate, 3)

        if delta >= 5.0:
            direction = "improving"
        elif delta >= 1.0:
            direction = "slight_improving"
        elif delta > -1.0:
            direction = "stable"
        elif delta > -5.0:
            direction = "slight_worsening"
        else:
            direction = "worsening"

        trend_map[item.dimension_value] = {
            "direction": direction,
            "delta": delta,
            "previous_rate": previous_rate,
            "current_rate": current_rate,
        }

    return trend_map


def compute_historical_baseline_from_ranking(
    *,
    db,
    dimension: str,
    end_at: datetime | None,
    region: str | None,
    channel: str | None,
    slot: str | None,
    locker_id: str | None,
    machine_id: str | None,
    operator_id: str | None,
    tenant_id: str | None,
    site_id: str | None,
    history_windows: int,
    window_days: int,
    limit: int,
) -> dict[str | None, dict[str, Any]]:
    now = end_at or datetime.now(timezone.utc)

    history: dict[str | None, list[float]] = {}

    for idx in range(history_windows):
        window_end = now - timedelta(days=window_days * idx)
        window_start = window_end - timedelta(days=window_days)

        ranking = build_pickup_ranking(
            db,
            category="trend",
            metric="redemption_rate",
            dimension=dimension,
            direction="desc",
            limit=limit,
            start_at=window_start,
            end_at=window_end,
            region=region,
            channel=channel,
            slot=slot,
            locker_id=locker_id,
            machine_id=machine_id,
            operator_id=operator_id,
            tenant_id=tenant_id,
            site_id=site_id,
        )

        for item in ranking.items:
            history.setdefault(item.dimension_value, []).append(float(item.redemption_rate))

    baseline_map: dict[str | None, dict[str, Any]] = {}

    for dimension_value, rates in history.items():
        if not rates:
            continue

        count = len(rates)
        mean_rate = sum(rates) / count

        if count <= 1:
            stddev = 0.0
        else:
            variance = sum((rate - mean_rate) ** 2 for rate in rates) / count
            stddev = variance ** 0.5

        baseline_map[dimension_value] = {
            "history_count": count,
            "mean_rate": round(mean_rate, 3),
            "stddev_rate": round(stddev, 3),
            "min_rate": round(min(rates), 3),
            "max_rate": round(max(rates), 3),
        }

    return baseline_map


def detect_anomalies(
    *,
    signals: Dict[str, Any],
    trend: dict[str, Any] | None,
    baseline: dict[str, Any] | None,
) -> dict[str, Any]:
    alerts: list[str] = []
    prediction_signals: list[str] = []

    abrupt_drop = False
    out_of_pattern = False
    predictive_risk = False

    trend_delta = _safe((trend or {}).get("delta"), 0.0)
    current_rate = _safe((trend or {}).get("current_rate"), 0.0)

    baseline_mean = _safe((baseline or {}).get("mean_rate"), 0.0)
    baseline_stddev = _safe((baseline or {}).get("stddev_rate"), 0.0)
    history_count = int(_safe((baseline or {}).get("history_count"), 0))

    expiration_rate = _safe(signals.get("expiration_rate"), 0.0)
    cancel_rate = _safe(signals.get("cancel_rate"), 0.0)
    avg_pickup_minutes = _safe(signals.get("avg_pickup_minutes"), 0.0)
    saturation_level = str(signals.get("saturation_level") or "").lower()

    if trend_delta <= -8.0:
        abrupt_drop = True
        alerts.append("queda_abruta")

    if history_count >= 3 and baseline_stddev > 0:
        z_score = abs(current_rate - baseline_mean) / baseline_stddev
        if z_score >= 2.0:
            out_of_pattern = True
            alerts.append("fora_do_padrao_historico")
    else:
        z_score = None

    predictive_score = 0

    if trend_delta <= -5.0:
        predictive_score += 2
        prediction_signals.append("queda_recente_relevante")

    if expiration_rate >= 0.15:
        predictive_score += 1
        prediction_signals.append("expiracao_alta")

    if cancel_rate >= 0.10:
        predictive_score += 1
        prediction_signals.append("cancelamento_alto")

    if avg_pickup_minutes >= 90.0:
        predictive_score += 1
        prediction_signals.append("sla_lento")

    if saturation_level == "high":
        predictive_score += 1
        prediction_signals.append("saturacao_alta")

    if out_of_pattern:
        predictive_score += 1
        prediction_signals.append("desvio_historico")

    if predictive_score >= 3:
        predictive_risk = True
        alerts.append("alerta_preditivo")

    return {
        "abrupt_drop": abrupt_drop,
        "out_of_pattern": out_of_pattern,
        "predictive_risk": predictive_risk,
        "alerts": alerts,
        "prediction_signals": prediction_signals,
        "baseline_mean_rate": baseline_mean if history_count > 0 else None,
        "baseline_stddev_rate": baseline_stddev if history_count > 0 else None,
        "z_score": round(z_score, 3) if z_score is not None else None,
        "history_count": history_count,
    }