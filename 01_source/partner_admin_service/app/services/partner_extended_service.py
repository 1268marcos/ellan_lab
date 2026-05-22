from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.partner_extended import (
    PartnerB2bInvoice,
    PartnerBillingLineItem,
    PartnerCommissionStructure,
    PartnerCreditNote,
    PartnerIntegrationHealth,
    PartnerOnboardingMilestone,
    PartnerOrderEventOutbox,
    PartnerPaymentHold,
    PartnerWebhookDelivery,
)
from app.models.webhook import PartnerWebhookEndpoint
from app.schemas.partner_extended import (
    B2bInvoiceListOut,
    B2bInvoiceOut,
    BillingLineItemListOut,
    BillingLineItemOut,
    CommissionListOut,
    CommissionOut,
    CreditNoteListOut,
    CreditNoteOut,
    IntegrationHealthListOut,
    IntegrationHealthOut,
    OnboardingListOut,
    OnboardingMilestoneOut,
    OnboardingPatchIn,
    OutboxEventListOut,
    OutboxEventOut,
    Partner360Out,
    PaymentHoldListOut,
    PaymentHoldOut,
    WebhookDeliveryListOut,
    WebhookDeliveryOut,
)
from app.services.crypto_util import new_id
from app.services.partner_domain_service import _resolve_partner


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


DEFAULT_MILESTONES = [
    ("KYC_VERIFIED", "KYC / dados fiscais", 10),
    ("CONTRACT_SIGNED", "Contrato comercial", 20),
    ("API_SANDBOX", "Credenciais sandbox", 30),
    ("WEBHOOK_TEST", "Webhook validado", 40),
    ("SERVICE_AREAS", "Áreas de cobertura", 50),
    ("BILLING_PLAN", "Plano de billing", 60),
    ("PROD_GO_LIVE", "Go-live produção", 70),
]


def ensure_onboarding(db: Session, partner_id: str, partner_type: str) -> None:
    _resolve_partner(db, partner_id)
    existing = db.query(PartnerOnboardingMilestone).filter(PartnerOnboardingMilestone.partner_id == partner_id).count()
    if existing:
        return
    now = _utcnow()
    for code, label, order in DEFAULT_MILESTONES:
        db.add(
            PartnerOnboardingMilestone(
                id=new_id(),
                partner_id=partner_id,
                partner_type=partner_type,
                milestone_code=code,
                milestone_label=label,
                status="DONE" if code in ("KYC_VERIFIED", "CONTRACT_SIGNED", "API_SANDBOX") else "PENDING",
                sort_order=order,
                completed_at=now if code in ("KYC_VERIFIED", "CONTRACT_SIGNED", "API_SANDBOX") else None,
                created_at=now,
                updated_at=now,
            )
        )
    db.commit()


def list_onboarding(db: Session, partner_id: str, partner_type: str = "ECOMMERCE") -> OnboardingListOut:
    _resolve_partner(db, partner_id)
    ensure_onboarding(db, partner_id, partner_type)
    rows = (
        db.query(PartnerOnboardingMilestone)
        .filter(PartnerOnboardingMilestone.partner_id == partner_id)
        .order_by(PartnerOnboardingMilestone.sort_order)
        .all()
    )
    done = sum(1 for r in rows if r.status == "DONE")
    pct = round((done / len(rows) * 100) if rows else 0, 1)
    items = [OnboardingMilestoneOut.model_validate(r) for r in rows]
    return OnboardingListOut(partner_id=partner_id, items=items, progress_pct=pct, total=len(items))


def patch_onboarding(
    db: Session, partner_id: str, milestone_id: str, body: OnboardingPatchIn
) -> OnboardingMilestoneOut:
    _resolve_partner(db, partner_id)
    row = db.get(PartnerOnboardingMilestone, milestone_id)
    if not row or row.partner_id != partner_id:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="milestone_not_found")
    now = _utcnow()
    row.status = body.status.upper()
    row.notes = body.notes
    if row.status == "DONE":
        row.completed_at = now
        row.completed_by = body.completed_by
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return OnboardingMilestoneOut.model_validate(row)


def list_webhook_deliveries(
    db: Session, partner_id: str, *, status: str | None = None, limit: int = 50
) -> WebhookDeliveryListOut:
    _resolve_partner(db, partner_id)
    endpoint_ids = [
        e.id
        for e in db.query(PartnerWebhookEndpoint)
        .filter(PartnerWebhookEndpoint.partner_id == partner_id)
        .all()
    ]
    if not endpoint_ids:
        return WebhookDeliveryListOut(partner_id=partner_id, items=[], total=0)
    q = db.query(PartnerWebhookDelivery).filter(PartnerWebhookDelivery.endpoint_id.in_(endpoint_ids))
    if status:
        q = q.filter(PartnerWebhookDelivery.status == status.upper())
    rows = q.order_by(PartnerWebhookDelivery.created_at.desc()).limit(limit).all()
    items = [WebhookDeliveryOut.model_validate(r) for r in rows]
    return WebhookDeliveryListOut(partner_id=partner_id, items=items, total=len(items))


def list_integration_health(db: Session, partner_id: str, *, limit: int = 20) -> IntegrationHealthListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerIntegrationHealth)
        .filter(PartnerIntegrationHealth.partner_id == partner_id)
        .order_by(PartnerIntegrationHealth.checked_at.desc())
        .limit(limit)
        .all()
    )
    items = [IntegrationHealthOut.model_validate(r) for r in rows]
    return IntegrationHealthListOut(partner_id=partner_id, items=items, total=len(items))


def record_health_probe(db: Session, partner_id: str, partner_type: str) -> IntegrationHealthOut:
    _resolve_partner(db, partner_id)
    endpoint = (
        db.query(PartnerWebhookEndpoint)
        .filter(PartnerWebhookEndpoint.partner_id == partner_id, PartnerWebhookEndpoint.active.is_(True))
        .first()
    )
    url = endpoint.url if endpoint else None
    status = "UP" if endpoint else "DEGRADED"
    row = PartnerIntegrationHealth(
        partner_id=partner_id,
        partner_type=partner_type,
        endpoint_url=url,
        status=status,
        latency_ms=42 if status == "UP" else None,
        http_status=200 if status == "UP" else None,
        checked_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return IntegrationHealthOut.model_validate(row)


def list_outbox(
    db: Session, partner_id: str, *, status: str | None = None, limit: int = 50
) -> OutboxEventListOut:
    _resolve_partner(db, partner_id)
    q = db.query(PartnerOrderEventOutbox).filter(PartnerOrderEventOutbox.partner_id == partner_id)
    if status:
        q = q.filter(PartnerOrderEventOutbox.status == status.upper())
    rows = q.order_by(PartnerOrderEventOutbox.created_at.desc()).limit(limit).all()
    items = [OutboxEventOut.model_validate(r) for r in rows]
    return OutboxEventListOut(partner_id=partner_id, items=items, total=len(items))


def list_invoices(db: Session, partner_id: str, *, status: str | None = None) -> B2bInvoiceListOut:
    _resolve_partner(db, partner_id)
    q = db.query(PartnerB2bInvoice).filter(PartnerB2bInvoice.partner_id == partner_id)
    if status:
        q = q.filter(PartnerB2bInvoice.status == status.upper())
    rows = q.order_by(PartnerB2bInvoice.created_at.desc()).all()
    items = [B2bInvoiceOut.model_validate(r) for r in rows]
    return B2bInvoiceListOut(partner_id=partner_id, items=items, total=len(items))


def list_billing_line_items(
    db: Session, partner_id: str, *, cycle_id: str | None = None
) -> BillingLineItemListOut:
    _resolve_partner(db, partner_id)
    q = db.query(PartnerBillingLineItem).filter(PartnerBillingLineItem.partner_id == partner_id)
    if cycle_id:
        q = q.filter(PartnerBillingLineItem.cycle_id == cycle_id)
    rows = q.order_by(PartnerBillingLineItem.id).all()
    items = [BillingLineItemOut.model_validate(r) for r in rows]
    return BillingLineItemListOut(partner_id=partner_id, cycle_id=cycle_id, items=items, total=len(items))


def list_credit_notes(db: Session, partner_id: str) -> CreditNoteListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerCreditNote)
        .filter(PartnerCreditNote.partner_id == partner_id)
        .order_by(PartnerCreditNote.created_at.desc())
        .all()
    )
    items = [CreditNoteOut.model_validate(r) for r in rows]
    return CreditNoteListOut(partner_id=partner_id, items=items, total=len(items))


def list_payment_holds(db: Session, partner_id: str) -> PaymentHoldListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerPaymentHold)
        .filter(PartnerPaymentHold.partner_id == partner_id)
        .order_by(PartnerPaymentHold.created_at.desc())
        .all()
    )
    items = [PaymentHoldOut.model_validate(r) for r in rows]
    return PaymentHoldListOut(partner_id=partner_id, items=items, total=len(items))


def list_commissions(db: Session, partner_id: str) -> CommissionListOut:
    _resolve_partner(db, partner_id)
    rows = (
        db.query(PartnerCommissionStructure)
        .filter(PartnerCommissionStructure.partner_id == partner_id)
        .order_by(PartnerCommissionStructure.effective_from.desc())
        .all()
    )
    items = [CommissionOut.model_validate(r) for r in rows]
    return CommissionListOut(partner_id=partner_id, items=items, total=len(items))


def get_partner_360(db: Session, partner_id: str, partner_type: str = "ECOMMERCE") -> Partner360Out:
    _resolve_partner(db, partner_id)
    from app.models.partner_domain import PartnerBillingCycle, PartnerSettlementBatch, PartnerSlaAgreement

    settlements_draft = (
        db.query(PartnerSettlementBatch)
        .filter(PartnerSettlementBatch.partner_id == partner_id, PartnerSettlementBatch.status == "DRAFT")
        .count()
    )
    settlements_paid = (
        db.query(PartnerSettlementBatch)
        .filter(PartnerSettlementBatch.partner_id == partner_id, PartnerSettlementBatch.status == "PAID")
        .count()
    )
    open_cycles = (
        db.query(PartnerBillingCycle)
        .filter(PartnerBillingCycle.partner_id == partner_id, PartnerBillingCycle.status.in_(("OPEN", "REVIEW")))
        .count()
    )
    pending_invoices = (
        db.query(PartnerB2bInvoice)
        .filter(PartnerB2bInvoice.partner_id == partner_id, PartnerB2bInvoice.status.in_(("DRAFT", "ISSUED", "SENT")))
        .count()
    )
    pending_outbox = (
        db.query(PartnerOrderEventOutbox)
        .filter(PartnerOrderEventOutbox.partner_id == partner_id, PartnerOrderEventOutbox.status == "PENDING")
        .count()
    )
    since = _utcnow() - timedelta(hours=24)
    endpoint_ids = [e.id for e in db.query(PartnerWebhookEndpoint).filter(PartnerWebhookEndpoint.partner_id == partner_id)]
    webhook_failures = 0
    if endpoint_ids:
        webhook_failures = (
            db.query(PartnerWebhookDelivery)
            .filter(
                PartnerWebhookDelivery.endpoint_id.in_(endpoint_ids),
                PartnerWebhookDelivery.status.in_(("FAILED", "DEAD_LETTER")),
                PartnerWebhookDelivery.created_at >= since,
            )
            .count()
        )
    last_health = (
        db.query(PartnerIntegrationHealth)
        .filter(PartnerIntegrationHealth.partner_id == partner_id)
        .order_by(PartnerIntegrationHealth.checked_at.desc())
        .first()
    )
    onboarding = list_onboarding(db, partner_id, partner_type)
    sla_active = (
        db.query(PartnerSlaAgreement)
        .filter(PartnerSlaAgreement.partner_id == partner_id, PartnerSlaAgreement.is_active.is_(True))
        .count()
        > 0
    )
    from app.models.partner_ecosystem import PartnerEcosystemLink, PartnerEcosystemPlayer

    eco_total = (
        db.query(PartnerEcosystemLink).filter(PartnerEcosystemLink.partner_id == partner_id).count()
    )
    priority_links = (
        db.query(PartnerEcosystemLink)
        .join(PartnerEcosystemPlayer, PartnerEcosystemLink.ecosystem_player_id == PartnerEcosystemPlayer.id)
        .filter(
            PartnerEcosystemLink.partner_id == partner_id,
            PartnerEcosystemPlayer.global_tier == "PRIORITY",
        )
        .count()
    )
    return Partner360Out(
        partner_id=partner_id,
        partner_type=partner_type,
        settlements_draft=settlements_draft,
        settlements_paid=settlements_paid,
        open_billing_cycles=open_cycles,
        pending_invoices=pending_invoices,
        pending_outbox=pending_outbox,
        webhook_failures_24h=webhook_failures,
        integration_status=last_health.status if last_health else "UNKNOWN",
        onboarding_progress_pct=onboarding.progress_pct,
        sla_active=sla_active,
        ecosystem_links=eco_total,
        ecosystem_priority_links=priority_links,
    )
