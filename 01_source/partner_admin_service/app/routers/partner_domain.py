from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.partner_domain import (
    BillingCycleListOut,
    BillingPlanListOut,
    PartnerStoreCreateIn,
    PartnerStoreListOut,
    PartnerStoreOut,
    PerformanceListOut,
    ServiceAreaCreateIn,
    ServiceAreaListOut,
    ServiceAreaOut,
    SettlementApproveIn,
    SettlementBatchListOut,
    SettlementBatchOut,
    SettlementGenerateIn,
    SettlementItemListOut,
    SlaAgreementCreateIn,
    SlaAgreementListOut,
    SlaAgreementOut,
    StatusHistoryListOut,
)
from app.schemas.partner_extended import (
    B2bInvoiceListOut,
    BillingLineItemListOut,
    CommissionListOut,
    CreditNoteListOut,
    IntegrationHealthListOut,
    IntegrationHealthOut,
    OnboardingListOut,
    OnboardingMilestoneOut,
    OnboardingPatchIn,
    OutboxEventListOut,
    Partner360Out,
    PaymentHoldListOut,
    WebhookDeliveryListOut,
)
from app.services import partner_domain_service as svc
from app.services import partner_extended_service as ext

router = APIRouter(prefix="/partners", tags=["partner-domain"])


@router.get("/{partner_id}/settlements", response_model=SettlementBatchListOut)
def list_settlements(
    partner_id: str,
    status: str | None = Query(None),
    from_period_start: date | None = Query(None),
    to_period_end: date | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> SettlementBatchListOut:
    return svc.list_settlements(
        db,
        partner_id,
        status_filter=status,
        from_period_start=from_period_start,
        to_period_end=to_period_end,
        limit=limit,
    )


@router.post("/{partner_id}/settlements/generate", response_model=SettlementBatchOut)
def generate_settlement(
    partner_id: str, body: SettlementGenerateIn, db: Session = Depends(get_db)
) -> SettlementBatchOut:
    return svc.generate_settlement(db, partner_id, body)


@router.patch("/{partner_id}/settlements/{batch_id}/approve", response_model=SettlementBatchOut)
def approve_settlement(
    partner_id: str,
    batch_id: str,
    body: SettlementApproveIn,
    db: Session = Depends(get_db),
) -> SettlementBatchOut:
    return svc.approve_settlement(db, partner_id, batch_id, body)


@router.patch("/{partner_id}/settlements/{batch_id}/pay", response_model=SettlementBatchOut)
def pay_settlement(
    partner_id: str, batch_id: str, db: Session = Depends(get_db)
) -> SettlementBatchOut:
    return svc.pay_settlement(db, partner_id, batch_id)


@router.get("/{partner_id}/settlements/{batch_id}/items", response_model=SettlementItemListOut)
def list_settlement_items(
    partner_id: str,
    batch_id: str,
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> SettlementItemListOut:
    return svc.list_settlement_items(db, partner_id, batch_id, limit=limit, offset=offset)


@router.get("/{partner_id}/performance", response_model=PerformanceListOut)
def list_performance(
    partner_id: str, limit: int = Query(6, ge=1, le=24), db: Session = Depends(get_db)
) -> PerformanceListOut:
    return svc.list_performance(db, partner_id, limit=limit)


@router.get("/{partner_id}/service-areas", response_model=ServiceAreaListOut)
def list_service_areas(
    partner_id: str,
    only_active: bool = Query(True),
    limit: int = Query(200, ge=1, le=500),
    db: Session = Depends(get_db),
) -> ServiceAreaListOut:
    return svc.list_service_areas(db, partner_id, only_active=only_active, limit=limit)


@router.post("/{partner_id}/service-areas", response_model=ServiceAreaOut)
def create_service_area(
    partner_id: str, body: ServiceAreaCreateIn, db: Session = Depends(get_db)
) -> ServiceAreaOut:
    return svc.create_service_area(db, partner_id, body)


@router.get("/{partner_id}/billing-plans", response_model=BillingPlanListOut)
def list_billing_plans(partner_id: str, db: Session = Depends(get_db)) -> BillingPlanListOut:
    return svc.list_billing_plans(db, partner_id)


@router.get("/{partner_id}/billing-cycles", response_model=BillingCycleListOut)
def list_billing_cycles(
    partner_id: str, status: str | None = Query(None), db: Session = Depends(get_db)
) -> BillingCycleListOut:
    return svc.list_billing_cycles(db, partner_id, status_filter=status)


@router.get("/{partner_id}/sla-agreements", response_model=SlaAgreementListOut)
def list_sla_agreements(partner_id: str, db: Session = Depends(get_db)) -> SlaAgreementListOut:
    return svc.list_sla_agreements(db, partner_id)


@router.post("/{partner_id}/sla-agreements", response_model=SlaAgreementOut)
def create_sla_agreement(
    partner_id: str, body: SlaAgreementCreateIn, db: Session = Depends(get_db)
) -> SlaAgreementOut:
    return svc.create_sla_agreement(db, partner_id, body)


@router.get("/{partner_id}/status-history", response_model=StatusHistoryListOut)
def list_status_history(
    partner_id: str, limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db)
) -> StatusHistoryListOut:
    return svc.list_status_history(db, partner_id, limit=limit)


@router.get("/{partner_id}/360", response_model=Partner360Out)
def partner_360(
    partner_id: str,
    partner_type: str = Query("ECOMMERCE"),
    db: Session = Depends(get_db),
) -> Partner360Out:
    return ext.get_partner_360(db, partner_id, partner_type)


@router.get("/{partner_id}/onboarding", response_model=OnboardingListOut)
def list_onboarding(
    partner_id: str,
    partner_type: str = Query("ECOMMERCE"),
    db: Session = Depends(get_db),
) -> OnboardingListOut:
    return ext.list_onboarding(db, partner_id, partner_type)


@router.patch("/{partner_id}/onboarding/{milestone_id}", response_model=OnboardingMilestoneOut)
def patch_onboarding(
    partner_id: str,
    milestone_id: str,
    body: OnboardingPatchIn,
    db: Session = Depends(get_db),
) -> OnboardingMilestoneOut:
    return ext.patch_onboarding(db, partner_id, milestone_id, body)


@router.get("/{partner_id}/webhook-deliveries", response_model=WebhookDeliveryListOut)
def list_webhook_deliveries(
    partner_id: str,
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> WebhookDeliveryListOut:
    return ext.list_webhook_deliveries(db, partner_id, status=status, limit=limit)


@router.get("/{partner_id}/integration-health", response_model=IntegrationHealthListOut)
def list_integration_health(
    partner_id: str, limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)
) -> IntegrationHealthListOut:
    return ext.list_integration_health(db, partner_id, limit=limit)


@router.post("/{partner_id}/integration-health/probe", response_model=IntegrationHealthOut)
def probe_integration_health(
    partner_id: str,
    partner_type: str = Query("ECOMMERCE"),
    db: Session = Depends(get_db),
) -> IntegrationHealthOut:
    return ext.record_health_probe(db, partner_id, partner_type)


@router.get("/{partner_id}/outbox", response_model=OutboxEventListOut)
def list_outbox(
    partner_id: str,
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> OutboxEventListOut:
    return ext.list_outbox(db, partner_id, status=status, limit=limit)


@router.get("/{partner_id}/invoices", response_model=B2bInvoiceListOut)
def list_invoices(
    partner_id: str, status: str | None = Query(None), db: Session = Depends(get_db)
) -> B2bInvoiceListOut:
    return ext.list_invoices(db, partner_id, status=status)


@router.get("/{partner_id}/billing-line-items", response_model=BillingLineItemListOut)
def list_billing_line_items(
    partner_id: str, cycle_id: str | None = Query(None), db: Session = Depends(get_db)
) -> BillingLineItemListOut:
    return ext.list_billing_line_items(db, partner_id, cycle_id=cycle_id)


@router.get("/{partner_id}/credit-notes", response_model=CreditNoteListOut)
def list_credit_notes(partner_id: str, db: Session = Depends(get_db)) -> CreditNoteListOut:
    return ext.list_credit_notes(db, partner_id)


@router.get("/{partner_id}/payment-holds", response_model=PaymentHoldListOut)
def list_payment_holds(partner_id: str, db: Session = Depends(get_db)) -> PaymentHoldListOut:
    return ext.list_payment_holds(db, partner_id)


@router.get("/{partner_id}/commissions", response_model=CommissionListOut)
def list_commissions(partner_id: str, db: Session = Depends(get_db)) -> CommissionListOut:
    return ext.list_commissions(db, partner_id)
