from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.data.world_locker_payment_players import PAYMENT_PRIORITY_CODES
from app.models.domain_hub import PaymentCrossDomainEvent, PaymentDomainObligation, PaymentExternalReference
from app.models.value_features import (
    PaymentIntegrationIncident,
    PaymentIntegrationMilestone,
    PaymentRoutingRule,
    PaymentSettlementCorridor,
)
from app.models.cross_domain import (
    PartnerPaymentHold,
    PaymentEcosystemPlayer,
    PaymentEcosystemSegment,
    PaymentOrderContext,
    PaymentPlayerCountryCoverage,
    PaymentPlayerIntegration,
    PaymentPlayerRelation,
    PaymentReconciliationBatch,
    WebhookDelivery,
)
from app.models.payments import (
    GatewayEvent,
    Payment,
    PaymentInstruction,
    PaymentSplit,
    PaymentTransaction,
)
from app.schemas.cross_domain import (
    PaymentContextPlayerLinkOut,
    PaymentIntelligenceSummary,
    PaymentOrderContextOut,
    PaymentOrderGraphOut,
)
from app.services import cross_domain_service, domain_hub_service


def build_summary(db: Session) -> PaymentIntelligenceSummary:
    tx_total = db.query(PaymentTransaction).count()
    tx_approved = (
        db.query(PaymentTransaction).filter(PaymentTransaction.status == "APPROVED").count()
    )
    recon_pending = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.reconciliation_status == "PENDING")
        .count()
    )
    open_batches = (
        db.query(PaymentReconciliationBatch)
        .filter(PaymentReconciliationBatch.status == "OPEN")
        .count()
    )
    wh_pending = db.query(WebhookDelivery).filter(WebhookDelivery.status == "PENDING").count()
    holds_cents = cross_domain_service.holds_active_cents(db)
    players_total = db.query(PaymentEcosystemPlayer).filter(PaymentEcosystemPlayer.is_active.is_(True)).count()
    players_live = (
        db.query(PaymentEcosystemPlayer)
        .filter(
            PaymentEcosystemPlayer.integration_status == "LIVE",
            PaymentEcosystemPlayer.is_active.is_(True),
        )
        .count()
    )
    priority_live = (
        db.query(PaymentEcosystemPlayer)
        .filter(
            PaymentEcosystemPlayer.code.in_(list(PAYMENT_PRIORITY_CODES)),
            PaymentEcosystemPlayer.integration_status == "LIVE",
            PaymentEcosystemPlayer.is_active.is_(True),
        )
        .count()
    )
    relations_total = (
        db.query(PaymentPlayerRelation).filter(PaymentPlayerRelation.is_active.is_(True)).count()
    )
    orders_ctx = db.query(PaymentOrderContext).count()
    segments_raw = (
        db.query(PaymentEcosystemPlayer.segment, func.count(PaymentEcosystemPlayer.id))
        .filter(PaymentEcosystemPlayer.is_active.is_(True))
        .group_by(PaymentEcosystemPlayer.segment)
        .all()
    )
    segments = {str(seg): int(cnt) for seg, cnt in segments_raw}
    seg_defined = (
        db.query(PaymentEcosystemSegment).filter(PaymentEcosystemSegment.is_active.is_(True)).count()
    )
    coverage_rows = db.query(PaymentPlayerCountryCoverage).count()
    integ_prod = (
        db.query(PaymentPlayerIntegration)
        .filter(PaymentPlayerIntegration.production_ready.is_(True))
        .count()
    )
    avg_readiness = (
        db.query(func.avg(PaymentPlayerIntegration.readiness_score)).scalar() or 0.0
    )
    open_incidents = (
        db.query(PaymentIntegrationIncident)
        .filter(PaymentIntegrationIncident.status == "OPEN")
        .count()
    )
    active_corridors = (
        db.query(PaymentSettlementCorridor)
        .filter(PaymentSettlementCorridor.is_active.is_(True))
        .count()
    )
    routing_active = (
        db.query(PaymentRoutingRule).filter(PaymentRoutingRule.is_active.is_(True)).count()
    )
    milestones_ip = (
        db.query(PaymentIntegrationMilestone)
        .filter(PaymentIntegrationMilestone.status == "IN_PROGRESS")
        .count()
    )
    ext_refs = db.query(PaymentExternalReference).count()
    pend_obs = (
        db.query(PaymentDomainObligation)
        .filter(PaymentDomainObligation.status == "PENDING")
        .count()
    )
    block_obs = (
        db.query(PaymentDomainObligation)
        .filter(
            PaymentDomainObligation.status == "PENDING",
            PaymentDomainObligation.blocking_payment.is_(True),
        )
        .count()
    )
    gaps_n = domain_hub_service.scan_cross_domain_gaps(db, limit=30).total
    ev_pending = (
        db.query(PaymentCrossDomainEvent)
        .filter(PaymentCrossDomainEvent.status == "PENDING")
        .count()
    )
    return PaymentIntelligenceSummary(
        transactions_total=tx_total,
        transactions_approved=tx_approved,
        reconciliation_pending=recon_pending,
        open_batches=open_batches,
        webhook_pending=wh_pending,
        holds_active_cents=holds_cents,
        ecosystem_players_live=players_live,
        ecosystem_players_total=players_total,
        player_relations_total=relations_total,
        priority_players_live=priority_live,
        orders_with_context=orders_ctx,
        segments=segments,
        priority_player_codes=sorted(PAYMENT_PRIORITY_CODES),
        ecosystem_segments_defined=seg_defined,
        country_coverage_rows=coverage_rows,
        integrations_production_ready=integ_prod,
        integrations_avg_readiness=round(float(avg_readiness), 1),
        open_integration_incidents=open_incidents,
        active_settlement_corridors=active_corridors,
        routing_rules_active=routing_active,
        milestones_in_progress=milestones_ip,
        external_references_total=ext_refs,
        pending_domain_obligations=pend_obs,
        blocking_domain_obligations=block_obs,
        cross_domain_gaps_detected=gaps_n,
        cross_domain_events_pending=ev_pending,
    )


def _serialize(model) -> dict:
    if model is None:
        return {}
    out = {}
    for col in model.__table__.columns:
        val = getattr(model, col.name)
        if hasattr(val, "isoformat"):
            val = val.isoformat()
        out[col.name] = val
    return out


def build_order_graph(db: Session, order_id: str) -> PaymentOrderGraphOut:
    from app.models.cross_domain import PaymentContextPlayerLink

    ctx = cross_domain_service.get_order_context_by_order(db, order_id)
    ctx_out = None
    if ctx:
        links = (
            db.query(PaymentContextPlayerLink)
            .filter(PaymentContextPlayerLink.order_context_id == ctx.id)
            .all()
        )
        ctx_out = PaymentOrderContextOut.model_validate(ctx)
        ctx_out.player_links = [PaymentContextPlayerLinkOut.model_validate(l) for l in links]
    txs = db.query(PaymentTransaction).filter(PaymentTransaction.order_id == order_id).all()
    inst = db.query(PaymentInstruction).filter(PaymentInstruction.order_id == order_id).all()
    splits = db.query(PaymentSplit).filter(PaymentSplit.order_id == order_id).all()
    pays = db.query(Payment).filter(Payment.order_id == order_id).all()
    holds = db.query(PartnerPaymentHold).filter(PartnerPaymentHold.order_id == order_id).all()
    events = db.query(GatewayEvent).filter(GatewayEvent.order_id == order_id).all()
    return PaymentOrderGraphOut(
        order_id=order_id,
        context=ctx_out,
        transactions=[_serialize(t) for t in txs],
        instructions=[_serialize(i) for i in inst],
        splits=[_serialize(s) for s in splits],
        payments=[_serialize(p) for p in pays],
        holds=[_serialize(h) for h in holds],
        gateway_events=[_serialize(e) for e in events],
    )
