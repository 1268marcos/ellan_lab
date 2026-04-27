from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ops_action_audit import OpsActionAudit
from app.models.reconciliation_pending import ReconciliationPending


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_aware_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _compute_action_kpis(*, db: Session, window_start: datetime, window_end: datetime) -> dict:
    total_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < window_end,
        )
        .scalar()
        or 0
    )
    success_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < window_end,
            OpsActionAudit.result == "SUCCESS",
        )
        .scalar()
        or 0
    )
    error_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < window_end,
            OpsActionAudit.result == "ERROR",
        )
        .scalar()
        or 0
    )
    error_rate = (float(error_actions) / float(total_actions)) if total_actions > 0 else 0.0
    recon_actions = int(
        db.query(func.count(OpsActionAudit.id))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < window_end,
            OpsActionAudit.action.in_(
                [
                    "OPS_RECONCILE_ORDER",
                    "OPS_RECON_PENDING_RUN_ONCE",
                    "SYSTEM_RECON_RETRY_PROCESS",
                ]
            ),
        )
        .scalar()
        or 0
    )
    return {
        "total_ops_actions": total_actions,
        "success_actions": success_actions,
        "error_actions": error_actions,
        "error_rate": round(error_rate, 4),
        "reconciliation_actions": recon_actions,
    }


def _error_severity_by_rate(error_rate: float) -> str:
    if error_rate > 0.50:
        return "CRITICAL"
    if error_rate >= 0.20:
        return "HIGH"
    if error_rate >= 0.05:
        return "MEDIUM"
    return "LOW"


def _extract_latency_ms(details: dict | None) -> float | None:
    if not isinstance(details, dict):
        return None
    candidates = [
        details.get("duration_ms"),
        details.get("latency_ms"),
        details.get("elapsed_ms"),
        details.get("processing_ms"),
        details.get("execution_ms"),
    ]
    metrics = details.get("metrics")
    if isinstance(metrics, dict):
        candidates.extend(
            [
                metrics.get("duration_ms"),
                metrics.get("latency_ms"),
                metrics.get("elapsed_ms"),
                metrics.get("processing_ms"),
                metrics.get("execution_ms"),
            ]
        )
    for value in candidates:
        if value is None:
            continue
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            continue
        if numeric >= 0:
            return numeric
    return None


def _compute_latency_percentiles(
    *, db: Session, window_start: datetime, window_end: datetime
) -> tuple[float, float, int]:
    rows = (
        db.query(OpsActionAudit.details_json)
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < window_end,
        )
        .all()
    )
    latency_values: list[float] = []
    for row in rows:
        details = row[0] if isinstance(row, tuple) else row
        latency = _extract_latency_ms(details if isinstance(details, dict) else {})
        if latency is not None:
            latency_values.append(latency)
    if not latency_values:
        return 0.0, 0.0, 0
    latency_values.sort()
    count = len(latency_values)

    def _percentile(sorted_values: list[float], percentile: float) -> float:
        if not sorted_values:
            return 0.0
        if len(sorted_values) == 1:
            return float(sorted_values[0])
        rank = (len(sorted_values) - 1) * percentile
        lower = int(rank)
        upper = min(lower + 1, len(sorted_values) - 1)
        weight = rank - lower
        return float(sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * weight)

    p50 = round(_percentile(latency_values, 0.50), 2)
    p95 = round(_percentile(latency_values, 0.95), 2)
    return p50, p95, count


def _build_trend_series(
    *,
    db: Session,
    window_start: datetime,
    window_end: datetime,
    lookback_hours: int,
) -> dict:
    bucket_minutes = 60 if lookback_hours <= 24 else 180 if lookback_hours <= 72 else 360
    bucket_delta = timedelta(minutes=bucket_minutes)
    total_buckets = max(int((window_end - window_start) / bucket_delta), 1)

    buckets: list[dict] = []
    cursor = window_start
    for _ in range(total_buckets):
        bucket_to = min(cursor + bucket_delta, window_end)
        buckets.append(
            {
                "from": cursor,
                "to": bucket_to,
                "total": 0,
                "errors": 0,
                "latencies": [],
            }
        )
        cursor = bucket_to
        if cursor >= window_end:
            break

    rows = (
        db.query(OpsActionAudit.created_at, OpsActionAudit.result, OpsActionAudit.details_json)
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < window_end,
        )
        .all()
    )
    for created_at, result, details_json in rows:
        if created_at is None:
            continue
        created_at_utc = _as_aware_utc(created_at)
        if created_at_utc is None:
            continue
        offset_seconds = (created_at_utc - window_start).total_seconds()
        if offset_seconds < 0:
            continue
        bucket_index = int(offset_seconds // bucket_delta.total_seconds())
        bucket_index = min(bucket_index, len(buckets) - 1)
        bucket = buckets[bucket_index]
        bucket["total"] += 1
        if str(result or "").upper() == "ERROR":
            bucket["errors"] += 1
        latency = _extract_latency_ms(details_json if isinstance(details_json, dict) else {})
        if latency is not None:
            bucket["latencies"].append(latency)

    points: list[dict] = []
    for bucket in buckets:
        latencies = sorted(bucket["latencies"])
        p95 = 0.0
        if latencies:
            rank = int(round((len(latencies) - 1) * 0.95))
            p95 = round(float(latencies[max(min(rank, len(latencies) - 1), 0)]), 2)
        total = int(bucket["total"])
        errors = int(bucket["errors"])
        points.append(
            {
                "from": bucket["from"].isoformat(),
                "to": bucket["to"].isoformat(),
                "total_ops_actions": total,
                "error_rate": round(float(errors) / float(total), 4) if total > 0 else 0.0,
                "latency_p95_ms": p95,
            }
        )

    return {
        "bucket_minutes": bucket_minutes,
        "points": points,
    }


def _build_predictive_alerts_from_trends(
    trends: dict,
    *,
    predictive_min_volume: int = 5,
    predictive_error_min_rate: float = 0.05,
    predictive_error_accel_factor: float = 1.5,
    predictive_latency_min_ms: float = 100.0,
    predictive_latency_accel_factor: float = 1.4,
) -> list[dict]:
    points = trends.get("points") if isinstance(trends, dict) else None
    if not isinstance(points, list) or len(points) < 4:
        return []

    predictive_alerts: list[dict] = []
    last_points = points[-4:]
    error_series = [float(p.get("error_rate") or 0.0) for p in last_points]
    latency_series = [float(p.get("latency_p95_ms") or 0.0) for p in last_points]
    volume_series = [int(p.get("total_ops_actions") or 0) for p in last_points]
    min_recent_volume = min(volume_series[-3:])
    min_volume = max(int(predictive_min_volume or 5), 1)
    if min_recent_volume <= 0:
        return []
    data_quality_flag = "LOW_VOLUME" if min_recent_volume < 10 else "MEDIUM_VOLUME" if min_recent_volume < 25 else "OK"

    # Heurística 1: degradação de erro (subida sustentada + aceleração vs histórico curto)
    if min_recent_volume >= min_volume:
        increasing_error = error_series[-1] > error_series[-2] > error_series[-3]
        baseline_error = sum(error_series[:-1]) / max(len(error_series[:-1]), 1)
        latest_error = error_series[-1]
        if increasing_error and latest_error >= predictive_error_min_rate and latest_error >= (
            baseline_error * predictive_error_accel_factor if baseline_error > 0 else predictive_error_min_rate
        ):
            confidence_level = "LOW" if data_quality_flag == "LOW_VOLUME" else "MEDIUM" if data_quality_flag == "MEDIUM_VOLUME" else "HIGH"
            predictive_alerts.append(
                {
                    "severity": "HIGH" if latest_error >= 0.20 else "MEDIUM",
                    "code": "OPS_PREDICTIVE_ERROR_DEGRADATION",
                    "message": "Sinal preditivo de degradação: taxa de erro em aceleração nas últimas janelas.",
                    "value": round(latest_error, 4),
                    "threshold": round(float(predictive_error_min_rate), 4),
                    "impact": "Sem mitigação, há risco de aumento de falhas operacionais na próxima janela.",
                    "investigate_hint": "Verificar mudanças recentes, integrações com locker e picos de timeout.",
                    "mitigation_hint": "Aplicar mitigação preventiva (retry/backoff, circuit breaker e contenção de carga).",
                    "investigate_url": "/ops/audit?action=OPS_METRICS_VIEW&limit=100",
                    "confidence_level": confidence_level,
                    "data_quality_flag": data_quality_flag,
                }
            )

    # Heurística 2: degradação de latência p95 (subida sustentada + salto relevante)
    if min_recent_volume >= min_volume:
        increasing_latency = latency_series[-1] > latency_series[-2] > latency_series[-3]
        baseline_latency = sum(latency_series[:-1]) / max(len(latency_series[:-1]), 1)
        latest_latency = latency_series[-1]
        if increasing_latency and latest_latency >= predictive_latency_min_ms and latest_latency >= (
            baseline_latency * predictive_latency_accel_factor if baseline_latency > 0 else predictive_latency_min_ms
        ):
            confidence_level = "LOW" if data_quality_flag == "LOW_VOLUME" else "MEDIUM" if data_quality_flag == "MEDIUM_VOLUME" else "HIGH"
            predictive_alerts.append(
                {
                    "severity": "MEDIUM",
                    "code": "OPS_PREDICTIVE_LATENCY_DEGRADATION",
                    "message": "Sinal preditivo de degradação: latência p95 em tendência de alta.",
                    "value": round(latest_latency, 2),
                    "threshold": round(float(predictive_latency_min_ms), 2),
                    "impact": "Sem ação preventiva, a latência pode pressionar SLA e aumentar erros por timeout.",
                    "investigate_hint": "Checar filas, workers, lock de processamento e latência de integração externa.",
                    "mitigation_hint": "Escalonar capacidade e atacar gargalos antes de virar incidente.",
                    "investigate_url": "/ops/audit?action=OPS_METRICS_VIEW&limit=100",
                    "confidence_level": confidence_level,
                    "data_quality_flag": data_quality_flag,
                }
            )

    return predictive_alerts


def _evaluate_predictive_monitoring(
    trends: dict,
    *,
    predictive_min_volume: int = 5,
    predictive_error_min_rate: float = 0.05,
    predictive_latency_min_ms: float = 100.0,
) -> dict:
    points = trends.get("points") if isinstance(trends, dict) else None
    if not isinstance(points, list) or len(points) < 6:
        return {
            "window_days": 7,
            "emitted_alerts": 0,
            "confirmed_alerts": 0,
            "false_positive_alerts": 0,
            "false_positive_rate": 0.0,
        }

    emitted = 0
    confirmed = 0
    false_positive = 0
    for idx in range(2, len(points) - 2):
        p_prev2 = points[idx - 2]
        p_prev1 = points[idx - 1]
        p_curr = points[idx]
        p_next1 = points[idx + 1]
        p_next2 = points[idx + 2]

        error_prev2 = float(p_prev2.get("error_rate") or 0.0)
        error_prev1 = float(p_prev1.get("error_rate") or 0.0)
        error_curr = float(p_curr.get("error_rate") or 0.0)
        latency_prev2 = float(p_prev2.get("latency_p95_ms") or 0.0)
        latency_prev1 = float(p_prev1.get("latency_p95_ms") or 0.0)
        latency_curr = float(p_curr.get("latency_p95_ms") or 0.0)
        volume_prev2 = int(p_prev2.get("total_ops_actions") or 0)
        volume_prev1 = int(p_prev1.get("total_ops_actions") or 0)
        volume_curr = int(p_curr.get("total_ops_actions") or 0)
        min_recent_volume = min(volume_prev2, volume_prev1, volume_curr)
        if min_recent_volume < max(int(predictive_min_volume or 5), 1):
            continue

        emits_error = error_curr > error_prev1 > error_prev2 and error_curr >= float(predictive_error_min_rate or 0.05)
        emits_latency = latency_curr > latency_prev1 > latency_prev2 and latency_curr >= float(predictive_latency_min_ms or 100.0)
        if not (emits_error or emits_latency):
            continue

        emitted += 1
        next_error1 = float(p_next1.get("error_rate") or 0.0)
        next_error2 = float(p_next2.get("error_rate") or 0.0)
        next_latency1 = float(p_next1.get("latency_p95_ms") or 0.0)
        next_latency2 = float(p_next2.get("latency_p95_ms") or 0.0)

        confirmed_error = emits_error and max(next_error1, next_error2) >= max(error_curr, 0.20)
        confirmed_latency = emits_latency and max(next_latency1, next_latency2) >= (latency_curr * 1.10)
        if confirmed_error or confirmed_latency:
            confirmed += 1
        else:
            false_positive += 1

    false_positive_rate = round(float(false_positive) / float(emitted), 4) if emitted > 0 else 0.0
    recommendation = "KEEP"
    if emitted >= 3 and false_positive_rate >= 0.50:
        recommendation = "INCREASE_SENSITIVITY_GUARDRAILS"
    elif emitted >= 3 and false_positive_rate <= 0.15 and confirmed >= 2:
        recommendation = "CAN_INCREASE_SENSITIVITY"
    return {
        "window_days": 7,
        "emitted_alerts": int(emitted),
        "confirmed_alerts": int(confirmed),
        "false_positive_alerts": int(false_positive),
        "false_positive_rate": false_positive_rate,
        "recommendation": recommendation,
    }


def _classify_error_type(message: str) -> str:
    normalized = str(message or "").strip().lower()
    if not normalized:
        return "OUTROS"

    timeout_keywords = ["timeout", "timed out", "tempo esgotado", "deadline exceeded"]
    validation_keywords = ["valid", "inval", "schema", "required", "obrigat", "constraint", "payload"]
    integration_keywords = ["gateway", "http", "api", "upstream", "locker", "integration", "integracao", "webhook"]
    infra_keywords = ["database", "db ", "redis", "connection refused", "network", "dns", "unavailable", "infra", "memory"]

    if any(token in normalized for token in timeout_keywords):
        return "TIMEOUT"
    if any(token in normalized for token in validation_keywords):
        return "VALIDACAO"
    if any(token in normalized for token in integration_keywords):
        return "INTEGRACAO"
    if any(token in normalized for token in infra_keywords):
        return "INFRA"
    return "OUTROS"


def _build_predictive_snapshots_history(*, db: Session, limit: int = 8) -> list[dict]:
    rows = (
        db.query(OpsActionAudit)
        .filter(OpsActionAudit.action == "OPS_PREDICTIVE_WEEKLY_SNAPSHOT")
        .order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .limit(max(int(limit or 8), 1))
        .all()
    )
    snapshots: list[dict] = []
    for row in rows:
        details = row.details_json if isinstance(row.details_json, dict) else {}
        thresholds = details.get("thresholds") if isinstance(details.get("thresholds"), dict) else {}
        monitoring = details.get("monitoring") if isinstance(details.get("monitoring"), dict) else {}
        snapshots.append(
            {
                "id": row.id,
                "created_at": _as_aware_utc(row.created_at).isoformat() if _as_aware_utc(row.created_at) else None,
                "environment": str(details.get("environment") or "unknown"),
                "decision": str(details.get("decision") or "KEEP"),
                "rationale": str(details.get("rationale")) if details.get("rationale") else None,
                "false_positive_rate": float(monitoring.get("false_positive_rate") or 0.0),
                "emitted_alerts": int(monitoring.get("emitted_alerts") or 0),
                "confirmed_alerts": int(monitoring.get("confirmed_alerts") or 0),
                "false_positive_alerts": int(monitoring.get("false_positive_alerts") or 0),
                "thresholds": {
                    "predictive_min_volume": int(thresholds.get("predictive_min_volume") or 0),
                    "predictive_error_min_rate": float(thresholds.get("predictive_error_min_rate") or 0.0),
                    "predictive_error_accel_factor": float(thresholds.get("predictive_error_accel_factor") or 0.0),
                    "predictive_latency_min_ms": float(thresholds.get("predictive_latency_min_ms") or 0.0),
                    "predictive_latency_accel_factor": float(thresholds.get("predictive_latency_accel_factor") or 0.0),
                },
            }
        )
    return snapshots


def build_ops_error_investigation_report(
    *,
    db: Session,
    lookback_hours: int = 24,
    top_causes_limit: int = 3,
    evidence_per_cause_limit: int = 3,
) -> dict:
    now = _utc_now()
    lookback = max(int(lookback_hours or 24), 1)
    window_start = now - timedelta(hours=lookback)

    rows = (
        db.query(OpsActionAudit)
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < now,
            OpsActionAudit.result == "ERROR",
        )
        .order_by(OpsActionAudit.created_at.desc(), OpsActionAudit.id.desc())
        .all()
    )
    total_errors = len(rows)
    category_counts: dict[str, int] = {
        "TIMEOUT": 0,
        "VALIDACAO": 0,
        "INTEGRACAO": 0,
        "INFRA": 0,
        "OUTROS": 0,
    }
    cause_counts: dict[tuple[str, str], int] = {}
    cause_evidence: dict[tuple[str, str], list[dict]] = {}

    for row in rows:
        message = str(row.error_message or "Erro não classificado").strip() or "Erro não classificado"
        category = _classify_error_type(message)
        category_counts[category] = int(category_counts.get(category, 0)) + 1
        cause_key = (message, category)
        cause_counts[cause_key] = int(cause_counts.get(cause_key, 0)) + 1
        if cause_key not in cause_evidence:
            cause_evidence[cause_key] = []
        if len(cause_evidence[cause_key]) < max(int(evidence_per_cause_limit or 3), 1):
            created = _as_aware_utc(row.created_at)
            cause_evidence[cause_key].append(
                {
                    "audit_id": row.id,
                    "created_at": created.isoformat() if created else None,
                    "correlation_id": str(row.correlation_id or ""),
                    "action": str(row.action or ""),
                    "message": message,
                    "category": category,
                }
            )

    categories = []
    for category in ["TIMEOUT", "VALIDACAO", "INTEGRACAO", "INFRA", "OUTROS"]:
        count = int(category_counts.get(category, 0))
        if count <= 0:
            continue
        categories.append(
            {
                "category": category,
                "count": count,
                "percentage": round((float(count) / float(total_errors)) * 100.0, 2) if total_errors > 0 else 0.0,
            }
        )

    sorted_causes = sorted(cause_counts.items(), key=lambda item: item[1], reverse=True)[: max(int(top_causes_limit or 3), 1)]
    top_causes = []
    for (message, category), count in sorted_causes:
        top_causes.append(
            {
                "message": message,
                "category": category,
                "count": int(count),
                "percentage": round((float(count) / float(total_errors)) * 100.0, 2) if total_errors > 0 else 0.0,
                "evidence": cause_evidence.get((message, category), []),
            }
        )

    return {
        "window": {
            "lookback_hours": lookback,
            "from": window_start.isoformat(),
            "to": now.isoformat(),
        },
        "total_error_actions": int(total_errors),
        "categories": categories,
        "top_causes": top_causes,
    }


def build_ops_metrics(
    *,
    db: Session,
    lookback_hours: int = 24,
    pending_open_threshold: int = 10,
    error_rate_threshold: float = 0.25,
    failed_final_threshold: int = 1,
    predictive_min_volume: int = 5,
    predictive_error_min_rate: float = 0.05,
    predictive_error_accel_factor: float = 1.5,
    predictive_latency_min_ms: float = 100.0,
    predictive_latency_accel_factor: float = 1.4,
) -> dict:
    now = _utc_now()
    lookback = max(int(lookback_hours or 24), 1)
    window_start = now - timedelta(hours=lookback)
    previous_window_start = window_start - timedelta(hours=lookback)

    current_action_kpis = _compute_action_kpis(db=db, window_start=window_start, window_end=now)
    previous_action_kpis = _compute_action_kpis(db=db, window_start=previous_window_start, window_end=window_start)
    current_p50_ms, current_p95_ms, current_latency_samples = _compute_latency_percentiles(
        db=db,
        window_start=window_start,
        window_end=now,
    )
    previous_p50_ms, previous_p95_ms, previous_latency_samples = _compute_latency_percentiles(
        db=db,
        window_start=previous_window_start,
        window_end=window_start,
    )
    trends = _build_trend_series(
        db=db,
        window_start=window_start,
        window_end=now,
        lookback_hours=lookback,
    )
    predictive_monitoring = _evaluate_predictive_monitoring(
        trends,
        predictive_min_volume=predictive_min_volume,
        predictive_error_min_rate=predictive_error_min_rate,
        predictive_latency_min_ms=predictive_latency_min_ms,
    )

    total_actions = int(current_action_kpis["total_ops_actions"])
    success_actions = int(current_action_kpis["success_actions"])
    error_actions = int(current_action_kpis["error_actions"])
    error_rate = float(current_action_kpis["error_rate"])
    recon_actions = int(current_action_kpis["reconciliation_actions"])

    pending_open_rows = (
        db.query(ReconciliationPending)
        .filter(ReconciliationPending.status.in_(["PENDING", "FAILED", "PROCESSING"]))
        .all()
    )
    pending_open_count = len(pending_open_rows)
    pending_failed_final_count = int(
        db.query(func.count(ReconciliationPending.id))
        .filter(ReconciliationPending.status == "FAILED_FINAL")
        .scalar()
        or 0
    )
    pending_due_retry_count = int(
        db.query(func.count(ReconciliationPending.id))
        .filter(
            ReconciliationPending.status == "FAILED",
            ReconciliationPending.next_retry_at.is_not(None),
            ReconciliationPending.next_retry_at <= now,
        )
        .scalar()
        or 0
    )
    stale_cutoff = now - timedelta(minutes=5)
    pending_processing_stale_count = int(
        db.query(func.count(ReconciliationPending.id))
        .filter(
            ReconciliationPending.status == "PROCESSING",
            ReconciliationPending.processing_started_at.is_not(None),
            ReconciliationPending.processing_started_at <= stale_cutoff,
        )
        .scalar()
        or 0
    )

    avg_open_pending_age_min = 0.0
    pending_age_buckets = {
        "0_1h": 0,
        "1_4h": 0,
        "4_24h": 0,
        "24h_plus": 0,
    }
    if pending_open_rows:
        ages = []
        for row in pending_open_rows:
            created_at = _as_aware_utc(row.created_at)
            if not created_at:
                continue
            age_minutes = max((now - created_at).total_seconds() / 60.0, 0.0)
            ages.append(age_minutes)
            if age_minutes < 60:
                pending_age_buckets["0_1h"] += 1
            elif age_minutes < 240:
                pending_age_buckets["1_4h"] += 1
            elif age_minutes < 1440:
                pending_age_buckets["4_24h"] += 1
            else:
                pending_age_buckets["24h_plus"] += 1
        if ages:
            avg_open_pending_age_min = round(sum(ages) / len(ages), 2)

    completed_rows = (
        db.query(ReconciliationPending)
        .filter(
            ReconciliationPending.completed_at.is_not(None),
            ReconciliationPending.completed_at >= window_start,
            ReconciliationPending.completed_at < now,
            ReconciliationPending.status.in_(["DONE", "FAILED_FINAL"]),
        )
        .all()
    )
    done_count = 0
    failed_final_count_window = 0
    reconciliation_durations_min: list[float] = []
    for row in completed_rows:
        status = str(row.status or "").upper()
        if status == "DONE":
            done_count += 1
        elif status == "FAILED_FINAL":
            failed_final_count_window += 1
        created_at = _as_aware_utc(row.created_at)
        completed_at = _as_aware_utc(row.completed_at)
        if created_at and completed_at and completed_at >= created_at:
            reconciliation_durations_min.append((completed_at - created_at).total_seconds() / 60.0)

    reconciliation_total_completed = done_count + failed_final_count_window
    auto_reconciliation_rate = (
        round(float(done_count) / float(reconciliation_total_completed), 4)
        if reconciliation_total_completed > 0
        else 0.0
    )
    avg_reconciliation_time_min = (
        round(sum(reconciliation_durations_min) / len(reconciliation_durations_min), 2)
        if reconciliation_durations_min
        else 0.0
    )

    alerts: list[dict] = []
    if pending_open_count >= int(pending_open_threshold or 10):
        alerts.append(
            {
                "severity": "MEDIUM",
                "code": "PENDING_BACKLOG_HIGH",
                "message": "Backlog de pendências de reconciliação acima do threshold.",
                "value": pending_open_count,
                "threshold": int(pending_open_threshold or 10),
                "impact": "Fila de pendências elevada, com risco de aumento de tempo de resolução.",
                "investigate_hint": "Abrir lista de reconciliação pendente e priorizar itens mais antigos.",
                "mitigation_hint": "Executar lote manual de retry e atacar causa dominante.",
                "investigate_url": "/ops/reconciliation",
            }
        )
    if total_actions >= 5 and error_rate >= float(error_rate_threshold or 0.25):
        severity = _error_severity_by_rate(error_rate)
        alerts.append(
            {
                "severity": severity,
                "code": "OPS_ERROR_RATE_HIGH",
                "message": (
                    f"Taxa de erro em {error_rate * 100:.1f}% "
                    f"({error_actions}/{total_actions} falhas) acima do threshold da janela."
                ),
                "value": round(error_rate, 4),
                "threshold": float(error_rate_threshold or 0.25),
                "impact": f"{error_actions} de {total_actions} ações falharam na janela atual.",
                "investigate_hint": "Verificar logs de timeout/conectividade e falhas de integração com lockers.",
                "mitigation_hint": "Aplicar retry com backoff e revisar thresholds/circuit breakers.",
                "investigate_url": "/ops/audit?action=OPS_METRICS_VIEW&result=ERROR&limit=50",
            }
        )
    if pending_failed_final_count >= int(failed_final_threshold or 1):
        alerts.append(
            {
                "severity": "HIGH",
                "code": "PENDING_FAILED_FINAL",
                "message": "Existem pendências em estado final de falha (FAILED_FINAL).",
                "value": pending_failed_final_count,
                "threshold": int(failed_final_threshold or 1),
                "impact": "Há itens que não serão processados automaticamente sem intervenção.",
                "investigate_hint": "Abrir lista de pendências FAILED_FINAL e validar causa raiz por item.",
                "mitigation_hint": "Executar runbook de reconciliação manual e corrigir erro recorrente.",
                "investigate_url": "/ops/reconciliation?status=FAILED_FINAL",
            }
        )
    if pending_processing_stale_count > 0:
        alerts.append(
            {
                "severity": "MEDIUM",
                "code": "PENDING_PROCESSING_STALE",
                "message": "Existem pendências presas em PROCESSING há mais de 5 minutos.",
                "value": pending_processing_stale_count,
                "threshold": 0,
                "impact": "Fluxo de reconciliação pode estar travado para parte dos itens.",
                "investigate_hint": "Correlacionar com workers e jobs de retry na mesma janela.",
                "mitigation_hint": "Reiniciar processamento afetado e validar lock/concorrência.",
                "investigate_url": "/ops/reconciliation?status=PROCESSING",
            }
        )
    alerts.extend(
        _build_predictive_alerts_from_trends(
            trends,
            predictive_min_volume=predictive_min_volume,
            predictive_error_min_rate=predictive_error_min_rate,
            predictive_error_accel_factor=predictive_error_accel_factor,
            predictive_latency_min_ms=predictive_latency_min_ms,
            predictive_latency_accel_factor=predictive_latency_accel_factor,
        )
    )

    top_error_rows = (
        db.query(OpsActionAudit.error_message, func.count(OpsActionAudit.id).label("total"))
        .filter(
            OpsActionAudit.created_at >= window_start,
            OpsActionAudit.created_at < now,
            OpsActionAudit.result == "ERROR",
        )
        .group_by(OpsActionAudit.error_message)
        .order_by(func.count(OpsActionAudit.id).desc())
        .limit(5)
        .all()
    )
    top_errors = []
    category_counter = {
        "TIMEOUT": 0,
        "VALIDACAO": 0,
        "INTEGRACAO": 0,
        "INFRA": 0,
        "OUTROS": 0,
    }
    for error_message, total in top_error_rows:
        count = int(total or 0)
        message = str(error_message or "Erro não classificado").strip() or "Erro não classificado"
        percentage = round((float(count) / float(error_actions)) * 100.0, 2) if error_actions > 0 else 0.0
        category = _classify_error_type(message)
        category_counter[category] = int(category_counter.get(category, 0)) + count
        top_errors.append(
            {
                "message": message,
                "count": count,
                "percentage": percentage,
                "category": category,
            }
        )

    category_items = []
    categorized_actions = 0
    for category in ["TIMEOUT", "VALIDACAO", "INTEGRACAO", "INFRA", "OUTROS"]:
        count = int(category_counter.get(category, 0))
        if count <= 0:
            continue
        categorized_actions += count
        category_items.append(
            {
                "category": category,
                "count": count,
                "percentage": round((float(count) / float(error_actions)) * 100.0, 2) if error_actions > 0 else 0.0,
            }
        )

    return {
        "window": {
            "lookback_hours": lookback,
            "from": window_start.isoformat(),
            "to": now.isoformat(),
        },
        "kpis": {
            "total_ops_actions": total_actions,
            "success_actions": success_actions,
            "error_actions": error_actions,
            "error_rate": round(error_rate, 4),
            "reconciliation_actions": recon_actions,
            "latency_p50_ms": current_p50_ms,
            "latency_p95_ms": current_p95_ms,
            "latency_samples": current_latency_samples,
            "pending_open_count": pending_open_count,
            "pending_age_0_1h": int(pending_age_buckets["0_1h"]),
            "pending_age_1_4h": int(pending_age_buckets["1_4h"]),
            "pending_age_4_24h": int(pending_age_buckets["4_24h"]),
            "pending_age_24h_plus": int(pending_age_buckets["24h_plus"]),
            "pending_due_retry_count": pending_due_retry_count,
            "pending_processing_stale_count": pending_processing_stale_count,
            "pending_failed_final_count": pending_failed_final_count,
            "avg_open_pending_age_min": avg_open_pending_age_min,
            "reconciliation_auto_rate": auto_reconciliation_rate,
            "avg_reconciliation_time_min": avg_reconciliation_time_min,
            "reconciliation_total_completed": int(reconciliation_total_completed),
            "reconciliation_done_count": int(done_count),
            "reconciliation_failed_final_count_window": int(failed_final_count_window),
            "unresolved_exceptions_count": int(pending_failed_final_count),
        },
        "alerts": alerts,
        "comparison": {
            "window": {
                "lookback_hours": lookback,
                "from": previous_window_start.isoformat(),
                "to": window_start.isoformat(),
            },
            "kpis": {
                **previous_action_kpis,
                "latency_p50_ms": previous_p50_ms,
                "latency_p95_ms": previous_p95_ms,
                "latency_samples": previous_latency_samples,
            },
        },
        "trends": trends,
        "predictive_monitoring": predictive_monitoring,
        "predictive_thresholds": {
            "predictive_min_volume": int(max(int(predictive_min_volume or 5), 1)),
            "predictive_error_min_rate": round(float(predictive_error_min_rate or 0.05), 4),
            "predictive_error_accel_factor": round(float(predictive_error_accel_factor or 1.5), 3),
            "predictive_latency_min_ms": round(float(predictive_latency_min_ms or 100.0), 2),
            "predictive_latency_accel_factor": round(float(predictive_latency_accel_factor or 1.4), 3),
        },
        "top_errors": top_errors,
        "error_classification": {
            "total_error_actions": int(error_actions),
            "categorized_actions": int(categorized_actions),
            "categories": category_items,
        },
        "predictive_snapshots": _build_predictive_snapshots_history(db=db, limit=8),
    }
