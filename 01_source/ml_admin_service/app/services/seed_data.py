from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.ml_core import MlFeaturesDaily, MlModelMetadata, MlPredictionFeedback, MlPredictionsLog
from app.models.ml_ops import (
    MlAlertRule,
    MlDriftReport,
    MlFeatureDefinition,
    MlInferenceSlo,
    MlModelRegistryEntry,
    MlPartnerUseCaseGrant,
    MlTrainingRun,
    MlUseCase,
)
from app.models.partner import MlDataPartner
from app.schemas.partner import WebhookConfigureIn
from app.services import network_players_service, partner_service
from app.services.crypto_util import new_id


USE_CASE_SEEDS = [
    ("LOCKER_HEALTH", "Saude preditiva de locker", "LOCKER", "CRITICAL"),
    ("OCCUPANCY_DEMAND", "Previsao de ocupacao", "LOCKER", "STANDARD"),
    ("PARTNER_CHURN", "Risco de churn de parceiro", "PARTNER", "STANDARD"),
    ("PICKUP_FRAUD", "Fraude em retirada", "LOGISTICS", "CRITICAL"),
    ("CUSTOMER_LTV", "LTV de cliente", "CUSTOMER", "STANDARD"),
    ("DYNAMIC_PRICING", "Precificacao dinamica", "PRICING", "EXPERIMENTAL"),
    ("FEEDBACK_NLP", "NLP em feedback", "CUSTOMER", "STANDARD"),
    ("ROUTE_OPTIMIZE", "Otimizacao de rotas", "LOGISTICS", "STANDARD"),
    ("NETWORK_HEALTH_BENCHMARK", "Benchmark saude por rede locker", "LOCKER", "STANDARD"),
    ("CROSS_NETWORK_OCCUPANCY", "Ocupacao comparada entre redes", "LOCKER", "STANDARD"),
    ("INTEGRATION_READINESS", "Prontidao de integracao por player", "PARTNER", "STANDARD"),
]

FEATURE_SEEDS = [
    ("battery_min", "telemetry", "ml_features_daily"),
    ("door_failures_7d", "telemetry", "ml_features_daily"),
    ("usage_events_7d", "usage", "ml_features_daily"),
    ("uptime_hours_7d", "telemetry", "ml_features_daily"),
    ("temperature_mean", "environmental", "ml_features_daily"),
    ("humidity_mean", "environmental", "ml_features_daily"),
    ("network_uptime_7d", "network", "ml_features_daily"),
    ("parcel_throughput_7d", "network", "ml_features_daily"),
    ("locker_fill_rate_7d", "network", "ml_features_daily"),
]


def run_seed(db: Session) -> dict[str, int]:
    counts = {
        "partners": 0,
        "models": 0,
        "features": 0,
        "predictions": 0,
        "feedback": 0,
        "use_cases": 0,
        "registry": 0,
        "feature_defs": 0,
        "slos": 0,
        "alerts": 0,
        "drift": 0,
        "training": 0,
        "grants": 0,
        "network_players": 0,
        "network_profiles": 0,
    }

    if not db.query(MlDataPartner).filter(MlDataPartner.code == "TELEMETRY-BR").first():
        pid = new_id()
        db.add(
            MlDataPartner(
                id=pid,
                name="Telemetria Brasil",
                code="TELEMETRY-BR",
                partner_type="TELEMETRY",
                region_code="BR",
                api_base_url="https://telemetry.example/ml",
                active=True,
            )
        )
        db.flush()
        counts["partners"] += 1
        partner_service.configure_webhook(
            db,
            pid,
            WebhookConfigureIn(
                url="https://hooks.example/ml/telemetry",
                secret="whsec_ml_demo",
                events=["prediction.*"],
            ),
        )

    use_case_ids: dict[str, str] = {}
    for code, name, domain, tier in USE_CASE_SEEDS:
        row = db.query(MlUseCase).filter(MlUseCase.code == code).first()
        if not row:
            uid = new_id()
            db.add(
                MlUseCase(
                    id=uid,
                    code=code,
                    name=name,
                    domain=domain,
                    tier=tier,
                    owner_team="ml-platform",
                    description=f"Caso de uso {code} — Ellan ML platform",
                    active=True,
                )
            )
            use_case_ids[code] = uid
            counts["use_cases"] += 1
        else:
            use_case_ids[code] = row.id

    health_uc = use_case_ids.get("LOCKER_HEALTH")
    if health_uc and not db.query(MlModelRegistryEntry).filter(
        MlModelRegistryEntry.use_case_id == health_uc, MlModelRegistryEntry.model_version == "rf-v1-demo"
    ).first():
        db.add(
            MlModelRegistryEntry(
                id=new_id(),
                use_case_id=health_uc,
                model_version="rf-v1-demo",
                algorithm="RandomForest",
                framework="sklearn",
                artifact_uri="s3://ellan-ml/models/rf-v1-demo.pkl",
                stage="PRODUCTION",
                registry_metadata_json=json.dumps({"auc": 0.82, "f1": 0.71}),
                promoted_at=datetime.now(timezone.utc),
            )
        )
        counts["registry"] += 1

    for fname, fgroup, src in FEATURE_SEEDS:
        if not db.query(MlFeatureDefinition).filter(MlFeatureDefinition.feature_name == fname).first():
            db.add(
                MlFeatureDefinition(
                    id=new_id(),
                    use_case_id=health_uc,
                    feature_name=fname,
                    feature_group=fgroup,
                    source_table=src,
                    data_type="float",
                    freshness_hours=24,
                    description=f"Feature {fname}",
                )
            )
            counts["feature_defs"] += 1

    if health_uc and not db.query(MlInferenceSlo).filter(MlInferenceSlo.use_case_id == health_uc).first():
        db.add(
            MlInferenceSlo(
                id=new_id(),
                use_case_id=health_uc,
                p95_latency_ms=350,
                min_availability_pct=99.9,
                max_error_rate_pct=0.5,
                min_predictions_per_day=500,
            )
        )
        counts["slos"] += 1

    if health_uc and not db.query(MlAlertRule).filter(
        MlAlertRule.use_case_id == health_uc, MlAlertRule.rule_code == "DRIFT_PSI"
    ).first():
        db.add(
            MlAlertRule(
                id=new_id(),
                use_case_id=health_uc,
                rule_code="DRIFT_PSI",
                metric="psi_score",
                operator="GT",
                threshold=0.25,
                severity="CRITICAL",
            )
        )
        counts["alerts"] += 1

    if health_uc and not db.query(MlDriftReport).filter(MlDriftReport.use_case_id == health_uc).first():
        db.add(
            MlDriftReport(
                id=new_id(),
                use_case_id=health_uc,
                model_version="rf-v1-demo",
                report_date=date.today(),
                drift_type="DATA",
                psi_score=0.08,
                status="OK",
                details_json=json.dumps({"window_days": 7}),
            )
        )
        counts["drift"] += 1

    if health_uc and not db.query(MlTrainingRun).filter(MlTrainingRun.run_name == "nightly-health-v1").first():
        db.add(
            MlTrainingRun(
                id=new_id(),
                use_case_id=health_uc,
                run_name="nightly-health-v1",
                model_version="rf-v1-demo",
                status="SUCCEEDED",
                triggered_by="scheduler",
                dataset_ref="ml_features_daily:last_90d",
                hyperparams_json=json.dumps({"n_estimators": 200, "max_depth": 12}),
                metrics_json=json.dumps({"auc": 0.82}),
            )
        )
        counts["training"] += 1

    if not db.query(MlModelMetadata).filter(MlModelMetadata.model_version == "rf-v1-demo").first():
        db.add(
            MlModelMetadata(
                model_version="rf-v1-demo",
                metrics_json=json.dumps({"auc": 0.82, "f1": 0.71}),
                status="ACTIVE",
            )
        )
        counts["models"] += 1

    locker_demo = "locker-ml-demo-001"
    fd = date.today() - timedelta(days=1)
    if not db.query(MlFeaturesDaily).filter(MlFeaturesDaily.locker_id == locker_demo, MlFeaturesDaily.feature_date == fd).first():
        db.add(
            MlFeaturesDaily(
                locker_id=locker_demo,
                feature_date=fd,
                temperature_mean=22.5,
                humidity_mean=55.0,
                battery_min=78.0,
                door_failures_7d=1,
                usage_events_7d=42,
                uptime_hours_7d=120.0,
                failure_label_7d=0,
            )
        )
        counts["features"] += 1

    if not db.query(MlPredictionsLog).filter(MlPredictionsLog.locker_id == locker_demo).first():
        pred = MlPredictionsLog(
            locker_id=locker_demo,
            failure_probability=0.12,
            health_score=88.0,
            model_version="rf-v1-demo",
        )
        db.add(pred)
        db.flush()
        db.add(
            MlPredictionFeedback(
                id=new_id(),
                prediction_id=pred.id,
                actual_value=0.0,
                error_pct=12.0,
                model_performance_status="GOOD",
            )
        )
        counts["predictions"] += 1
        counts["feedback"] += 1

    partner_row = db.query(MlDataPartner).filter(MlDataPartner.code == "TELEMETRY-BR").first()
    if health_uc and partner_row:
        if partner_row and not db.query(MlPartnerUseCaseGrant).filter(
            MlPartnerUseCaseGrant.partner_id == partner_row.id,
            MlPartnerUseCaseGrant.use_case_id == health_uc,
        ).first():
            db.add(
                MlPartnerUseCaseGrant(
                    partner_id=partner_row.id,
                    use_case_id=health_uc,
                    scopes_json=json.dumps(["ml:predict", "ml:read", "ml:features"]),
                )
            )
            counts["grants"] += 1

    net_seed = network_players_service.seed_from_catalog(db)
    counts["network_players"] = net_seed.get("inserted", 0) + net_seed.get("updated", 0)
    counts["network_profiles"] = net_seed.get("profiles_created", 0)

    db.commit()
    return counts
