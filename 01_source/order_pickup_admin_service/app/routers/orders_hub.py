from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.order_ops import (
    AllocationRecord,
    CreditRecord,
    DomainEventOutboxRecord,
    FulfillmentOrder,
    LifecycleDeadlineRecord,
    LogisticsManifest,
    OmnichannelOrder,
    FoodDeliveryOrder,
    OrderDispute,
    OrderNotificationLog,
    OrderOpsHold,
    OrderPaymentReconciliation,
    OrderGiftPickup,
    OrderItemSubstitution,
    OrderReturn,
    PaymentTransactionRecord,
    OrderFulfillmentTracking,
    OrderIntegrationChannel,
    OrderOpsTimeline,
    OrderSlaWatch,
    OrderItemRecord,
    OrderMarketplaceCommission,
    OrderRecord,
    PartnerOrderEventsOutbox,
    PickupRecord,
)
from app.schemas.order_ops import OrdersHubSummaryOut

router = APIRouter(tags=["orders-hub"])


@router.get("/hub/summary", response_model=OrdersHubSummaryOut)
def hub_summary(db: Session = Depends(get_db)) -> OrdersHubSummaryOut:
    return OrdersHubSummaryOut(
        orders=db.query(OrderRecord).count(),
        pickups=db.query(PickupRecord).count(),
        credits=db.query(CreditRecord).count(),
        partner_outbox_pending=db.query(PartnerOrderEventsOutbox)
        .filter(PartnerOrderEventsOutbox.status == "PENDING")
        .count(),
        domain_outbox_pending=db.query(DomainEventOutboxRecord)
        .filter(DomainEventOutboxRecord.status == "PENDING")
        .count(),
        fulfillment_tracking=db.query(OrderFulfillmentTracking).count(),
        omnichannel=db.query(OmnichannelOrder).count(),
        fulfillment_orders=db.query(FulfillmentOrder).count(),
        allocations=db.query(AllocationRecord).count(),
        logistics_manifests=db.query(LogisticsManifest).count(),
        integration_channels=db.query(OrderIntegrationChannel).count(),
        marketplace_commissions=db.query(OrderMarketplaceCommission).count(),
        lifecycle_deadlines_pending=db.query(LifecycleDeadlineRecord)
        .filter(LifecycleDeadlineRecord.status == "PENDING")
        .count(),
        order_items=db.query(OrderItemRecord).count(),
        food_delivery_orders=db.query(FoodDeliveryOrder).count(),
        timeline_events=db.query(OrderOpsTimeline).count(),
        sla_watches_active=db.query(OrderSlaWatch).filter(OrderSlaWatch.status == "ACTIVE").count(),
        sla_watches_breached=db.query(OrderSlaWatch).filter(OrderSlaWatch.status == "BREACHED").count(),
        disputes_open=db.query(OrderDispute).filter(OrderDispute.status == "OPEN").count(),
        returns_open=db.query(OrderReturn)
        .filter(OrderReturn.status.in_(("REQUESTED", "IN_TRANSIT", "RECEIVED")))
        .count(),
        payment_recon_mismatch=db.query(OrderPaymentReconciliation)
        .filter(OrderPaymentReconciliation.status == "MISMATCH")
        .count(),
        ops_holds_active=db.query(OrderOpsHold).filter(OrderOpsHold.status == "ACTIVE").count(),
        notifications_sent=db.query(OrderNotificationLog).filter(OrderNotificationLog.status == "SENT").count(),
        substitutions_pending=db.query(OrderItemSubstitution)
        .filter(OrderItemSubstitution.status == "REQUESTED")
        .count(),
        gifts_pending_verification=db.query(OrderGiftPickup)
        .filter(OrderGiftPickup.status == "PENDING_VERIFICATION")
        .count(),
        payment_transactions=db.query(PaymentTransactionRecord).count(),
    )
