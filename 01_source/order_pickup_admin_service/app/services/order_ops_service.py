from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order_ops import (
    CreditRecord,
    DomainEventOutboxRecord,
    FulfillmentOrder,
    OmnichannelOrder,
    OrderFulfillmentTracking,
    OrderItemRecord,
    OrderRecord,
    PartnerOrderEventsOutbox,
    PickupAttemptRecord,
    PickupEventRecord,
    PickupRecord,
    PickupTokenRecord,
)
from app.schemas.order_ops import (
    CreditCreateIn,
    CreditOut,
    DomainOutboxOut,
    FulfillmentOut,
    FulfillmentUpdateIn,
    OrderCreateIn,
    OrderItemOut,
    OrderOut,
    OrderUpdateIn,
    OutboxOut,
    PickupAttemptOut,
    PickupCreateIn,
    PickupEventOut,
    PickupOut,
    PickupTokenOut,
    PickupUpdateIn,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_orders(
    db: Session,
    *,
    status: str | None = None,
    partner_id: str | None = None,
    order_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[OrderOut], int]:
    q = db.query(OrderRecord)
    if status:
        q = q.filter(OrderRecord.status == status.upper())
    if partner_id:
        q = q.filter(OrderRecord.ecommerce_partner_id == partner_id)
    if order_id:
        q = q.filter(OrderRecord.id == order_id)
    total = q.count()
    rows = q.order_by(OrderRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [OrderOut.model_validate(r) for r in rows], total


def get_order_or_404(db: Session, order_id: str) -> OrderRecord:
    row = db.get(OrderRecord, order_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order_not_found")
    return row


def create_order(db: Session, body: OrderCreateIn) -> OrderOut:
    oid = body.id or f"ord-{new_id()[:12]}"
    if db.get(OrderRecord, oid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="order_id_exists")
    now = _utcnow()
    row = OrderRecord(
        id=oid,
        channel=body.channel,
        region=body.region,
        totem_id=body.totem_id,
        amount_cents=body.amount_cents,
        currency=body.currency,
        status=body.status.upper(),
        payment_status=body.payment_status.upper(),
        ecommerce_partner_id=body.ecommerce_partner_id,
        tenant_id=body.tenant_id,
        partner_order_ref=body.partner_order_ref,
        sku_id=body.sku_id,
        locker_id=body.locker_id,
        pickup_deadline_at=now + timedelta(hours=72),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return OrderOut.model_validate(row)


def update_order(db: Session, order_id: str, body: OrderUpdateIn) -> OrderOut:
    row = get_order_or_404(db, order_id)
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key in {"status", "payment_status"} and value is not None:
            value = str(value).upper()
        setattr(row, key, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return OrderOut.model_validate(row)


def delete_order(db: Session, order_id: str) -> None:
    row = get_order_or_404(db, order_id)
    db.delete(row)
    db.commit()


def list_pickups(
    db: Session,
    *,
    order_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[PickupOut], int]:
    q = db.query(PickupRecord)
    if order_id:
        q = q.filter(PickupRecord.order_id == order_id)
    if status:
        q = q.filter(PickupRecord.status == status.upper())
    total = q.count()
    rows = q.order_by(PickupRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [PickupOut.model_validate(r) for r in rows], total


def create_pickup(db: Session, body: PickupCreateIn) -> PickupOut:
    get_order_or_404(db, body.order_id)
    pid = body.id or f"pkp-{new_id()[:12]}"
    if db.get(PickupRecord, pid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="pickup_id_exists")
    now = _utcnow()
    row = PickupRecord(
        id=pid,
        order_id=body.order_id,
        channel=body.channel,
        region=body.region,
        locker_id=body.locker_id,
        slot=body.slot,
        status=body.status.upper(),
        lifecycle_stage=body.lifecycle_stage.upper(),
        expires_at=now + timedelta(hours=48),
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return PickupOut.model_validate(row)


def update_pickup(db: Session, pickup_id: str, body: PickupUpdateIn) -> PickupOut:
    row = db.get(PickupRecord, pickup_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pickup_not_found")
    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        if key in {"status", "lifecycle_stage"} and value is not None:
            value = str(value).upper()
        setattr(row, key, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return PickupOut.model_validate(row)


def list_credits(db: Session, *, order_id: str | None = None, limit: int = 50, offset: int = 0) -> tuple[list[CreditOut], int]:
    q = db.query(CreditRecord)
    if order_id:
        q = q.filter(CreditRecord.order_id == order_id)
    total = q.count()
    rows = q.order_by(CreditRecord.updated_at.desc()).offset(offset).limit(limit).all()
    return [CreditOut.model_validate(r) for r in rows], total


def list_outbox(
    db: Session,
    *,
    status: str | None = None,
    partner_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[OutboxOut], int]:
    q = db.query(PartnerOrderEventsOutbox)
    if status:
        q = q.filter(PartnerOrderEventsOutbox.status == status.upper())
    if partner_id:
        q = q.filter(PartnerOrderEventsOutbox.partner_id == partner_id)
    total = q.count()
    rows = q.order_by(PartnerOrderEventsOutbox.created_at.desc()).offset(offset).limit(limit).all()
    return [OutboxOut.model_validate(r) for r in rows], total


def replay_outbox(db: Session, outbox_id: str) -> tuple[bool, OutboxOut]:
    row = db.get(PartnerOrderEventsOutbox, outbox_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="outbox_not_found")
    replayed = row.status in {"FAILED", "DEAD_LETTER", "SKIPPED", "PENDING"}
    if replayed:
        row.status = "PENDING"
        row.attempt_count = 0
        row.next_retry_at = _utcnow()
        row.last_error = None
        row.updated_at = _utcnow()
        db.commit()
        db.refresh(row)
    return replayed, OutboxOut.model_validate(row)


def list_fulfillment(
    db: Session,
    *,
    status: str | None = None,
    partner_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[FulfillmentOut], int]:
    q = db.query(OrderFulfillmentTracking)
    if status:
        q = q.filter(OrderFulfillmentTracking.status == status.upper())
    if partner_id:
        q = q.filter(OrderFulfillmentTracking.partner_id == partner_id)
    total = q.count()
    rows = q.order_by(OrderFulfillmentTracking.updated_at.desc()).offset(offset).limit(limit).all()
    return [FulfillmentOut.model_validate(r) for r in rows], total


def update_fulfillment(db: Session, tracking_id: str, body: FulfillmentUpdateIn) -> FulfillmentOut:
    row = db.get(OrderFulfillmentTracking, tracking_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="fulfillment_not_found")
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "status" and value is not None:
            value = str(value).upper()
        setattr(row, field, value)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return FulfillmentOut.model_validate(row)


def get_pickup_or_404(db: Session, pickup_id: str) -> PickupRecord:
    row = db.get(PickupRecord, pickup_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="pickup_not_found")
    return row


def create_credit(db: Session, body: CreditCreateIn) -> CreditOut:
    get_order_or_404(db, body.order_id)
    cid = body.id or f"crd-{new_id()[:12]}"
    if db.get(CreditRecord, cid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="credit_id_exists")
    now = _utcnow()
    row = CreditRecord(
        id=cid,
        order_id=body.order_id,
        user_id=body.user_id,
        type=body.type,
        amount_cents=body.amount_cents,
        currency=body.currency,
        status=body.status.upper(),
        created_at_epoch=int(time.time()),
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CreditOut.model_validate(row)


def list_order_items(
    db: Session, *, order_id: str | None = None, limit: int = 50, offset: int = 0
) -> tuple[list[OrderItemOut], int]:
    q = db.query(OrderItemRecord)
    if order_id:
        q = q.filter(OrderItemRecord.order_id == order_id)
    total = q.count()
    rows = q.order_by(OrderItemRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [OrderItemOut.model_validate(r) for r in rows], total


def list_pickup_events(
    db: Session, *, pickup_id: str | None = None, limit: int = 50, offset: int = 0
) -> tuple[list[PickupEventOut], int]:
    q = db.query(PickupEventRecord)
    if pickup_id:
        q = q.filter(PickupEventRecord.pickup_id == pickup_id)
    total = q.count()
    rows = q.order_by(PickupEventRecord.occurred_at.desc()).offset(offset).limit(limit).all()
    return [PickupEventOut.model_validate(r) for r in rows], total


def list_pickup_tokens(
    db: Session, *, order_id: str | None = None, limit: int = 50, offset: int = 0
) -> tuple[list[PickupTokenOut], int]:
    q = db.query(PickupTokenRecord)
    if order_id:
        q = q.filter(PickupTokenRecord.order_id == order_id)
    total = q.count()
    rows = q.order_by(PickupTokenRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [PickupTokenOut.model_validate(r) for r in rows], total


def list_pickup_attempts(
    db: Session, *, order_id: str | None = None, limit: int = 50, offset: int = 0
) -> tuple[list[PickupAttemptOut], int]:
    q = db.query(PickupAttemptRecord)
    if order_id:
        q = q.filter(PickupAttemptRecord.order_id == order_id)
    total = q.count()
    rows = q.order_by(PickupAttemptRecord.created_at_epoch.desc()).offset(offset).limit(limit).all()
    return [PickupAttemptOut.model_validate(r) for r in rows], total


def list_domain_outbox(
    db: Session,
    *,
    status: str | None = None,
    aggregate_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[DomainOutboxOut], int]:
    q = db.query(DomainEventOutboxRecord)
    if status:
        q = q.filter(DomainEventOutboxRecord.status == status.upper())
    if aggregate_id:
        q = q.filter(DomainEventOutboxRecord.aggregate_id == aggregate_id)
    total = q.count()
    rows = q.order_by(DomainEventOutboxRecord.created_at.desc()).offset(offset).limit(limit).all()
    return [DomainOutboxOut.model_validate(r) for r in rows], total


def replay_domain_outbox(db: Session, outbox_id: str) -> tuple[bool, DomainOutboxOut]:
    row = db.get(DomainEventOutboxRecord, outbox_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="domain_outbox_not_found")
    replayed = row.status in {"FAILED", "DEAD_LETTER", "PENDING", "SKIPPED"}
    if replayed:
        row.status = "PENDING"
        row.retry_count = 0
        row.last_error = None
        row.updated_at = _utcnow()
        db.commit()
        db.refresh(row)
    return replayed, DomainOutboxOut.model_validate(row)


def seed_demo_order_graph(db: Session, *, partner_id: str = "ec-demo-001") -> dict[str, str]:
    now = _utcnow()
    order_id = "ord-seed-demo-001"
    pickup_id = "pkp-seed-demo-001"
    credit_id = "crd-seed-demo-001"
    outbox_id = "obx-seed-demo-001"
    oitem_id = "oitem-seed-demo-001"
    dom_id = "dom-seed-demo-001"
    if not db.get(OrderRecord, order_id):
        db.add(
            OrderRecord(
                id=order_id,
                channel="PARTNER_API",
                region="BR",
                totem_id="TOTEM-DEMO",
                amount_cents=4990,
                currency="BRL",
                status="PAID_PENDING_PICKUP",
                payment_status="PAID",
                ecommerce_partner_id=partner_id,
                tenant_id="tenant-demo",
                partner_order_ref="PO-SEED-001",
                sku_id="SKU-DEMO",
                locker_id="LOCKER-DEMO-01",
                paid_at=now,
                pickup_deadline_at=now + timedelta(hours=72),
                order_metadata=json.dumps({"seed": True}),
                created_at=now,
                updated_at=now,
            )
        )
    if not db.get(PickupRecord, pickup_id):
        db.add(
            PickupRecord(
                id=pickup_id,
                order_id=order_id,
                channel="PARTNER_API",
                region="BR",
                locker_id="LOCKER-DEMO-01",
                slot="A1",
                status="READY",
                lifecycle_stage="READY_FOR_PICKUP",
                ready_at=now,
                expires_at=now + timedelta(hours=48),
                created_at=now,
                updated_at=now,
            )
        )
    if not db.get(CreditRecord, credit_id):
        db.add(
            CreditRecord(
                id=credit_id,
                order_id=order_id,
                user_id="usr-demo",
                type="GOODWILL",
                amount_cents=500,
                currency="BRL",
                status="AVAILABLE",
                created_at_epoch=int(time.time()),
                meta_json="{}",
                updated_at=now,
            )
        )
    if not db.get(PartnerOrderEventsOutbox, outbox_id):
        db.add(
            PartnerOrderEventsOutbox(
                id=outbox_id,
                partner_id=partner_id,
                order_id=order_id,
                event_type="ORDER_PAID",
                payload_json=json.dumps({"order_id": order_id}),
                status="PENDING",
                created_at=now,
                updated_at=now,
            )
        )
    ft_id = "oft-seed-demo-001"
    if not db.get(OrderFulfillmentTracking, ft_id):
        db.add(
            OrderFulfillmentTracking(
                id=ft_id,
                order_id=order_id,
                fulfillment_type="ECOMMERCE_PARTNER",
                partner_id=partner_id,
                status="ALLOCATED",
                last_event_type="ORDER_PAID",
                last_outbox_status="PENDING",
                allocated_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    if not db.get(OrderItemRecord, oitem_id):
        db.add(
            OrderItemRecord(
                id=oitem_id,
                order_id=order_id,
                sku_id="SKU-DEMO",
                sku_description="Produto demo pickup",
                quantity=1,
                unit_amount_cents=4990,
                total_amount_cents=4990,
                item_status="ALLOCATED",
                created_at=now,
                updated_at=now,
            )
        )
    pevt_id = "pevt-seed-demo-001"
    if not db.get(PickupEventRecord, pevt_id):
        db.add(
            PickupEventRecord(
                id=pevt_id,
                pickup_id=pickup_id,
                version=1,
                event_type="PICKUP_READY",
                payload_json=json.dumps({"locker_id": "LOCKER-DEMO-01"}),
                occurred_at=now,
                created_at=now,
            )
        )
    ptk_id = "ptk-seed-demo-001"
    if not db.get(PickupTokenRecord, ptk_id):
        db.add(
            PickupTokenRecord(
                id=ptk_id,
                order_id=order_id,
                pickup_id=pickup_id,
                token_hash="hash-demo-token",
                expires_at=now + timedelta(hours=48),
                is_active=True,
                manual_code="123456",
                created_at=now,
            )
        )
    patt_id = "patt-seed-demo-001"
    if not db.get(PickupAttemptRecord, patt_id):
        db.add(
            PickupAttemptRecord(
                id=patt_id,
                order_id=order_id,
                gateway_id="gw-demo",
                created_at_epoch=int(time.time()),
                ok=True,
                reason=None,
            )
        )
    if not db.get(DomainEventOutboxRecord, dom_id):
        db.add(
            DomainEventOutboxRecord(
                id=dom_id,
                event_key=f"order.{order_id}.paid",
                aggregate_type="order",
                aggregate_id=order_id,
                event_name="OrderPaid",
                status="PENDING",
                payload_json=json.dumps({"order_id": order_id}),
                occurred_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    omni_id = "omni-seed-demo-001"
    if not db.get(OmnichannelOrder, omni_id):
        db.add(
            OmnichannelOrder(
                id=omni_id,
                order_id=order_id,
                store_id="store-magalu-demo-01",
                pickup_type="LOCKER_DELIVERY",
                status="READY",
                ready_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    fo_id = "fo-seed-demo-001"
    if not db.get(FulfillmentOrder, fo_id):
        db.add(
            FulfillmentOrder(
                id=fo_id,
                order_id=order_id,
                fulfillment_center_id="fc-sp-001",
                status="SHIPPED",
                priority=10,
                carrier="DHL",
                tracking_code="JD0146000123456789",
                shipped_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    from app.services.orders_domain_service import seed_extended_order_graph

    db.commit()
    seed_extended_order_graph(db, order_id=order_id, partner_id=partner_id)
    return {
        "order_id": order_id,
        "pickup_id": pickup_id,
        "credit_id": credit_id,
        "outbox_id": outbox_id,
        "order_item_id": oitem_id,
        "domain_outbox_id": dom_id,
    }
