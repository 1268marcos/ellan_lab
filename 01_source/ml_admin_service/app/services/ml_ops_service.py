from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ml_core import MlModelMetadata
from app.models.ml_ops import (
    MlAlertRule,
    MlDeploymentEvent,
    MlDriftReport,
    MlFeatureDefinition,
    MlInferenceSlo,
    MlModelRegistryEntry,
    MlPartnerUseCaseGrant,
    MlTrainingRun,
    MlUseCase,
)
from app.schemas.ml_ops import (
    MlAlertRuleIn,
    MlDeploymentEventIn,
    MlDriftReportIn,
    MlFeatureDefinitionIn,
    MlInferenceSloIn,
    MlModelRegistryIn,
    MlPartnerGrantIn,
    MlTrainingRunIn,
    MlUseCaseIn,
)
from app.services.crypto_util import new_id

VALID_STAGES = {"DEV", "STAGING", "PRODUCTION", "ARCHIVED"}
VALID_RUN_STATUS = {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"}
VALID_DRIFT_STATUS = {"OK", "WARNING", "CRITICAL"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _get_use_case_or_404(db: Session, use_case_id: str) -> MlUseCase:
    row = db.get(MlUseCase, use_case_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="use_case_not_found")
    return row


# --- use cases ---


def list_use_cases(db: Session, active_only: bool = False) -> list[MlUseCase]:
    q = db.query(MlUseCase)
    if active_only:
        q = q.filter(MlUseCase.active.is_(True))
    return q.order_by(MlUseCase.code).all()


def create_use_case(db: Session, body: MlUseCaseIn) -> MlUseCase:
    if db.query(MlUseCase).filter(MlUseCase.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="use_case_code_exists")
    row = MlUseCase(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- model registry ---


def list_registry(db: Session, use_case_id: str | None = None, stage: str | None = None) -> list[MlModelRegistryEntry]:
    q = db.query(MlModelRegistryEntry)
    if use_case_id:
        q = q.filter(MlModelRegistryEntry.use_case_id == use_case_id)
    if stage:
        q = q.filter(MlModelRegistryEntry.stage == stage)
    return q.order_by(MlModelRegistryEntry.updated_at.desc()).all()


def create_registry_entry(db: Session, body: MlModelRegistryIn) -> MlModelRegistryEntry:
    _get_use_case_or_404(db, body.use_case_id)
    if body.stage not in VALID_STAGES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_stage")
    exists = (
        db.query(MlModelRegistryEntry)
        .filter(
            MlModelRegistryEntry.use_case_id == body.use_case_id,
            MlModelRegistryEntry.model_version == body.model_version,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="registry_version_exists")
    row = MlModelRegistryEntry(
        id=new_id(),
        use_case_id=body.use_case_id,
        model_version=body.model_version,
        algorithm=body.algorithm,
        framework=body.framework,
        artifact_uri=body.artifact_uri,
        stage=body.stage,
        status_note=body.status_note,
        registry_metadata_json=json.dumps(body.registry_metadata),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def promote_registry_entry(db: Session, entry_id: str, actor_id: str | None, notes: str | None) -> MlModelRegistryEntry:
    row = db.get(MlModelRegistryEntry, entry_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="registry_entry_not_found")
    prev = (
        db.query(MlModelRegistryEntry)
        .filter(
            MlModelRegistryEntry.use_case_id == row.use_case_id,
            MlModelRegistryEntry.stage == "PRODUCTION",
            MlModelRegistryEntry.id != row.id,
        )
        .first()
    )
    from_version = prev.model_version if prev else None
    if prev:
        prev.stage = "ARCHIVED"
        prev.updated_at = _utcnow()
    row.stage = "PRODUCTION"
    row.promoted_at = _utcnow()
    row.updated_at = _utcnow()
    db.add(
        MlDeploymentEvent(
            id=new_id(),
            use_case_id=row.use_case_id,
            from_version=from_version,
            to_version=row.model_version,
            event_type="PROMOTE",
            actor_id=actor_id,
            notes=notes,
        )
    )
    meta = db.query(MlModelMetadata).filter(MlModelMetadata.model_version == row.model_version).first()
    if meta:
        db.query(MlModelMetadata).filter(MlModelMetadata.status == "ACTIVE").update({"status": "STALE"})
        meta.status = "ACTIVE"
    else:
        db.add(
            MlModelMetadata(
                model_version=row.model_version,
                metrics_json=row.registry_metadata_json,
                status="ACTIVE",
            )
        )
    db.commit()
    db.refresh(row)
    return row


# --- training runs ---


def list_training_runs(db: Session, use_case_id: str | None = None, limit: int = 100) -> list[MlTrainingRun]:
    q = db.query(MlTrainingRun)
    if use_case_id:
        q = q.filter(MlTrainingRun.use_case_id == use_case_id)
    return q.order_by(MlTrainingRun.created_at.desc()).limit(limit).all()


def create_training_run(db: Session, body: MlTrainingRunIn) -> MlTrainingRun:
    _get_use_case_or_404(db, body.use_case_id)
    row = MlTrainingRun(
        id=new_id(),
        use_case_id=body.use_case_id,
        run_name=body.run_name,
        triggered_by=body.triggered_by,
        dataset_ref=body.dataset_ref,
        hyperparams_json=json.dumps(body.hyperparams),
        status="QUEUED",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def complete_training_run(
    db: Session, run_id: str, *, ok: bool, model_version: str | None, metrics: dict | None, error: str | None
) -> MlTrainingRun:
    row = db.get(MlTrainingRun, run_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="training_run_not_found")
    now = _utcnow()
    row.started_at = row.started_at or now
    row.finished_at = now
    if ok:
        row.status = "SUCCEEDED"
        row.model_version = model_version
        row.metrics_json = json.dumps(metrics or {})
    else:
        row.status = "FAILED"
        row.error_message = error
    db.commit()
    db.refresh(row)
    return row


# --- feature catalog ---


def list_feature_definitions(db: Session, use_case_id: str | None = None) -> list[MlFeatureDefinition]:
    q = db.query(MlFeatureDefinition).filter(MlFeatureDefinition.active.is_(True))
    if use_case_id:
        q = q.filter(MlFeatureDefinition.use_case_id == use_case_id)
    return q.order_by(MlFeatureDefinition.feature_group, MlFeatureDefinition.feature_name).all()


def create_feature_definition(db: Session, body: MlFeatureDefinitionIn) -> MlFeatureDefinition:
    if body.use_case_id:
        _get_use_case_or_404(db, body.use_case_id)
    if db.query(MlFeatureDefinition).filter(MlFeatureDefinition.feature_name == body.feature_name).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="feature_name_exists")
    row = MlFeatureDefinition(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- drift ---


def list_drift_reports(db: Session, use_case_id: str | None = None, limit: int = 100) -> list[MlDriftReport]:
    q = db.query(MlDriftReport)
    if use_case_id:
        q = q.filter(MlDriftReport.use_case_id == use_case_id)
    return q.order_by(MlDriftReport.report_date.desc()).limit(limit).all()


def create_drift_report(db: Session, body: MlDriftReportIn) -> MlDriftReport:
    _get_use_case_or_404(db, body.use_case_id)
    if body.status not in VALID_DRIFT_STATUS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid_drift_status")
    row = MlDriftReport(
        id=new_id(),
        use_case_id=body.use_case_id,
        model_version=body.model_version,
        report_date=body.report_date or date.today(),
        drift_type=body.drift_type,
        psi_score=body.psi_score,
        status=body.status,
        details_json=json.dumps(body.details),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- SLO & alerts ---


def list_inference_slos(db: Session) -> list[MlInferenceSlo]:
    return db.query(MlInferenceSlo).order_by(MlInferenceSlo.use_case_id).all()


def upsert_inference_slo(db: Session, body: MlInferenceSloIn) -> MlInferenceSlo:
    _get_use_case_or_404(db, body.use_case_id)
    row = db.query(MlInferenceSlo).filter(MlInferenceSlo.use_case_id == body.use_case_id).first()
    data = body.model_dump()
    if row:
        for k, v in data.items():
            if k != "use_case_id":
                setattr(row, k, v)
        row.updated_at = _utcnow()
    else:
        row = MlInferenceSlo(id=new_id(), **data)
        db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_alert_rules(db: Session, use_case_id: str | None = None) -> list[MlAlertRule]:
    q = db.query(MlAlertRule).filter(MlAlertRule.active.is_(True))
    if use_case_id:
        q = q.filter(MlAlertRule.use_case_id == use_case_id)
    return q.order_by(MlAlertRule.severity.desc(), MlAlertRule.rule_code).all()


def create_alert_rule(db: Session, body: MlAlertRuleIn) -> MlAlertRule:
    _get_use_case_or_404(db, body.use_case_id)
    row = MlAlertRule(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- deployments ---


def list_deployment_events(db: Session, use_case_id: str | None = None, limit: int = 100) -> list[MlDeploymentEvent]:
    q = db.query(MlDeploymentEvent)
    if use_case_id:
        q = q.filter(MlDeploymentEvent.use_case_id == use_case_id)
    return q.order_by(MlDeploymentEvent.created_at.desc()).limit(limit).all()


def create_deployment_event(db: Session, body: MlDeploymentEventIn) -> MlDeploymentEvent:
    _get_use_case_or_404(db, body.use_case_id)
    row = MlDeploymentEvent(id=new_id(), **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


# --- partner grants ---


def list_partner_grants(db: Session, partner_id: str | None = None) -> list[MlPartnerUseCaseGrant]:
    q = db.query(MlPartnerUseCaseGrant)
    if partner_id:
        q = q.filter(MlPartnerUseCaseGrant.partner_id == partner_id)
    return q.all()


def create_partner_grant(db: Session, body: MlPartnerGrantIn) -> MlPartnerUseCaseGrant:
    _get_use_case_or_404(db, body.use_case_id)
    if (
        db.query(MlPartnerUseCaseGrant)
        .filter(
            MlPartnerUseCaseGrant.partner_id == body.partner_id,
            MlPartnerUseCaseGrant.use_case_id == body.use_case_id,
        )
        .first()
    ):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="grant_exists")
    row = MlPartnerUseCaseGrant(
        partner_id=body.partner_id,
        use_case_id=body.use_case_id,
        scopes_json=json.dumps(body.scopes or ["ml:predict", "ml:read"]),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ops_dashboard_counts(db: Session) -> dict:
    return {
        "use_cases": db.query(MlUseCase).filter(MlUseCase.active.is_(True)).count(),
        "registry_production": db.query(MlModelRegistryEntry).filter(MlModelRegistryEntry.stage == "PRODUCTION").count(),
        "training_running": db.query(MlTrainingRun).filter(MlTrainingRun.status == "RUNNING").count(),
        "drift_critical": db.query(MlDriftReport).filter(MlDriftReport.status == "CRITICAL").count(),
        "feature_definitions": db.query(MlFeatureDefinition).filter(MlFeatureDefinition.active.is_(True)).count(),
        "alert_rules": db.query(MlAlertRule).filter(MlAlertRule.active.is_(True)).count(),
        "deployments_7d": db.query(MlDeploymentEvent)
        .filter(MlDeploymentEvent.created_at >= _utcnow() - timedelta(days=7))
        .count(),
    }
