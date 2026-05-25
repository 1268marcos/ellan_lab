from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.professional_ops import (
    HardwareCapabilityWebhook,
    HardwareCorridorHandoffStep,
    HardwareCorridorSla,
    HardwareIntegrationIncident,
    HardwareIntegrationReadiness,
    HardwareLockerCorridor,
    HardwareOnboardingMilestone,
    HardwareOnboardingPlaybook,
    HardwareOnboardingRun,
    HardwarePlayerCertification,
    HardwareReadinessAlert,
    HardwareSyncAuditLog,
)
from app.schemas.professional_ops import (
    HardwareCapabilityWebhookDeliveryListOut,
    HardwareCapabilityWebhookDeliveryOut,
    HardwareCapabilityWebhookListOut,
    HardwareCapabilityWebhookOut,
    HardwareCorridorHandoffStepOut,
    HardwareCorridorSlaOut,
    HardwareIntegrationIncidentListOut,
    HardwareIntegrationIncidentOut,
    HardwareIntegrationReadinessListOut,
    HardwareIntegrationReadinessPersistedOut,
    HardwareLockerCorridorOut,
    HardwareOnboardingMilestoneOut,
    HardwareOnboardingPlaybookOut,
    HardwareOnboardingRunOut,
    HardwarePlayerCertificationListOut,
    HardwarePlayerCertificationOut,
    HardwareProfessionalOpsSummaryOut,
    HardwareReadinessAlertListOut,
    HardwareReadinessAlertOut,
    HardwareSyncAuditLogListOut,
    HardwareSyncAuditLogOut,
)
from app.services import capability_webhook_service, professional_ops_service

router = APIRouter(prefix="/professional-ops", tags=["professional-ops"])


@router.get("/summary", response_model=HardwareProfessionalOpsSummaryOut)
def professional_summary(db: Session = Depends(get_db)) -> HardwareProfessionalOpsSummaryOut:
    return professional_ops_service.professional_ops_summary(db)


@router.post("/readiness/recompute")
def recompute_readiness(actor_id: str | None = Query(None), db: Session = Depends(get_db)) -> dict:
    return professional_ops_service.recompute_readiness(db, actor_id=actor_id)


@router.get("/readiness", response_model=HardwareIntegrationReadinessListOut)
def list_readiness(
    band: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareIntegrationReadinessListOut:
    q = db.query(HardwareIntegrationReadiness).order_by(HardwareIntegrationReadiness.score_total.desc())
    if band:
        q = q.filter(HardwareIntegrationReadiness.readiness_band == band.upper())
    rows = q.all()
    items = [HardwareIntegrationReadinessPersistedOut.model_validate(r) for r in rows]
    return HardwareIntegrationReadinessListOut(items=items, total=len(items))


@router.get("/readiness-alerts", response_model=HardwareReadinessAlertListOut)
def list_readiness_alerts(
    open_only: bool = Query(True), db: Session = Depends(get_db)
) -> HardwareReadinessAlertListOut:
    q = db.query(HardwareReadinessAlert).order_by(HardwareReadinessAlert.created_at.desc())
    if open_only:
        q = q.filter(HardwareReadinessAlert.status == "OPEN")
    items = [HardwareReadinessAlertOut.model_validate(r) for r in q.all()]
    return HardwareReadinessAlertListOut(items=items, total=len(items))


@router.post("/readiness-alerts/{alert_id}/acknowledge", response_model=HardwareReadinessAlertOut)
def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)) -> HardwareReadinessAlertOut:
    try:
        return HardwareReadinessAlertOut.model_validate(professional_ops_service.acknowledge_alert(db, alert_id))
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="alert_not_found") from None


@router.get("/incidents", response_model=HardwareIntegrationIncidentListOut)
def list_incidents(
    open_only: bool = Query(True), db: Session = Depends(get_db)
) -> HardwareIntegrationIncidentListOut:
    q = db.query(HardwareIntegrationIncident).order_by(HardwareIntegrationIncident.opened_at.desc())
    if open_only:
        q = q.filter(HardwareIntegrationIncident.status == "OPEN")
    items = [HardwareIntegrationIncidentOut.model_validate(r) for r in q.all()]
    return HardwareIntegrationIncidentListOut(items=items, total=len(items))


@router.post("/incidents/detect")
def detect_incidents(db: Session = Depends(get_db)) -> dict:
    return {"inserted": professional_ops_service.detect_incidents_from_signals(db)}


@router.get("/audit-log", response_model=HardwareSyncAuditLogListOut)
def list_audit_log(limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)) -> HardwareSyncAuditLogListOut:
    rows = db.query(HardwareSyncAuditLog).order_by(HardwareSyncAuditLog.created_at.desc()).limit(limit).all()
    items = [HardwareSyncAuditLogOut.model_validate(r) for r in rows]
    return HardwareSyncAuditLogListOut(items=items, total=len(items))


@router.get("/certifications", response_model=HardwarePlayerCertificationListOut)
def list_certifications(
    player_code: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwarePlayerCertificationListOut:
    q = db.query(HardwarePlayerCertification)
    if player_code:
        q = q.filter(HardwarePlayerCertification.player_code == player_code)
    items = [HardwarePlayerCertificationOut.model_validate(r) for r in q.all()]
    return HardwarePlayerCertificationListOut(items=items, total=len(items))


@router.get("/corridors", response_model=list[HardwareLockerCorridorOut])
def list_corridors(db: Session = Depends(get_db)) -> list[HardwareLockerCorridorOut]:
    rows = db.query(HardwareLockerCorridor).filter(HardwareLockerCorridor.active.is_(True)).order_by(HardwareLockerCorridor.priority).all()
    return [HardwareLockerCorridorOut.model_validate(r) for r in rows]


@router.get("/corridors/{corridor_id}/steps", response_model=list[HardwareCorridorHandoffStepOut])
def list_corridor_steps(corridor_id: str, db: Session = Depends(get_db)) -> list[HardwareCorridorHandoffStepOut]:
    rows = (
        db.query(HardwareCorridorHandoffStep)
        .filter(HardwareCorridorHandoffStep.corridor_id == corridor_id)
        .order_by(HardwareCorridorHandoffStep.step_order)
        .all()
    )
    return [HardwareCorridorHandoffStepOut.model_validate(r) for r in rows]


@router.get("/corridor-sla", response_model=list[HardwareCorridorSlaOut])
def list_corridor_sla(db: Session = Depends(get_db)) -> list[HardwareCorridorSlaOut]:
    return [HardwareCorridorSlaOut.model_validate(r) for r in db.query(HardwareCorridorSla).all()]


@router.get("/onboarding/playbooks", response_model=list[HardwareOnboardingPlaybookOut])
def list_playbooks(db: Session = Depends(get_db)) -> list[HardwareOnboardingPlaybookOut]:
    return [HardwareOnboardingPlaybookOut.model_validate(r) for r in db.query(HardwareOnboardingPlaybook).all()]


@router.get("/onboarding/runs", response_model=list[HardwareOnboardingRunOut])
def list_onboarding_runs(db: Session = Depends(get_db)) -> list[HardwareOnboardingRunOut]:
    return [HardwareOnboardingRunOut.model_validate(r) for r in db.query(HardwareOnboardingRun).all()]


@router.get("/onboarding/runs/{run_id}/milestones", response_model=list[HardwareOnboardingMilestoneOut])
def list_milestones(run_id: str, db: Session = Depends(get_db)) -> list[HardwareOnboardingMilestoneOut]:
    rows = (
        db.query(HardwareOnboardingMilestone)
        .filter(HardwareOnboardingMilestone.run_id == run_id)
        .order_by(HardwareOnboardingMilestone.step_order)
        .all()
    )
    return [HardwareOnboardingMilestoneOut.model_validate(r) for r in rows]


@router.get("/capability-webhooks", response_model=HardwareCapabilityWebhookListOut)
def list_capability_webhooks(
    player_code: str | None = Query(None), db: Session = Depends(get_db)
) -> HardwareCapabilityWebhookListOut:
    q = db.query(HardwareCapabilityWebhook)
    if player_code:
        q = q.filter(HardwareCapabilityWebhook.player_code == player_code)
    items = [HardwareCapabilityWebhookOut.model_validate(r) for r in q.all()]
    return HardwareCapabilityWebhookListOut(items=items, total=len(items))


@router.get("/capability-webhooks/deliveries", response_model=HardwareCapabilityWebhookDeliveryListOut)
def list_webhook_deliveries(
    status: str | None = Query(None),
    webhook_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> HardwareCapabilityWebhookDeliveryListOut:
    rows = capability_webhook_service.list_deliveries(db, status=status, webhook_id=webhook_id, limit=limit)
    items = [HardwareCapabilityWebhookDeliveryOut.model_validate(r) for r in rows]
    return HardwareCapabilityWebhookDeliveryListOut(items=items, total=len(items))


@router.post("/capability-webhooks/{webhook_id}/test", response_model=HardwareCapabilityWebhookDeliveryOut)
def test_capability_webhook(webhook_id: str, db: Session = Depends(get_db)) -> HardwareCapabilityWebhookDeliveryOut:
    return HardwareCapabilityWebhookDeliveryOut.model_validate(capability_webhook_service.test_webhook(db, webhook_id))


@router.post("/capability-webhooks/deliveries/{delivery_id}/replay", response_model=HardwareCapabilityWebhookDeliveryOut)
def replay_webhook_delivery(delivery_id: str, db: Session = Depends(get_db)) -> HardwareCapabilityWebhookDeliveryOut:
    return HardwareCapabilityWebhookDeliveryOut.model_validate(capability_webhook_service.replay_delivery(db, delivery_id))


@router.post("/capability-webhooks/deliveries/replay-dead-letter")
def replay_dead_letter_batch(limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)) -> dict:
    return capability_webhook_service.replay_dead_letter_batch(db, limit=limit)


@router.post("/capability-webhooks/seed-dlq-demo")
def seed_dlq_demo(db: Session = Depends(get_db)) -> dict:
    return capability_webhook_service.seed_demo_deliveries_to_dlq(db)


@router.post("/certifications/mirror-marketplace")
def mirror_marketplace_certifications(db: Session = Depends(get_db)) -> dict:
    try:
        return professional_ops_service.mirror_certifications_from_marketplace(db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
