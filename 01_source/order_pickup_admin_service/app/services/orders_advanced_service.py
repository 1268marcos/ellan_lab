from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.order_ops import (
    OrderGiftPickup,
    OrderItemSubstitution,
    OrderNotificationLog,
    OrderOpsHold,
    OrderPaymentReconciliation,
    OrderRecord,
    OrderReturn,
)
from app.services.payments_bridge_service import (
    captured_totals_for_order,
    seed_payment_transaction_demo,
    sync_from_payments_admin,
)
from app.schemas.order_ops import (
    GiftPickupCreateIn,
    GiftPickupOut,
    GiftPickupUpdateIn,
    ItemSubstitutionCreateIn,
    ItemSubstitutionOut,
    ItemSubstitutionUpdateIn,
    NotificationLogOut,
    OpsHoldCreateIn,
    OpsHoldOut,
    OrderReturnCreateIn,
    OrderReturnOut,
    OrderReturnUpdateIn,
    PaymentReconciliationOut,
)
from app.services.crypto_util import new_id
from app.services.orders_extras_service import append_timeline

DEMO_ORDER = "ord-seed-demo-001"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def list_returns(
    db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int
) -> tuple[list[OrderReturnOut], int]:
    q = db.query(OrderReturn)
    if order_id:
        q = q.filter(OrderReturn.order_id == order_id)
    if status:
        q = q.filter(OrderReturn.status == status.upper())
    total = q.count()
    rows = q.order_by(OrderReturn.requested_at.desc()).offset(offset).limit(limit).all()
    return [OrderReturnOut.model_validate(r) for r in rows], total


def create_return(db: Session, body: OrderReturnCreateIn) -> OrderReturnOut:
    if not db.get(OrderRecord, body.order_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    now = _utcnow()
    row = OrderReturn(
        id=body.id or new_id(),
        order_id=body.order_id,
        return_type=body.return_type,
        status=body.status.upper(),
        reason_code=body.reason_code,
        refund_amount_cents=body.refund_amount_cents,
        currency=body.currency,
        locker_id=body.locker_id,
        tracking_code=body.tracking_code,
        notes=body.notes,
        requested_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    append_timeline(
        db,
        order_id=body.order_id,
        event_source="returns",
        event_type="RETURN_REQUESTED",
        title=f"Devolução {row.return_type} aberta",
        severity="WARN",
        detail={"return_id": row.id, "status": row.status},
    )
    return OrderReturnOut.model_validate(row)


def update_return(db: Session, return_id: str, body: OrderReturnUpdateIn) -> OrderReturnOut:
    row = db.get(OrderReturn, return_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="return not found")
    now = _utcnow()
    if body.status:
        row.status = body.status.upper()
    if body.received_at is not None:
        row.received_at = body.received_at
    if body.resolved_at is not None:
        row.resolved_at = body.resolved_at
    if body.notes is not None:
        row.notes = body.notes
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return OrderReturnOut.model_validate(row)


def list_notifications(
    db: Session, *, order_id: str | None, channel: str | None, limit: int, offset: int
) -> tuple[list[NotificationLogOut], int]:
    q = db.query(OrderNotificationLog)
    if order_id:
        q = q.filter(OrderNotificationLog.order_id == order_id)
    if channel:
        q = q.filter(OrderNotificationLog.channel == channel.upper())
    total = q.count()
    rows = q.order_by(OrderNotificationLog.sent_at.desc()).offset(offset).limit(limit).all()
    return [NotificationLogOut.model_validate(r) for r in rows], total


def list_payment_reconciliation(
    db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int
) -> tuple[list[PaymentReconciliationOut], int]:
    q = db.query(OrderPaymentReconciliation)
    if order_id:
        q = q.filter(OrderPaymentReconciliation.order_id == order_id)
    if status:
        q = q.filter(OrderPaymentReconciliation.status == status.upper())
    total = q.count()
    rows = q.order_by(OrderPaymentReconciliation.updated_at.desc()).offset(offset).limit(limit).all()
    return [PaymentReconciliationOut.model_validate(r) for r in rows], total


def run_payment_reconciliation(db: Session, order_id: str | None = None) -> dict[str, int]:
    """Reconcilia pedido vs soma de payment_transactions (gateway); fallback em payment_status."""
    now = _utcnow()
    created = 0
    updated = 0
    mismatched = 0
    used_gateway = 0
    q = db.query(OrderRecord)
    if order_id:
        q = q.filter(OrderRecord.id == order_id)
    for order in q.all():
        gw = captured_totals_for_order(db, order.id)
        if gw is not None:
            captured, fee, payment_ref = gw
            used_gateway += 1
            if captured == order.amount_cents:
                recon_status = "MATCHED"
                reason = None
            elif captured == 0:
                recon_status = "MISMATCH"
                reason = "gateway_no_captured_tx"
            else:
                recon_status = "MISMATCH"
                reason = "amount_delta"
        elif order.payment_status in ("PAID", "CAPTURED", "SETTLED"):
            captured = order.amount_cents
            fee = max(0, int(order.amount_cents * 0.029))
            payment_ref = f"legacy-{order.id[:12]}"
            recon_status = "MATCHED"
            reason = None
        else:
            captured = 0
            fee = 0
            payment_ref = None
            recon_status = "MISMATCH" if order.amount_cents > 0 else "PENDING"
            reason = "no_gateway_tx" if recon_status == "MISMATCH" else None
        row = db.query(OrderPaymentReconciliation).filter(OrderPaymentReconciliation.order_id == order.id).first()
        if not row:
            row = OrderPaymentReconciliation(
                id=new_id(),
                order_id=order.id,
                payment_ref=payment_ref or f"pay-{order.id[:12]}",
                expected_cents=order.amount_cents,
                captured_cents=captured,
                fee_cents=fee,
                currency=order.currency,
                status=recon_status,
                mismatch_reason=reason,
                reconciled_at=now if recon_status == "MATCHED" else None,
                created_at=now,
                updated_at=now,
            )
            db.add(row)
            created += 1
        else:
            row.expected_cents = order.amount_cents
            row.captured_cents = captured
            row.fee_cents = fee
            row.status = recon_status
            row.mismatch_reason = reason
            row.reconciled_at = now if recon_status == "MATCHED" else None
            row.updated_at = now
            updated += 1
        if recon_status == "MISMATCH":
            mismatched += 1
            append_timeline(
                db,
                order_id=order.id,
                event_source="payments",
                event_type="RECON_MISMATCH",
                title="Reconciliação pagamento divergente",
                severity="ERROR",
                detail={"expected": order.amount_cents, "captured": captured},
            )
    db.commit()
    return {"created": created, "updated": updated, "mismatched": mismatched, "used_gateway": used_gateway}


def list_substitutions(
    db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int
) -> tuple[list[ItemSubstitutionOut], int]:
    q = db.query(OrderItemSubstitution)
    if order_id:
        q = q.filter(OrderItemSubstitution.order_id == order_id)
    if status:
        q = q.filter(OrderItemSubstitution.status == status.upper())
    total = q.count()
    rows = q.order_by(OrderItemSubstitution.created_at.desc()).offset(offset).limit(limit).all()
    return [ItemSubstitutionOut.model_validate(r) for r in rows], total


def create_substitution(db: Session, body: ItemSubstitutionCreateIn) -> ItemSubstitutionOut:
    if not db.get(OrderRecord, body.order_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    now = _utcnow()
    row = OrderItemSubstitution(
        id=body.id or new_id(),
        order_id=body.order_id,
        order_item_id=body.order_item_id,
        original_sku_id=body.original_sku_id,
        substitute_sku_id=body.substitute_sku_id,
        reason_code=body.reason_code.upper(),
        status=body.status.upper(),
        quantity=body.quantity,
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    append_timeline(
        db,
        order_id=body.order_id,
        event_source="fulfillment",
        event_type="ITEM_SUBSTITUTION",
        title=f"Substituição {body.original_sku_id} → {body.substitute_sku_id}",
        severity="WARN",
        detail={"substitution_id": row.id, "reason": body.reason_code},
    )
    return ItemSubstitutionOut.model_validate(row)


def update_substitution(db: Session, sub_id: str, body: ItemSubstitutionUpdateIn) -> ItemSubstitutionOut:
    row = db.get(OrderItemSubstitution, sub_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="substitution not found")
    now = _utcnow()
    if body.status:
        row.status = body.status.upper()
        if row.status == "APPLIED":
            row.approved_by = body.approved_by or "ops"
    if body.notes is not None:
        row.notes = body.notes
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return ItemSubstitutionOut.model_validate(row)


def list_gift_pickups(
    db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int
) -> tuple[list[GiftPickupOut], int]:
    q = db.query(OrderGiftPickup)
    if order_id:
        q = q.filter(OrderGiftPickup.order_id == order_id)
    if status:
        q = q.filter(OrderGiftPickup.status == status.upper())
    total = q.count()
    rows = q.order_by(OrderGiftPickup.created_at.desc()).offset(offset).limit(limit).all()
    return [GiftPickupOut.model_validate(r) for r in rows], total


def create_gift_pickup(db: Session, body: GiftPickupCreateIn) -> GiftPickupOut:
    if not db.get(OrderRecord, body.order_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    if db.query(OrderGiftPickup).filter(OrderGiftPickup.order_id == body.order_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="gift pickup already exists for order")
    now = _utcnow()
    auth_code = body.pickup_authorization_code or new_id()[:8].upper()
    row = OrderGiftPickup(
        id=body.id or new_id(),
        order_id=body.order_id,
        is_gift=True,
        purchaser_name=body.purchaser_name,
        recipient_name=body.recipient_name,
        recipient_phone_masked=body.recipient_phone_masked,
        recipient_document_masked=body.recipient_document_masked,
        pickup_authorization_code=auth_code,
        id_verification_required=body.id_verification_required,
        status="PENDING_VERIFICATION",
        message=body.message,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    append_timeline(
        db,
        order_id=body.order_id,
        event_source="pickup",
        event_type="GIFT_RECIPIENT",
        title=f"Gift para {body.recipient_name}",
        severity="INFO",
        detail={"gift_id": row.id, "auth_code": auth_code},
    )
    return GiftPickupOut.model_validate(row)


def update_gift_pickup(db: Session, gift_id: str, body: GiftPickupUpdateIn) -> GiftPickupOut:
    row = db.get(OrderGiftPickup, gift_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="gift pickup not found")
    now = _utcnow()
    if body.status:
        row.status = body.status.upper()
    if body.verified_at is not None:
        row.verified_at = body.verified_at
    elif row.status == "AUTHORIZED" and not row.verified_at:
        row.verified_at = now
    if body.picked_up_at is not None:
        row.picked_up_at = body.picked_up_at
    row.updated_at = now
    db.commit()
    db.refresh(row)
    return GiftPickupOut.model_validate(row)


def list_holds(
    db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int
) -> tuple[list[OpsHoldOut], int]:
    q = db.query(OrderOpsHold)
    if order_id:
        q = q.filter(OrderOpsHold.order_id == order_id)
    if status:
        q = q.filter(OrderOpsHold.status == status.upper())
    total = q.count()
    rows = q.order_by(OrderOpsHold.placed_at.desc()).offset(offset).limit(limit).all()
    return [OpsHoldOut.model_validate(r) for r in rows], total


def create_hold(db: Session, body: OpsHoldCreateIn) -> OpsHoldOut:
    if not db.get(OrderRecord, body.order_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order not found")
    active = (
        db.query(OrderOpsHold)
        .filter(OrderOpsHold.order_id == body.order_id, OrderOpsHold.status == "ACTIVE", OrderOpsHold.hold_type == body.hold_type)
        .first()
    )
    if active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="hold already active for type")
    now = _utcnow()
    row = OrderOpsHold(
        id=body.id or new_id(),
        order_id=body.order_id,
        hold_type=body.hold_type.upper(),
        status="ACTIVE",
        reason=body.reason,
        placed_by=body.placed_by,
        placed_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    append_timeline(
        db,
        order_id=body.order_id,
        event_source="ops",
        event_type="HOLD_PLACED",
        title=f"Hold {row.hold_type} ativo",
        severity="WARN",
        detail={"hold_id": row.id},
    )
    return OpsHoldOut.model_validate(row)


def release_hold(db: Session, hold_id: str, released_by: str) -> OpsHoldOut:
    row = db.get(OrderOpsHold, hold_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="hold not found")
    if row.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="hold not active")
    now = _utcnow()
    row.status = "RELEASED"
    row.released_by = released_by
    row.released_at = now
    row.updated_at = now
    db.commit()
    db.refresh(row)
    append_timeline(
        db,
        order_id=row.order_id,
        event_source="ops",
        event_type="HOLD_RELEASED",
        title=f"Hold {row.hold_type} liberado",
        severity="INFO",
        detail={"hold_id": row.id},
    )
    return OpsHoldOut.model_validate(row)


def seed_advanced_demo(db: Session, order_id: str = DEMO_ORDER) -> None:
    now = _utcnow()
    if not db.query(OrderReturn).filter(OrderReturn.order_id == order_id).first():
        db.add(
            OrderReturn(
                id="ret-seed-demo-001",
                order_id=order_id,
                return_type="LOCKER_DROP_OFF",
                status="REQUESTED",
                reason_code="DAMAGED_ITEM",
                refund_amount_cents=1990,
                currency="BRL",
                locker_id="LOCKER-DEMO-01",
                requested_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    templates = [
        ("SMS", "PICKUP_READY"),
        ("EMAIL", "PICKUP_REMINDER_24H"),
        ("PUSH", "LOCKER_CODE_READY"),
    ]
    for ch, tpl in templates:
        if not db.query(OrderNotificationLog).filter(
            OrderNotificationLog.order_id == order_id,
            OrderNotificationLog.template_code == tpl,
        ).first():
            db.add(
                OrderNotificationLog(
                    id=new_id(),
                    order_id=order_id,
                    channel=ch,
                    template_code=tpl,
                    recipient_masked="***@email.com" if ch == "EMAIL" else "+55***9999",
                    status="SENT",
                    provider_ref=f"prov-{tpl.lower()}",
                    payload_json=json.dumps({"order_id": order_id}),
                    sent_at=now,
                    created_at=now,
                )
            )
    if not db.query(OrderOpsHold).filter(OrderOpsHold.order_id == order_id, OrderOpsHold.status == "ACTIVE").first():
        db.add(
            OrderOpsHold(
                id="hold-seed-demo-001",
                order_id=order_id,
                hold_type="FRAUD_REVIEW",
                status="ACTIVE",
                reason="Demo prompt7 — revisar antes de liberar pickup",
                placed_by="ops-seed",
                placed_at=now,
                created_at=now,
                updated_at=now,
            )
        )
    order = db.get(OrderRecord, order_id)
    if order:
        seed_payment_transaction_demo(db, order_id, amount_cents=order.amount_cents)
    if not db.query(OrderItemSubstitution).filter(OrderItemSubstitution.order_id == order_id).first():
        db.add(
            OrderItemSubstitution(
                id="sub-seed-demo-001",
                order_id=order_id,
                order_item_id="oi-seed-demo-001",
                original_sku_id="SKU-DEMO",
                substitute_sku_id="SKU-DEMO-V2",
                reason_code="OUT_OF_STOCK",
                status="REQUESTED",
                quantity=1,
                notes="Demo — aguardar aprovação OPS",
                created_at=now,
                updated_at=now,
            )
        )
    if not db.query(OrderGiftPickup).filter(OrderGiftPickup.order_id == order_id).first():
        db.add(
            OrderGiftPickup(
                id="gift-seed-demo-001",
                order_id=order_id,
                is_gift=True,
                purchaser_name="Maria Demo",
                recipient_name="João Presenteado",
                recipient_phone_masked="+55***1234",
                recipient_document_masked="***.456.789-**",
                pickup_authorization_code="GIFT8DEMO",
                id_verification_required=True,
                status="PENDING_VERIFICATION",
                message="Feliz aniversário!",
                created_at=now,
                updated_at=now,
            )
        )
    db.commit()
    run_payment_reconciliation(db, order_id=order_id)
