from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.marketplace_extended import MarketplaceChannelPartner
from app.schemas.marketplace_seller_operations import (
    ChannelSkuMapCreateIn,
    ChannelSkuMapListOut,
    ChannelSkuMapOut,
    FulfillmentPreferenceOut,
    FulfillmentPreferenceUpsertIn,
    InventoryAllocationListOut,
    InventoryAllocationOut,
    InventoryAllocationUpsertIn,
    NotificationSubCreateIn,
    NotificationSubListOut,
    NotificationSubOut,
    OnboardingTaskCompleteIn,
    OnboardingTaskListOut,
    OnboardingTaskOut,
    PricingRuleCreateIn,
    PricingRuleListOut,
    PricingRuleOut,
    ReturnPolicyCreateIn,
    ReturnPolicyListOut,
    ReturnPolicyOut,
    SellerOperationsSummaryOut,
)
from app.services import seller_operations_service

router = APIRouter(tags=["seller-operations"])


def _pc(db: Session) -> dict[str, str]:
    return {p.id: p.code for p in db.query(MarketplaceChannelPartner).all()}


@router.post("/seller-operations/seed")
def seed_seller_ops(
    seller_id: str = "mk-seller-demo-001",
    db: Session = Depends(get_db),
) -> dict:
    return seller_operations_service.seed_seller_operations(db, seller_id)


@router.get("/sellers/{seller_id}/operations-summary", response_model=SellerOperationsSummaryOut)
def operations_summary(seller_id: str, db: Session = Depends(get_db)) -> SellerOperationsSummaryOut:
    return SellerOperationsSummaryOut.model_validate(seller_operations_service.seller_operations_summary(db, seller_id))


@router.get("/sellers/{seller_id}/onboarding-tasks", response_model=OnboardingTaskListOut)
def list_onboarding(seller_id: str, db: Session = Depends(get_db)) -> OnboardingTaskListOut:
    data = seller_operations_service.list_onboarding(db, seller_id)
    tasks = [OnboardingTaskOut.model_validate(t) for t in data["tasks"]]
    return OnboardingTaskListOut(
        tasks=tasks,
        total=data["total"],
        completed_count=data["completed_count"],
        progress_pct=data["progress_pct"],
    )


@router.post("/onboarding-tasks/{task_id}/complete", response_model=OnboardingTaskOut)
def complete_task(task_id: str, body: OnboardingTaskCompleteIn, db: Session = Depends(get_db)) -> OnboardingTaskOut:
    return OnboardingTaskOut.model_validate(seller_operations_service.complete_onboarding_task(db, task_id, body))


@router.get("/sellers/{seller_id}/channel-sku-maps", response_model=ChannelSkuMapListOut)
def list_sku_maps(seller_id: str, db: Session = Depends(get_db)) -> ChannelSkuMapListOut:
    rows = seller_operations_service.list_sku_maps(db, seller_id)
    return ChannelSkuMapListOut(maps=[ChannelSkuMapOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/seller-channel-sku-maps", response_model=ChannelSkuMapOut, status_code=status.HTTP_201_CREATED)
def create_sku_map(body: ChannelSkuMapCreateIn, db: Session = Depends(get_db)) -> ChannelSkuMapOut:
    row = seller_operations_service.create_sku_map(db, body)
    return ChannelSkuMapOut.model_validate(
        {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "partner_code": _pc(db).get(row.channel_partner_id)}
    )


@router.get("/sellers/{seller_id}/pricing-rules", response_model=PricingRuleListOut)
def list_pricing(seller_id: str, db: Session = Depends(get_db)) -> PricingRuleListOut:
    rows = seller_operations_service.list_pricing_rules(db, seller_id)
    return PricingRuleListOut(rules=[PricingRuleOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/seller-pricing-rules", response_model=PricingRuleOut, status_code=status.HTTP_201_CREATED)
def create_pricing(body: PricingRuleCreateIn, db: Session = Depends(get_db)) -> PricingRuleOut:
    row = seller_operations_service.create_pricing_rule(db, body)
    return PricingRuleOut.model_validate(
        {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "partner_code": _pc(db).get(row.channel_partner_id)}
    )


@router.get("/sellers/{seller_id}/pricing-preview")
def pricing_preview(
    seller_id: str,
    internal_sku: str = Query(...),
    base_price_cents: int = Query(...),
    channel_partner_id: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict:
    return seller_operations_service.apply_pricing_preview(db, seller_id, internal_sku, base_price_cents, channel_partner_id)


@router.get("/sellers/{seller_id}/return-policies", response_model=ReturnPolicyListOut)
def list_returns(seller_id: str, db: Session = Depends(get_db)) -> ReturnPolicyListOut:
    rows = seller_operations_service.list_return_policies(db, seller_id)
    return ReturnPolicyListOut(policies=[ReturnPolicyOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/seller-return-policies", response_model=ReturnPolicyOut, status_code=status.HTTP_201_CREATED)
def create_return(body: ReturnPolicyCreateIn, db: Session = Depends(get_db)) -> ReturnPolicyOut:
    return ReturnPolicyOut.model_validate(seller_operations_service.create_return_policy(db, body))


@router.get("/sellers/{seller_id}/notification-subscriptions", response_model=NotificationSubListOut)
def list_notifs(seller_id: str, db: Session = Depends(get_db)) -> NotificationSubListOut:
    rows = seller_operations_service.list_notifications(db, seller_id)
    return NotificationSubListOut(subscriptions=[NotificationSubOut.model_validate(r) for r in rows], total=len(rows))


@router.post("/seller-notification-subscriptions", response_model=NotificationSubOut, status_code=status.HTTP_201_CREATED)
def create_notif(body: NotificationSubCreateIn, db: Session = Depends(get_db)) -> NotificationSubOut:
    return NotificationSubOut.model_validate(seller_operations_service.create_notification(db, body))


@router.get("/sellers/{seller_id}/inventory-allocations", response_model=InventoryAllocationListOut)
def list_allocations(seller_id: str, db: Session = Depends(get_db)) -> InventoryAllocationListOut:
    rows = seller_operations_service.list_allocations(db, seller_id)
    return InventoryAllocationListOut(allocations=[InventoryAllocationOut.model_validate(r) for r in rows], total=len(rows))


@router.put("/seller-inventory-allocations", response_model=InventoryAllocationOut)
def upsert_allocation(body: InventoryAllocationUpsertIn, db: Session = Depends(get_db)) -> InventoryAllocationOut:
    row = seller_operations_service.upsert_allocation(db, body)
    return InventoryAllocationOut.model_validate(
        {**{c.name: getattr(row, c.name) for c in row.__table__.columns}, "partner_code": _pc(db).get(row.channel_partner_id)}
    )


@router.get("/sellers/{seller_id}/fulfillment-preferences", response_model=FulfillmentPreferenceOut | None)
def get_fulfillment(seller_id: str, db: Session = Depends(get_db)) -> FulfillmentPreferenceOut | None:
    row = seller_operations_service.get_fulfillment_prefs(db, seller_id)
    return FulfillmentPreferenceOut.model_validate(row) if row else None


@router.put("/seller-fulfillment-preferences", response_model=FulfillmentPreferenceOut)
def upsert_fulfillment(body: FulfillmentPreferenceUpsertIn, db: Session = Depends(get_db)) -> FulfillmentPreferenceOut:
    return FulfillmentPreferenceOut.model_validate(seller_operations_service.upsert_fulfillment_prefs(db, body))
