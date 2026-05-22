from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.marketplace_integration import MarketplaceSyncAuditLog
from app.schemas.marketplace_extended import (
    CapabilityWebhookIn,
    CapabilityWebhookListOut,
    CapabilityWebhookOut,
    IntegrationHubSummaryOut,
    IntegrationIncidentListOut,
    IntegrationIncidentOut,
    IntegrationReadinessListOut,
    IntegrationReadinessOut,
    MarketplaceCertificationOut,
    CapabilityWebhookDeliveryMktOut,
    MarketplaceCorridorSlaOut,
    MarketplaceGlobalCorridorOut,
    MarketplaceGlobalOpsSummaryOut,
    MarketplaceCorridorStepOut,
    ReadinessAlertListOut,
    ReadinessAlertOut,
    SimulateScoreDropIn,
    SyncAuditLogListOut,
    SyncAuditLogOut,
)
from app.services import (
    capability_webhook_service,
    integration_readiness_service,
    marketplace_global_ops_service,
    readiness_alert_service,
)

router = APIRouter(tags=["integration-hub"])


def _readiness_out(row) -> IntegrationReadinessOut:
    try:
        blockers = json.loads(row.blockers_json or "[]")
    except json.JSONDecodeError:
        blockers = []
    return IntegrationReadinessOut(
        channel_partner_id=row.channel_partner_id,
        partner_code=row.partner_code,
        score_total=float(row.score_total),
        score_capabilities=float(row.score_capabilities),
        score_api=float(row.score_api),
        score_operations=float(row.score_operations),
        readiness_band=row.readiness_band,
        blockers=blockers,
        ml_network_code=row.ml_network_code,
        computed_at=row.computed_at,
    )


@router.get("/integration-hub/summary", response_model=IntegrationHubSummaryOut)
def integration_hub_summary(db: Session = Depends(get_db)) -> IntegrationHubSummaryOut:
    return IntegrationHubSummaryOut(**integration_readiness_service.hub_summary(db))


@router.post("/integration-readiness/recompute")
def recompute_integration_readiness(
    actor_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    return integration_readiness_service.recompute_all_readiness(db, actor_id=actor_id)


@router.get("/integration-readiness", response_model=IntegrationReadinessListOut)
def list_integration_readiness(
    band: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> IntegrationReadinessListOut:
    rows = integration_readiness_service.list_readiness(db, band=band, limit=limit)
    items = [_readiness_out(r) for r in rows]
    return IntegrationReadinessListOut(items=items, total=len(items))


@router.get("/integration-incidents", response_model=IntegrationIncidentListOut)
def list_integration_incidents(
    open_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> IntegrationIncidentListOut:
    rows = integration_readiness_service.list_incidents(db, open_only=open_only)
    items = [IntegrationIncidentOut.model_validate(r) for r in rows]
    return IntegrationIncidentListOut(items=items, total=len(items))


@router.post("/integration-incidents/seed-demo")
def seed_integration_incidents(db: Session = Depends(get_db)) -> dict:
    n = integration_readiness_service.seed_demo_incidents(db)
    db.commit()
    return {"inserted": n}


@router.get("/readiness-alerts", response_model=ReadinessAlertListOut)
def list_readiness_alerts(
    open_only: bool = Query(True),
    db: Session = Depends(get_db),
) -> ReadinessAlertListOut:
    rows = readiness_alert_service.list_readiness_alerts(db, open_only=open_only)
    items = [ReadinessAlertOut.model_validate(r) for r in rows]
    return ReadinessAlertListOut(items=items, total=len(items))


@router.post("/readiness-alerts/{alert_id}/acknowledge", response_model=ReadinessAlertOut)
def acknowledge_readiness_alert(alert_id: str, db: Session = Depends(get_db)) -> ReadinessAlertOut:
    return ReadinessAlertOut.model_validate(readiness_alert_service.acknowledge_alert(db, alert_id))


@router.post("/integration-readiness/simulate-drop")
def simulate_score_drop(body: SimulateScoreDropIn, db: Session = Depends(get_db)) -> dict:
    from app.models.marketplace_integration import MarketplaceIntegrationReadiness

    row = (
        db.query(MarketplaceIntegrationReadiness)
        .filter(MarketplaceIntegrationReadiness.partner_code == body.partner_code.upper())
        .first()
    )
    if not row:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="readiness_not_found")
    prev_score = float(row.score_total)
    prev_band = row.readiness_band
    stats = readiness_alert_service.record_score_and_check_alerts(
        db,
        channel_partner_id=row.channel_partner_id,
        partner_code=row.partner_code,
        previous_score=prev_score,
        previous_band=prev_band,
        new_score=body.new_score,
        new_band="BLOCKED" if body.new_score < 25 else "PLANNED",
    )
    row.score_total = body.new_score
    row.readiness_band = "BLOCKED" if body.new_score < 25 else row.readiness_band
    db.commit()
    return {"partner_code": row.partner_code, "previous_score": prev_score, "new_score": body.new_score, **stats}


@router.get("/capability-webhooks", response_model=CapabilityWebhookListOut)
def list_capability_webhooks(
    channel_partner_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> CapabilityWebhookListOut:
    import json

    rows = capability_webhook_service.list_capability_webhooks(db, channel_partner_id)
    items = []
    for r in rows:
        try:
            events = json.loads(r.event_types_json or "[]")
        except json.JSONDecodeError:
            events = []
        items.append(
            CapabilityWebhookOut(
                id=r.id,
                channel_partner_id=r.channel_partner_id,
                partner_code=r.partner_code,
                capability_code=r.capability_code,
                url=r.url,
                active=r.active,
                event_types=events,
                last_http_status=r.last_http_status,
                last_delivered_at=r.last_delivered_at,
                last_error=r.last_error,
            )
        )
    return CapabilityWebhookListOut(items=items, total=len(items))


@router.put("/capability-webhooks", response_model=CapabilityWebhookOut)
def upsert_capability_webhook(body: CapabilityWebhookIn, db: Session = Depends(get_db)) -> CapabilityWebhookOut:
    import json

    row = capability_webhook_service.configure_capability_webhook(
        db,
        channel_partner_id=body.channel_partner_id,
        capability_code=body.capability_code,
        url=body.url,
        secret=body.secret,
        events=body.events,
        active=body.active,
    )
    events = json.loads(row.event_types_json or "[]")
    return CapabilityWebhookOut(
        id=row.id,
        channel_partner_id=row.channel_partner_id,
        partner_code=row.partner_code,
        capability_code=row.capability_code,
        url=row.url,
        active=row.active,
        event_types=events,
        last_http_status=row.last_http_status,
        last_delivered_at=row.last_delivered_at,
        last_error=row.last_error,
    )


@router.post("/capability-webhooks/{webhook_id}/test")
def test_capability_webhook(webhook_id: str, db: Session = Depends(get_db)) -> dict:
    return capability_webhook_service.test_capability_webhook(db, webhook_id)


@router.post("/capability-webhooks/seed-demo")
def seed_capability_webhooks_demo(db: Session = Depends(get_db)) -> dict:
    n = readiness_alert_service.seed_demo_capability_webhooks(db)
    return {"inserted": n}


@router.post("/capability-webhooks/seed-from-catalog")
def seed_capability_webhooks_from_catalog(db: Session = Depends(get_db)) -> dict:
    return readiness_alert_service.seed_capability_webhooks_from_catalog(db)


@router.get("/sync-audit-log", response_model=SyncAuditLogListOut)
def list_sync_audit_log(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> SyncAuditLogListOut:
    rows = (
        db.query(MarketplaceSyncAuditLog)
        .order_by(MarketplaceSyncAuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
    items = [SyncAuditLogOut.model_validate(r) for r in rows]
    return SyncAuditLogListOut(items=items, total=len(items))


@router.get("/global-ops/summary", response_model=MarketplaceGlobalOpsSummaryOut)
def marketplace_global_ops_summary(db: Session = Depends(get_db)) -> MarketplaceGlobalOpsSummaryOut:
    return MarketplaceGlobalOpsSummaryOut(**marketplace_global_ops_service.global_ops_summary(db))


@router.post("/global-ops/seed")
def seed_marketplace_global_ops(db: Session = Depends(get_db)) -> dict:
    return marketplace_global_ops_service.seed_global_ops(db)


@router.get("/global-ops/certifications", response_model=list[MarketplaceCertificationOut])
def list_marketplace_certifications(
    partner_code: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[MarketplaceCertificationOut]:
    return [
        MarketplaceCertificationOut.model_validate(r)
        for r in marketplace_global_ops_service.list_certifications(db, partner_code=partner_code)
    ]


@router.get("/global-ops/corridors", response_model=list[MarketplaceGlobalCorridorOut])
def list_marketplace_corridors(
    origin: str | None = Query(None),
    dest: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[MarketplaceGlobalCorridorOut]:
    out: list[MarketplaceGlobalCorridorOut] = []
    for row in marketplace_global_ops_service.list_corridors(db, origin=origin, dest=dest):
        steps = [
            MarketplaceCorridorStepOut.model_validate(s)
            for s in marketplace_global_ops_service.list_corridor_steps(db, row.id)
        ]
        base = MarketplaceGlobalCorridorOut.model_validate(row)
        out.append(base.model_copy(update={"steps": steps}))
    return out


@router.get("/global-ops/corridor-sla", response_model=list[MarketplaceCorridorSlaOut])
def list_marketplace_corridor_sla(
    compliance_status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> list[MarketplaceCorridorSlaOut]:
    return [
        MarketplaceCorridorSlaOut.model_validate(r)
        for r in marketplace_global_ops_service.list_corridor_sla(db, compliance_status=compliance_status)
    ]


@router.post("/global-ops/certifications/mirror")
def mirror_marketplace_certifications(db: Session = Depends(get_db)) -> dict:
    out = marketplace_global_ops_service.mirror_certifications_from_partner(db)
    db.commit()
    return out


@router.get("/capability-webhooks/deliveries", response_model=list[CapabilityWebhookDeliveryMktOut])
def list_mkt_webhook_deliveries(
    status: str | None = Query(None),
    webhook_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[CapabilityWebhookDeliveryMktOut]:
    rows = capability_webhook_service.list_deliveries(db, status=status, webhook_id=webhook_id, limit=limit)
    return [CapabilityWebhookDeliveryMktOut.model_validate(r) for r in rows]


@router.post("/capability-webhooks/deliveries/{delivery_id}/replay", response_model=CapabilityWebhookDeliveryMktOut)
def replay_mkt_delivery(delivery_id: str, db: Session = Depends(get_db)) -> CapabilityWebhookDeliveryMktOut:
    d = capability_webhook_service.replay_delivery(db, delivery_id)
    return CapabilityWebhookDeliveryMktOut.model_validate(d)


@router.post("/capability-webhooks/deliveries/replay-dead-letter")
def replay_mkt_dead_letter_batch(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    return capability_webhook_service.replay_dead_letter_batch(db, limit=limit)
