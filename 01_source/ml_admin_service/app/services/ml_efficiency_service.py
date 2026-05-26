from __future__ import annotations

import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ml_efficiency import MlFeatureFreshnessBreach, MlInferenceUsageDaily, MlOpsRecommendation
from app.models.ml_ops import MlDriftReport, MlFeatureDefinition, MlTrainingRun
from app.models.ml_readiness import MlIntegrationReadinessSnapshot
from app.services.crypto_util import new_id

USAGE_SEEDS = [
    ("LOCKER_HEALTH", "INPOST"),
    ("LOCKER_HEALTH", "DHL"),
    ("OCCUPANCY_DEMAND", "MAGALU"),
    ("PARTNER_CHURN", "MERCADOLIVRE"),
    ("PICKUP_FRAUD", "AMAZON_BR"),
]

RECOMMENDATION_TEMPLATES = [
    ("RETRAIN_STALE_MODEL", "MODEL", "HIGH", "Retreinar modelo com drift WARNING", "Promover nova versão após training run OK."),
    ("REDUCE_INFERENCE_COST", "COST", "MEDIUM", "Otimizar batch inference", "Agrupar predições por rede locker fora do pico."),
    ("FIX_FEATURE_LAG", "DATA", "HIGH", "Corrigir lag de features", "Sincronizar ml_features_daily com mart locker_pnl."),
    ("ENABLE_READINESS_BLOCKER", "INTEGRATION", "MEDIUM", "Resolver blockers de readiness", "Completar webhooks e API keys por player Tier-1."),
]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def seed_efficiency(db: Session) -> dict[str, int]:
    counts = {"usage": 0, "breaches": 0, "recommendations": 0}
    today = date.today()
    for uc, player in USAGE_SEEDS:
        key = (today, uc, player)
        exists = (
            db.query(MlInferenceUsageDaily)
            .filter(
                MlInferenceUsageDaily.usage_date == today,
                MlInferenceUsageDaily.use_case_code == uc,
                MlInferenceUsageDaily.network_player_code == player,
            )
            .first()
        )
        if not exists:
            db.add(
                MlInferenceUsageDaily(
                    id=new_id(),
                    usage_date=today,
                    use_case_code=uc,
                    network_player_code=player,
                    request_count=random.randint(500, 8000),
                    p95_latency_ms=random.randint(40, 220),
                    error_rate_pct=round(random.uniform(0.1, 2.5), 3),
                    estimated_cost_usd=round(random.uniform(5, 80), 2),
                )
            )
            counts["usage"] += 1
    for feat in db.query(MlFeatureDefinition).limit(3).all():
        if (
            db.query(MlFeatureFreshnessBreach)
            .filter(MlFeatureFreshnessBreach.feature_name == feat.feature_name, MlFeatureFreshnessBreach.status == "OPEN")
            .first()
        ):
            continue
        lag = random.uniform(26, 48)
        db.add(
            MlFeatureFreshnessBreach(
                id=new_id(),
                feature_name=feat.feature_name,
                source_table=feat.source_table or "ml_features_daily",
                sla_hours=int(feat.freshness_hours or 24),
                lag_hours=round(lag, 2),
                severity="CRITICAL" if lag > 40 else "WARNING",
                summary=f"Feature {feat.feature_name} com lag {lag:.1f}h > SLA {feat.freshness_hours or 24}h",
            )
        )
        counts["breaches"] += 1
    for code, cat, pri, title, hint in RECOMMENDATION_TEMPLATES:
        if db.query(MlOpsRecommendation).filter(MlOpsRecommendation.recommendation_code == code).first():
            continue
        db.add(
            MlOpsRecommendation(
                id=new_id(),
                recommendation_code=code,
                category=cat,
                priority=pri,
                title=title,
                action_hint=hint,
                impact_score=random.uniform(60, 95),
            )
        )
        counts["recommendations"] += 1
    db.commit()
    return counts


def list_inference_usage(db: Session, days: int = 7) -> list[MlInferenceUsageDaily]:
    since = date.today() - timedelta(days=days)
    return (
        db.query(MlInferenceUsageDaily)
        .filter(MlInferenceUsageDaily.usage_date >= since)
        .order_by(MlInferenceUsageDaily.usage_date.desc(), MlInferenceUsageDaily.use_case_code)
        .all()
    )


def list_freshness_breaches(db: Session, status: str | None = None) -> list[MlFeatureFreshnessBreach]:
    q = db.query(MlFeatureFreshnessBreach).order_by(MlFeatureFreshnessBreach.detected_at.desc())
    if status:
        q = q.filter(MlFeatureFreshnessBreach.status == status)
    return q.limit(100).all()


def list_recommendations(db: Session, status: str | None = None) -> list[MlOpsRecommendation]:
    q = db.query(MlOpsRecommendation).order_by(MlOpsRecommendation.impact_score.desc())
    if status:
        q = q.filter(MlOpsRecommendation.status == status)
    return q.limit(100).all()


def generate_recommendations(db: Session) -> dict:
    created = 0
    critical_drift = (
        db.query(MlDriftReport).filter(MlDriftReport.status == "CRITICAL").order_by(MlDriftReport.created_at.desc()).limit(3).all()
    )
    for d in critical_drift:
        code = f"DRIFT_{d.id[:8]}"
        if db.query(MlOpsRecommendation).filter(MlOpsRecommendation.recommendation_code == code).first():
            continue
        db.add(
            MlOpsRecommendation(
                id=new_id(),
                recommendation_code=code,
                category="DRIFT",
                priority="HIGH",
                title=f"Drift crítico em {d.model_version}",
                action_hint="Retreinar e promover modelo; validar PSI < 0.25.",
                related_entity=d.id,
                impact_score=88,
            )
        )
        created += 1
    low_readiness = (
        db.query(MlIntegrationReadinessSnapshot)
        .filter(MlIntegrationReadinessSnapshot.readiness_band != "GO_LIVE")
        .limit(5)
        .all()
    )
    for r in low_readiness:
        code = f"READY_{r.network_player_code}"
        if db.query(MlOpsRecommendation).filter(MlOpsRecommendation.recommendation_code == code).first():
            continue
        db.add(
            MlOpsRecommendation(
                id=new_id(),
                recommendation_code=code,
                category="INTEGRATION",
                priority="MEDIUM",
                title=f"Elevar readiness {r.network_player_code}",
                action_hint="Completar telemetria, webhooks e perfil ML da rede.",
                related_entity=r.network_player_code,
                impact_score=float(r.score_total or 50),
            )
        )
        created += 1
    running = db.query(MlTrainingRun).filter(MlTrainingRun.status == "RUNNING").count()
    if running > 2:
        code = "TRAINING_QUEUE"
        if not db.query(MlOpsRecommendation).filter(MlOpsRecommendation.recommendation_code == code).first():
            db.add(
                MlOpsRecommendation(
                    id=new_id(),
                    recommendation_code=code,
                    category="OPS",
                    priority="LOW",
                    title="Fila de training runs elevada",
                    action_hint="Escalar workers ou pausar experimentos não críticos.",
                    impact_score=45,
                )
            )
            created += 1
    db.commit()
    return {"created": created}


def dismiss_recommendation(db: Session, rec_id: str) -> MlOpsRecommendation | None:
    row = db.get(MlOpsRecommendation, rec_id)
    if not row:
        return None
    row.status = "DISMISSED"
    row.dismissed_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def efficiency_scorecard(db: Session) -> dict:
    since = date.today() - timedelta(days=7)
    usage = db.query(MlInferenceUsageDaily).filter(MlInferenceUsageDaily.usage_date >= since).all()
    req_7d = sum(int(u.request_count or 0) for u in usage)
    latencies = [int(u.p95_latency_ms) for u in usage if u.p95_latency_ms is not None]
    avg_lat = sum(latencies) / len(latencies) if latencies else None
    cost_7d = sum(float(u.estimated_cost_usd or 0) for u in usage)
    open_breach = (
        db.query(func.count(MlFeatureFreshnessBreach.id))
        .filter(MlFeatureFreshnessBreach.status == "OPEN")
        .scalar()
        or 0
    )
    open_rec = (
        db.query(func.count(MlOpsRecommendation.id)).filter(MlOpsRecommendation.status == "OPEN").scalar() or 0
    )
    readiness_avg = db.query(func.avg(MlIntegrationReadinessSnapshot.score_total)).scalar() or 0
    err_avg = (
        sum(float(u.error_rate_pct or 0) for u in usage) / len(usage) if usage else 0
    )
    score = min(
        100.0,
        max(
            0.0,
            float(readiness_avg or 0) * 0.4
            + max(0, 100 - open_breach * 12) * 0.25
            + max(0, 100 - open_rec * 8) * 0.15
            + max(0, 100 - err_avg * 10) * 0.1
            + (100 if avg_lat is None or avg_lat < 150 else max(0, 100 - (avg_lat - 150) / 5)) * 0.1,
        ),
    )
    recs: list[str] = []
    if open_breach:
        recs.append(f"Resolver {open_breach} breach(es) de freshness de features.")
    if open_rec:
        recs.append(f"Tratar {open_rec} recomendação(ões) OPS abertas.")
    if err_avg > 1.5:
        recs.append("Error rate de inferência acima do SLO — revisar deployments.")
    if cost_7d > 500:
        recs.append("Custo estimado 7d elevado — considerar batch/caching de inferência.")
    if not recs:
        recs.append("Plataforma ML operando dentro dos SLOs.")
    return {
        "efficiency_score": round(score, 2),
        "inference_requests_7d": int(req_7d),
        "avg_p95_latency_ms": round(avg_lat, 2) if avg_lat is not None else None,
        "open_freshness_breaches": int(open_breach),
        "open_recommendations": int(open_rec),
        "estimated_cost_7d_usd": round(cost_7d, 2),
        "recommendations": recs,
    }
