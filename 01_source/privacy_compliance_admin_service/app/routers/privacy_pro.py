from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.privacy_extended import TransferRecordOut
from app.schemas.privacy_pro import (
    AuditEventListOut,
    BreachTimelineOut,
    ComplianceCompareOut,
    ComplianceScoreOut,
    ConsentAnalyticsOut,
    DsrTaskListOut,
    DsrTaskOut,
    DsrTaskUpdate,
    GlobalOpsBridgeSummaryOut,
    GlobalOpsSyncOut,
    IntegrationHealthListOut,
    PlayerCertificationMirrorListOut,
    PlayerCertificationMirrorOut,
    RopaGraphOut,
    TransferWizardSessionOut,
    TransferWizardStartIn,
    TransferWizardStepIn,
    WebhookDeliveryListOut,
    WebhookDeliveryOut,
    WebhookDispatchIn,
    WebhookProcessOut,
)
from app.services.compliance_score_service import compare_regulations, compute_compliance_score
from app.services.global_ops_bridge_service import (
    global_ops_bridge_summary,
    list_certification_mirrors,
    sync_certifications_from_partner,
)
from app.services.privacy_pro_service import (
    breach_timeline,
    consent_analytics,
    dsr_tasks,
    list_audit_events,
    list_integration_health,
    ropa_graph,
    update_dsr_task,
)
from app.services.transfer_wizard_service import advance_wizard_step, complete_wizard, get_wizard, start_wizard
from app.services.webhook_dispatcher_service import (
    dispatch_delivery,
    enqueue_webhook_event,
    list_webhook_deliveries,
    process_pending_deliveries,
)

router = APIRouter(tags=["privacy-pro"])


@router.get("/compliance/score", response_model=ComplianceScoreOut)
def get_compliance_score(
    regulation_code: str = Query(..., min_length=2),
    persist: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    return compute_compliance_score(db, regulation_code, persist=persist)


@router.get("/compliance/compare", response_model=ComplianceCompareOut)
def get_compliance_compare(
    codes: str = Query(..., description="Comma-separated regulation codes, e.g. GDPR,LGPD,CCPA"),
    db: Session = Depends(get_db),
):
    return compare_regulations(db, [c.strip() for c in codes.split(",") if c.strip()])


@router.get("/audit-events", response_model=AuditEventListOut)
def get_audit_events(
    regulation_code: str | None = None,
    resource_type: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items = list_audit_events(db, regulation_code=regulation_code, resource_type=resource_type, limit=limit)
    return AuditEventListOut(items=items, total=len(items))


@router.get("/analytics/consents", response_model=ConsentAnalyticsOut)
def get_consent_analytics(
    regulation_code: str | None = None,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    return consent_analytics(db, regulation_code=regulation_code, days=days)


@router.get("/breach-incidents/{breach_id}/timeline", response_model=BreachTimelineOut)
def get_breach_timeline(breach_id: str, db: Session = Depends(get_db)):
    return breach_timeline(db, breach_id)


@router.get("/subject-requests/{request_id}/tasks", response_model=DsrTaskListOut)
def get_dsr_tasks(request_id: str, db: Session = Depends(get_db)):
    return dsr_tasks(db, request_id)


@router.patch("/dsr-tasks/{task_id}", response_model=DsrTaskOut)
def patch_dsr_task(task_id: str, body: DsrTaskUpdate, db: Session = Depends(get_db)):
    return update_dsr_task(db, task_id, status=body.status, assignee=body.assignee, notes=body.notes)


@router.get("/ropa/graph", response_model=RopaGraphOut)
def get_ropa_graph(
    regulation_code: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    return ropa_graph(db, regulation_code)


@router.get("/ecosystem/health", response_model=IntegrationHealthListOut)
def get_ecosystem_health(
    player_code: str | None = None,
    status: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return list_integration_health(db, player_code=player_code, status_filter=status, limit=limit)


@router.post("/transfer-wizard/sessions", response_model=TransferWizardSessionOut, status_code=201)
def post_transfer_wizard_session(body: TransferWizardStartIn, db: Session = Depends(get_db)):
    return start_wizard(db, regulation_code=body.regulation_code)


@router.get("/transfer-wizard/sessions/{session_id}", response_model=TransferWizardSessionOut)
def get_transfer_wizard_session(session_id: str, db: Session = Depends(get_db)):
    return get_wizard(db, session_id)


@router.patch("/transfer-wizard/sessions/{session_id}/step", response_model=TransferWizardSessionOut)
def patch_transfer_wizard_step(session_id: str, body: TransferWizardStepIn, db: Session = Depends(get_db)):
    return advance_wizard_step(
        db,
        session_id,
        step=body.step,
        destination_country=body.destination_country,
        mechanism=body.mechanism,
        processor_id=body.processor_id,
        processing_activity_id=body.processing_activity_id,
        document_ref=body.document_ref,
        adequacy_notes=body.adequacy_notes,
    )


@router.post("/transfer-wizard/sessions/{session_id}/complete", response_model=TransferRecordOut)
def post_transfer_wizard_complete(session_id: str, db: Session = Depends(get_db)):
    return complete_wizard(db, session_id)


@router.get("/webhook-deliveries", response_model=WebhookDeliveryListOut)
def get_webhook_deliveries(
    regulation_code: str | None = None,
    webhook_id: str | None = None,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items = list_webhook_deliveries(
        db, regulation_code=regulation_code, webhook_id=webhook_id, status_filter=status, limit=limit
    )
    return WebhookDeliveryListOut(items=[WebhookDeliveryOut.model_validate(i) for i in items], total=len(items))


@router.post("/webhooks/dispatch", response_model=WebhookDeliveryOut, status_code=201)
def post_webhook_dispatch(body: WebhookDispatchIn, db: Session = Depends(get_db)):
    row = enqueue_webhook_event(
        db,
        regulation_code=body.regulation_code,
        event_name=body.event_name,
        payload=body.payload,
        aggregate_id=body.aggregate_id,
    )
    if body.dispatch_now:
        return WebhookDeliveryOut.model_validate(dispatch_delivery(db, row.id))
    return WebhookDeliveryOut.model_validate(
        {
            "id": row.id,
            "webhook_id": row.webhook_id,
            "regulation_code": row.regulation_code,
            "event_name": row.event_name,
            "aggregate_id": row.aggregate_id,
            "payload": body.payload,
            "status": row.status,
            "attempt_count": row.attempt_count,
            "max_attempts": row.max_attempts,
            "last_status_code": row.last_status_code,
            "last_response_body": row.last_response_body,
            "last_attempt_at": row.last_attempt_at,
            "next_attempt_at": row.next_attempt_at,
            "delivered_at": row.delivered_at,
            "created_at": row.created_at,
        }
    )


@router.post("/webhook-deliveries/{delivery_id}/retry", response_model=WebhookDeliveryOut)
def post_webhook_delivery_retry(delivery_id: str, db: Session = Depends(get_db)):
    return WebhookDeliveryOut.model_validate(dispatch_delivery(db, delivery_id))


@router.post("/webhook-deliveries/process-pending", response_model=WebhookProcessOut)
def post_webhook_process_pending(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return process_pending_deliveries(db, limit=limit)


@router.get("/ecosystem/global-ops-bridge", response_model=GlobalOpsBridgeSummaryOut)
def get_global_ops_bridge(db: Session = Depends(get_db)):
    return global_ops_bridge_summary(db)


@router.post("/ecosystem/certifications/sync", response_model=GlobalOpsSyncOut)
def post_certifications_sync(
    player_code: str | None = None,
    db: Session = Depends(get_db),
):
    return sync_certifications_from_partner(db, player_code=player_code)


@router.get("/ecosystem/certifications", response_model=PlayerCertificationMirrorListOut)
def get_ecosystem_certifications(
    player_code: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
):
    items = list_certification_mirrors(db, player_code=player_code, limit=limit)
    return PlayerCertificationMirrorListOut(
        items=[PlayerCertificationMirrorOut.model_validate(i) for i in items],
        total=len(items),
    )

