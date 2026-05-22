from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.ml_ops import (
    MlAlertRuleIn,
    MlAlertRuleListOut,
    MlAlertRuleOut,
    MlDeploymentEventIn,
    MlDeploymentEventListOut,
    MlDeploymentEventOut,
    MlDriftReportIn,
    MlDriftReportListOut,
    MlDriftReportOut,
    MlFeatureDefinitionIn,
    MlFeatureDefinitionListOut,
    MlFeatureDefinitionOut,
    MlInferenceSloIn,
    MlInferenceSloListOut,
    MlInferenceSloOut,
    MlModelRegistryIn,
    MlModelRegistryListOut,
    MlModelRegistryOut,
    MlModelRegistryPromoteIn,
    MlPartnerGrantIn,
    MlPartnerGrantListOut,
    MlPartnerGrantOut,
    MlTrainingRunIn,
    MlTrainingRunListOut,
    MlTrainingRunOut,
    MlUseCaseIn,
    MlUseCaseListOut,
    MlUseCaseOut,
)
from app.services import ml_ops_service

router = APIRouter(tags=["ml-ops"])


class TrainingRunCompleteIn(BaseModel):
    ok: bool = True
    model_version: str | None = None
    metrics: dict = Field(default_factory=dict)
    error: str | None = None


@router.get("/ml-use-cases", response_model=MlUseCaseListOut)
def list_use_cases(active_only: bool = Query(False), db: Session = Depends(get_db)) -> MlUseCaseListOut:
    items = ml_ops_service.list_use_cases(db, active_only=active_only)
    out = [MlUseCaseOut.model_validate(i) for i in items]
    return MlUseCaseListOut(items=out, total=len(out))


@router.post("/ml-use-cases", response_model=MlUseCaseOut, status_code=status.HTTP_201_CREATED)
def create_use_case(body: MlUseCaseIn, db: Session = Depends(get_db)) -> MlUseCaseOut:
    return MlUseCaseOut.model_validate(ml_ops_service.create_use_case(db, body))


@router.get("/ml-model-registry", response_model=MlModelRegistryListOut)
def list_registry(
    use_case_id: str | None = Query(None),
    stage: str | None = Query(None),
    db: Session = Depends(get_db),
) -> MlModelRegistryListOut:
    items = ml_ops_service.list_registry(db, use_case_id=use_case_id, stage=stage)
    out = [MlModelRegistryOut.model_validate(i) for i in items]
    return MlModelRegistryListOut(items=out, total=len(out))


@router.post("/ml-model-registry", response_model=MlModelRegistryOut, status_code=status.HTTP_201_CREATED)
def create_registry(body: MlModelRegistryIn, db: Session = Depends(get_db)) -> MlModelRegistryOut:
    return MlModelRegistryOut.model_validate(ml_ops_service.create_registry_entry(db, body))


@router.post("/ml-model-registry/{entry_id}/promote", response_model=MlModelRegistryOut)
def promote_registry(
    entry_id: str, body: MlModelRegistryPromoteIn, db: Session = Depends(get_db)
) -> MlModelRegistryOut:
    return MlModelRegistryOut.model_validate(
        ml_ops_service.promote_registry_entry(db, entry_id, body.actor_id, body.notes)
    )


@router.get("/ml-training-runs", response_model=MlTrainingRunListOut)
def list_training_runs(
    use_case_id: str | None = Query(None), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)
) -> MlTrainingRunListOut:
    items = ml_ops_service.list_training_runs(db, use_case_id=use_case_id, limit=limit)
    out = [MlTrainingRunOut.model_validate(i) for i in items]
    return MlTrainingRunListOut(items=out, total=len(out))


@router.post("/ml-training-runs", response_model=MlTrainingRunOut, status_code=status.HTTP_201_CREATED)
def create_training_run(body: MlTrainingRunIn, db: Session = Depends(get_db)) -> MlTrainingRunOut:
    return MlTrainingRunOut.model_validate(ml_ops_service.create_training_run(db, body))


@router.post("/ml-training-runs/{run_id}/complete", response_model=MlTrainingRunOut)
def complete_training_run(
    run_id: str, body: TrainingRunCompleteIn, db: Session = Depends(get_db)
) -> MlTrainingRunOut:
    return MlTrainingRunOut.model_validate(
        ml_ops_service.complete_training_run(
            db,
            run_id,
            ok=body.ok,
            model_version=body.model_version,
            metrics=body.metrics,
            error=body.error,
        )
    )


@router.get("/ml-feature-definitions", response_model=MlFeatureDefinitionListOut)
def list_feature_definitions(
    use_case_id: str | None = Query(None), db: Session = Depends(get_db)
) -> MlFeatureDefinitionListOut:
    items = ml_ops_service.list_feature_definitions(db, use_case_id=use_case_id)
    out = [MlFeatureDefinitionOut.model_validate(i) for i in items]
    return MlFeatureDefinitionListOut(items=out, total=len(out))


@router.post("/ml-feature-definitions", response_model=MlFeatureDefinitionOut, status_code=status.HTTP_201_CREATED)
def create_feature_definition(body: MlFeatureDefinitionIn, db: Session = Depends(get_db)) -> MlFeatureDefinitionOut:
    return MlFeatureDefinitionOut.model_validate(ml_ops_service.create_feature_definition(db, body))


@router.get("/ml-drift-reports", response_model=MlDriftReportListOut)
def list_drift_reports(
    use_case_id: str | None = Query(None), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)
) -> MlDriftReportListOut:
    items = ml_ops_service.list_drift_reports(db, use_case_id=use_case_id, limit=limit)
    out = [MlDriftReportOut.model_validate(i) for i in items]
    return MlDriftReportListOut(items=out, total=len(out))


@router.post("/ml-drift-reports", response_model=MlDriftReportOut, status_code=status.HTTP_201_CREATED)
def create_drift_report(body: MlDriftReportIn, db: Session = Depends(get_db)) -> MlDriftReportOut:
    return MlDriftReportOut.model_validate(ml_ops_service.create_drift_report(db, body))


@router.get("/ml-inference-slo", response_model=MlInferenceSloListOut)
def list_inference_slos(db: Session = Depends(get_db)) -> MlInferenceSloListOut:
    items = ml_ops_service.list_inference_slos(db)
    out = [MlInferenceSloOut.model_validate(i) for i in items]
    return MlInferenceSloListOut(items=out, total=len(out))


@router.put("/ml-inference-slo", response_model=MlInferenceSloOut)
def upsert_inference_slo(body: MlInferenceSloIn, db: Session = Depends(get_db)) -> MlInferenceSloOut:
    return MlInferenceSloOut.model_validate(ml_ops_service.upsert_inference_slo(db, body))


@router.get("/ml-alert-rules", response_model=MlAlertRuleListOut)
def list_alert_rules(
    use_case_id: str | None = Query(None), db: Session = Depends(get_db)
) -> MlAlertRuleListOut:
    items = ml_ops_service.list_alert_rules(db, use_case_id=use_case_id)
    out = [MlAlertRuleOut.model_validate(i) for i in items]
    return MlAlertRuleListOut(items=out, total=len(out))


@router.post("/ml-alert-rules", response_model=MlAlertRuleOut, status_code=status.HTTP_201_CREATED)
def create_alert_rule(body: MlAlertRuleIn, db: Session = Depends(get_db)) -> MlAlertRuleOut:
    return MlAlertRuleOut.model_validate(ml_ops_service.create_alert_rule(db, body))


@router.get("/ml-deployment-events", response_model=MlDeploymentEventListOut)
def list_deployment_events(
    use_case_id: str | None = Query(None), limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db)
) -> MlDeploymentEventListOut:
    items = ml_ops_service.list_deployment_events(db, use_case_id=use_case_id, limit=limit)
    out = [MlDeploymentEventOut.model_validate(i) for i in items]
    return MlDeploymentEventListOut(items=out, total=len(out))


@router.post("/ml-deployment-events", response_model=MlDeploymentEventOut, status_code=status.HTTP_201_CREATED)
def create_deployment_event(body: MlDeploymentEventIn, db: Session = Depends(get_db)) -> MlDeploymentEventOut:
    return MlDeploymentEventOut.model_validate(ml_ops_service.create_deployment_event(db, body))


@router.get("/ml-partner-use-case-grants", response_model=MlPartnerGrantListOut)
def list_partner_grants(
    partner_id: str | None = Query(None), db: Session = Depends(get_db)
) -> MlPartnerGrantListOut:
    items = ml_ops_service.list_partner_grants(db, partner_id=partner_id)
    out = [MlPartnerGrantOut.model_validate(i) for i in items]
    return MlPartnerGrantListOut(items=out, total=len(out))


@router.post("/ml-partner-use-case-grants", response_model=MlPartnerGrantOut, status_code=status.HTTP_201_CREATED)
def create_partner_grant(body: MlPartnerGrantIn, db: Session = Depends(get_db)) -> MlPartnerGrantOut:
    return MlPartnerGrantOut.model_validate(ml_ops_service.create_partner_grant(db, body))
