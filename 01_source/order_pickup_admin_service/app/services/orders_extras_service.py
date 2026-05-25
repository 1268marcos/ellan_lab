from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order_ops import (
    AllocationRecord,
    CreditRecord,
    DomainEventOutboxRecord,
    FoodDeliveryOrder,
    FulfillmentOrder,
    LifecycleDeadlineRecord,
    OrderDispute,
    OrderFulfillmentTracking,
    OrderGiftPickup,
    OrderItemSubstitution,
    OrderNotificationLog,
    OrderOpsHold,
    OrderPaymentReconciliation,
    OrderReturn,
    PaymentTransactionRecord,
    OrderIntegrationHealth,
    OrderItemRecord,
    OrderMarketplaceCommission,
    OrderOpsTimeline,
    OrderRecord,
    OrderSlaWatch,
    OmnichannelOrder,
    PartnerOrderEventsOutbox,
    PickupRecord,
)
from app.schemas.order_ops import (
    DisputeCreateIn,
    DisputeOut,
    IntegrationHealthOut,
    Order360Out,
    SlaWatchOut,
    TimelineCreateIn,
    TimelineEventOut,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def append_timeline(
    db: Session,
    *,
    order_id: str,
    event_source: str,
    event_type: str,
    title: str,
    severity: str = "INFO",
    detail: dict | None = None,
    occurred_at: datetime | None = None,
) -> TimelineEventOut:
    now = occurred_at or _utcnow()
    row = OrderOpsTimeline(
        id=new_id(),
        order_id=order_id,
        event_source=event_source,
        event_type=event_type,
        severity=severity,
        title=title,
        detail_json=json.dumps(detail or {}),
        occurred_at=now,
        created_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return TimelineEventOut.model_validate(row)


def rebuild_timeline_for_order(db: Session, order_id: str) -> int:
    """Materializa timeline a partir de entidades existentes (idempotente por chave lógica)."""
    order = db.get(OrderRecord, order_id)
    if not order:
        return 0
    count = 0
    existing = {
        (r.event_source, r.event_type, r.title)
        for r in db.query(OrderOpsTimeline).filter(OrderOpsTimeline.order_id == order_id).all()
    }

    def add(source: str, etype: str, title: str, at: datetime, severity: str = "INFO", detail: dict | None = None):
        nonlocal count
        key = (source, etype, title)
        if key in existing:
            return
        append_timeline(
            db,
            order_id=order_id,
            event_source=source,
            event_type=etype,
            title=title,
            severity=severity,
            detail=detail,
            occurred_at=at,
        )
        existing.add(key)
        count += 1

    add("order", "CREATED", f"Pedido {order.status}", order.created_at, detail={"payment_status": order.payment_status})
    if order.paid_at:
        add("payment", "PAID", "Pagamento confirmado", order.paid_at, "SUCCESS")
    for p in db.query(PickupRecord).filter(PickupRecord.order_id == order_id).all():
        add("pickup", p.lifecycle_stage, f"Pickup {p.status}", p.updated_at, detail={"pickup_id": p.id})
    for ob in db.query(PartnerOrderEventsOutbox).filter(PartnerOrderEventsOutbox.order_id == order_id).all():
        add("partner_outbox", ob.event_type, f"Outbox parceiro {ob.status}", ob.created_at, detail={"outbox_id": ob.id})
    for dl in db.query(LifecycleDeadlineRecord).filter(LifecycleDeadlineRecord.order_id == order_id).all():
        sev = "WARN" if dl.status == "PENDING" else "INFO"
        add("lifecycle", dl.deadline_type, f"Deadline {dl.status}", dl.due_at, sev)
    return count


def get_order_360(db: Session, order_id: str) -> Order360Out:
    order = db.get(OrderRecord, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order_not_found")

    rebuild_timeline_for_order(db, order_id)

    timeline = (
        db.query(OrderOpsTimeline)
        .filter(OrderOpsTimeline.order_id == order_id)
        .order_by(OrderOpsTimeline.occurred_at.desc())
        .limit(100)
        .all()
    )
    sla_active = (
        db.query(OrderSlaWatch)
        .filter(OrderSlaWatch.order_id == order_id, OrderSlaWatch.status == "ACTIVE")
        .count()
    )
    sla_breached = (
        db.query(OrderSlaWatch)
        .filter(OrderSlaWatch.order_id == order_id, OrderSlaWatch.status == "BREACHED")
        .count()
    )
    open_disputes = (
        db.query(OrderDispute).filter(OrderDispute.order_id == order_id, OrderDispute.status == "OPEN").count()
    )
    open_returns = (
        db.query(OrderReturn)
        .filter(
            OrderReturn.order_id == order_id,
            OrderReturn.status.in_(("REQUESTED", "IN_TRANSIT", "RECEIVED")),
        )
        .count()
    )
    active_holds = (
        db.query(OrderOpsHold).filter(OrderOpsHold.order_id == order_id, OrderOpsHold.status == "ACTIVE").count()
    )
    pay_mismatch = (
        db.query(OrderPaymentReconciliation)
        .filter(
            OrderPaymentReconciliation.order_id == order_id,
            OrderPaymentReconciliation.status == "MISMATCH",
        )
        .first()
    )

    risks: list[str] = []
    if sla_breached:
        risks.append("SLA_BREACHED")
    if open_disputes:
        risks.append("OPEN_DISPUTE")
    if open_returns:
        risks.append("RETURN_IN_PROGRESS")
    if active_holds:
        risks.append("OPS_HOLD_ACTIVE")
    if pay_mismatch:
        risks.append("PAYMENT_MISMATCH")
    if (
        db.query(OrderItemSubstitution)
        .filter(OrderItemSubstitution.order_id == order_id, OrderItemSubstitution.status == "REQUESTED")
        .count()
    ):
        risks.append("SUBSTITUTION_PENDING")
    gift = db.query(OrderGiftPickup).filter(OrderGiftPickup.order_id == order_id).first()
    if gift and gift.status == "PENDING_VERIFICATION":
        risks.append("GIFT_PENDING_VERIFICATION")
    pending_outbox = (
        db.query(PartnerOrderEventsOutbox)
        .filter(PartnerOrderEventsOutbox.order_id == order_id, PartnerOrderEventsOutbox.status == "PENDING")
        .count()
    )
    if pending_outbox:
        risks.append("PARTNER_OUTBOX_PENDING")
    if order.payment_status not in ("PAID", "CAPTURED", "SETTLED") and order.status == "PENDING":
        risks.append("PAYMENT_PENDING")

    health_score = max(0, 100 - len(risks) * 12 - sla_breached * 10)

    return Order360Out(
        order_id=order_id,
        order={
            "id": order.id,
            "status": order.status,
            "payment_status": order.payment_status,
            "amount_cents": order.amount_cents,
            "currency": order.currency,
            "partner_id": order.ecommerce_partner_id,
            "locker_id": order.locker_id,
            "created_at": order.created_at.isoformat(),
        },
        counts={
            "pickups": db.query(PickupRecord).filter(PickupRecord.order_id == order_id).count(),
            "items": db.query(OrderItemRecord).filter(OrderItemRecord.order_id == order_id).count(),
            "allocations": db.query(AllocationRecord).filter(AllocationRecord.order_id == order_id).count(),
            "partner_outbox": db.query(PartnerOrderEventsOutbox).filter(PartnerOrderEventsOutbox.order_id == order_id).count(),
            "domain_outbox": db.query(DomainEventOutboxRecord)
            .filter(DomainEventOutboxRecord.aggregate_id == order_id)
            .count(),
            "credits": db.query(CreditRecord).filter(CreditRecord.order_id == order_id).count(),
            "fulfillment_tracking": db.query(OrderFulfillmentTracking)
            .filter(OrderFulfillmentTracking.order_id == order_id)
            .count(),
            "omnichannel": db.query(OmnichannelOrder).filter(OmnichannelOrder.order_id == order_id).count(),
            "warehouse": db.query(FulfillmentOrder).filter(FulfillmentOrder.order_id == order_id).count(),
            "food_delivery": db.query(FoodDeliveryOrder).filter(FoodDeliveryOrder.order_id == order_id).count(),
            "commissions": db.query(OrderMarketplaceCommission)
            .filter(OrderMarketplaceCommission.order_id == order_id)
            .count(),
            "timeline": len(timeline),
            "returns": open_returns,
            "notifications": db.query(OrderNotificationLog)
            .filter(OrderNotificationLog.order_id == order_id)
            .count(),
            "payment_reconciliation": 1 if pay_mismatch else 0,
            "ops_holds": active_holds,
            "substitutions": db.query(OrderItemSubstitution)
            .filter(OrderItemSubstitution.order_id == order_id)
            .count(),
            "gift_pickup": 1 if gift else 0,
            "payment_transactions": db.query(PaymentTransactionRecord)
            .filter(PaymentTransactionRecord.order_id == order_id)
            .count(),
        },
        timeline=[TimelineEventOut.model_validate(t) for t in timeline],
        sla={"active": sla_active, "breached": sla_breached},
        disputes_open=open_disputes,
        risk_flags=risks,
        health_score=health_score,
        pickups=[
            {
                "id": p.id,
                "status": p.status,
                "lifecycle_stage": p.lifecycle_stage,
                "locker_id": p.locker_id,
            }
            for p in db.query(PickupRecord).filter(PickupRecord.order_id == order_id).all()
        ],
        partner_outbox_pending=pending_outbox,
    )


def list_timeline(db: Session, order_id: str, limit: int, offset: int) -> tuple[list[TimelineEventOut], int]:
    q = db.query(OrderOpsTimeline).filter(OrderOpsTimeline.order_id == order_id)
    total = q.count()
    rows = q.order_by(OrderOpsTimeline.occurred_at.desc()).offset(offset).limit(limit).all()
    return [TimelineEventOut.model_validate(r) for r in rows], total


def sync_sla_watches(db: Session) -> dict[str, int]:
    now = _utcnow()
    created = 0
    breached = 0
    for dl in db.query(LifecycleDeadlineRecord).filter(LifecycleDeadlineRecord.status == "PENDING").all():
        watch = (
            db.query(OrderSlaWatch)
            .filter(OrderSlaWatch.order_id == dl.order_id, OrderSlaWatch.watch_type == dl.deadline_type)
            .first()
        )
        if not watch:
            watch = OrderSlaWatch(
                id=new_id(),
                order_id=dl.order_id,
                watch_type=dl.deadline_type,
                due_at=dl.due_at,
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
            db.add(watch)
            created += 1
        due = _ensure_utc(dl.due_at)
        if due and due < now and watch.status == "ACTIVE":
            watch.status = "BREACHED"
            watch.breached_at = now
            watch.breach_reason = "deadline_passed"
            watch.updated_at = now
            breached += 1
            append_timeline(
                db,
                order_id=dl.order_id,
                event_source="sla",
                event_type="BREACHED",
                title=f"SLA {dl.deadline_type} violado",
                severity="ERROR",
                detail={"watch_type": dl.deadline_type},
            )
    for order in db.query(OrderRecord).filter(OrderRecord.pickup_deadline_at.isnot(None)).all():
        if not order.pickup_deadline_at:
            continue
        watch = (
            db.query(OrderSlaWatch)
            .filter(OrderSlaWatch.order_id == order.id, OrderSlaWatch.watch_type == "PICKUP_DEADLINE")
            .first()
        )
        if not watch:
            watch = OrderSlaWatch(
                id=new_id(),
                order_id=order.id,
                watch_type="PICKUP_DEADLINE",
                due_at=order.pickup_deadline_at,
                status="ACTIVE",
                created_at=now,
                updated_at=now,
            )
            db.add(watch)
            created += 1
        else:
            pickup_due = _ensure_utc(order.pickup_deadline_at)
            if pickup_due and pickup_due < now and watch.status == "ACTIVE":
                watch.status = "BREACHED"
                watch.breached_at = now
                watch.updated_at = now
                breached += 1
    db.commit()
    return {"created": created, "breached": breached}


def list_sla_watches(
    db: Session, *, status: str | None, order_id: str | None, limit: int, offset: int
) -> tuple[list[SlaWatchOut], int]:
    q = db.query(OrderSlaWatch)
    if status:
        q = q.filter(OrderSlaWatch.status == status.upper())
    if order_id:
        q = q.filter(OrderSlaWatch.order_id == order_id)
    total = q.count()
    rows = q.order_by(OrderSlaWatch.due_at.asc()).offset(offset).limit(limit).all()
    return [SlaWatchOut.model_validate(r) for r in rows], total


def create_dispute(db: Session, body: DisputeCreateIn) -> DisputeOut:
    row = OrderDispute(
        id=body.id or new_id(),
        order_id=body.order_id,
        dispute_type=body.dispute_type.upper(),
        status=body.status,
        amount_cents=body.amount_cents,
        currency=body.currency,
        reason_code=body.reason_code,
        notes=body.notes,
        opened_at=_utcnow(),
        created_at=_utcnow(),
        updated_at=_utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    append_timeline(
        db,
        order_id=body.order_id,
        event_source="dispute",
        event_type=body.dispute_type,
        title=f"Disputa aberta ({body.status})",
        severity="WARN",
    )
    return DisputeOut.model_validate(row)


def list_disputes(
    db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int
) -> tuple[list[DisputeOut], int]:
    q = db.query(OrderDispute)
    if order_id:
        q = q.filter(OrderDispute.order_id == order_id)
    if status:
        q = q.filter(OrderDispute.status == status.upper())
    total = q.count()
    rows = q.order_by(OrderDispute.opened_at.desc()).offset(offset).limit(limit).all()
    return [DisputeOut.model_validate(r) for r in rows], total


def record_integration_health(
    db: Session, *, channel_code: str, status: str, latency_ms: int | None = None, last_error: str | None = None
) -> IntegrationHealthOut:
    now = _utcnow()
    row = OrderIntegrationHealth(
        id=new_id(),
        channel_code=channel_code.upper(),
        status=status.upper(),
        latency_ms=latency_ms,
        last_error=last_error,
        checked_at=now,
        created_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return IntegrationHealthOut.model_validate(row)


def list_integration_health(
    db: Session, *, channel_code: str | None, limit: int, offset: int
) -> tuple[list[IntegrationHealthOut], int]:
    q = db.query(OrderIntegrationHealth)
    if channel_code:
        q = q.filter(OrderIntegrationHealth.channel_code == channel_code.upper())
    total = q.count()
    rows = q.order_by(OrderIntegrationHealth.checked_at.desc()).offset(offset).limit(limit).all()
    return [IntegrationHealthOut.model_validate(r) for r in rows], total


def seed_extras_demo(db: Session, order_id: str) -> None:
    now = _utcnow()
    if not db.query(OrderDispute).filter(OrderDispute.order_id == order_id).first():
        db.add(
            OrderDispute(
                id="disp-seed-demo-001",
                order_id=order_id,
                dispute_type="CHARGEBACK",
                status="OPEN",
                amount_cents=4990,
                currency="BRL",
                reason_code="FRAUD_SUSPECT",
                notes="Demo prompt5 — revisão manual OPS",
                opened_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    sync_sla_watches(db)
    rebuild_timeline_for_order(db, order_id)
    for code in ("MAGALU", "INPOST", "IFOOD"):
        if not db.query(OrderIntegrationHealth).filter(OrderIntegrationHealth.channel_code == code).first():
            record_integration_health(db, channel_code=code, status="OK", latency_ms=120)
    db.commit()
