from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cross_domain import (
    PartnerPaymentHold,
    PaymentContextPlayerLink,
    PaymentEcosystemPlayer,
    PaymentOrderContext,
    PaymentReconciliationBatch,
    SavedPaymentMethod,
    WebhookDelivery,
)
from app.models.payments import PaymentTransaction
from app.schemas.cross_domain import (
    PartnerPaymentHoldIn,
    PartnerPaymentHoldUpdate,
    PaymentEcosystemPlayerIn,
    PaymentEcosystemPlayerUpdate,
    PaymentOrderContextIn,
    PaymentReconciliationBatchIn,
    PaymentReconciliationBatchUpdate,
    SavedPaymentMethodIn,
)
from app.services.crypto_util import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _links_for_context(db: Session, context_id: str) -> list[PaymentContextPlayerLink]:
    return (
        db.query(PaymentContextPlayerLink)
        .filter(PaymentContextPlayerLink.order_context_id == context_id)
        .all()
    )


# --- ecosystem players ---


def list_ecosystem_players(
    db: Session, *, segment: str | None = None, active_only: bool = False, limit: int = 200
) -> list[PaymentEcosystemPlayer]:
    q = db.query(PaymentEcosystemPlayer)
    if segment:
        q = q.filter(PaymentEcosystemPlayer.segment == segment.upper())
    if active_only:
        q = q.filter(PaymentEcosystemPlayer.is_active.is_(True))
    return q.order_by(PaymentEcosystemPlayer.code).limit(limit).all()


def create_ecosystem_player(db: Session, body: PaymentEcosystemPlayerIn) -> PaymentEcosystemPlayer:
    if db.query(PaymentEcosystemPlayer).filter(PaymentEcosystemPlayer.code == body.code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="player_code_exists")
    row = PaymentEcosystemPlayer(id=body.id or new_id(), **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_ecosystem_player(
    db: Session, player_id: str, body: PaymentEcosystemPlayerUpdate
) -> PaymentEcosystemPlayer:
    row = db.get(PaymentEcosystemPlayer, player_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="player_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


# --- order context ---


def list_order_contexts(
    db: Session, *, tenant_id: str | None = None, locker_id: str | None = None, limit: int = 100
) -> list[PaymentOrderContext]:
    q = db.query(PaymentOrderContext)
    if tenant_id:
        q = q.filter(PaymentOrderContext.tenant_id == tenant_id)
    if locker_id:
        q = q.filter(PaymentOrderContext.locker_id == locker_id)
    return q.order_by(PaymentOrderContext.created_at.desc()).limit(limit).all()


def get_order_context_by_order(db: Session, order_id: str) -> PaymentOrderContext | None:
    return db.query(PaymentOrderContext).filter(PaymentOrderContext.order_id == order_id).first()


def create_order_context(db: Session, body: PaymentOrderContextIn) -> PaymentOrderContext:
    if get_order_context_by_order(db, body.order_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="order_context_exists")
    cid = body.id or new_id()
    links = body.player_links
    row = PaymentOrderContext(
        id=cid,
        **body.model_dump(exclude={"id", "player_links"}),
    )
    db.add(row)
    for link in links:
        db.add(
            PaymentContextPlayerLink(
                id=new_id(),
                order_context_id=cid,
                player_code=link.player_code,
                role=link.role.upper(),
                amount_cents=link.amount_cents,
                share_pct=link.share_pct,
            )
        )
    db.commit()
    db.refresh(row)
    return row


def get_order_context_or_404(db: Session, context_id: str) -> PaymentOrderContext:
    row = db.get(PaymentOrderContext, context_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="order_context_not_found")
    return row


# --- reconciliation batches ---


def list_reconciliation_batches(
    db: Session, *, status: str | None = None, limit: int = 100
) -> list[PaymentReconciliationBatch]:
    q = db.query(PaymentReconciliationBatch)
    if status:
        q = q.filter(PaymentReconciliationBatch.status == status.upper())
    return q.order_by(PaymentReconciliationBatch.created_at.desc()).limit(limit).all()


def create_reconciliation_batch(
    db: Session, body: PaymentReconciliationBatchIn
) -> PaymentReconciliationBatch:
    if db.query(PaymentReconciliationBatch).filter(PaymentReconciliationBatch.batch_code == body.batch_code).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="batch_code_exists")
    row = PaymentReconciliationBatch(id=body.id or new_id(), **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_reconciliation_batch(
    db: Session, batch_id: str, body: PaymentReconciliationBatchUpdate
) -> PaymentReconciliationBatch:
    row = db.get(PaymentReconciliationBatch, batch_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="batch_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    if body.status and body.status.upper() == "CLOSED" and not row.closed_at:
        row.closed_at = _utcnow()
        pending = (
            db.query(PaymentTransaction)
            .filter(
                PaymentTransaction.reconciliation_batch_id == row.batch_code,
                PaymentTransaction.reconciliation_status == "PENDING",
            )
            .count()
        )
        row.mismatch_count = pending
    db.commit()
    db.refresh(row)
    return row


def assign_transactions_to_batch(db: Session, batch_code: str, transaction_ids: list[str]) -> dict[str, int]:
    batch = db.query(PaymentReconciliationBatch).filter(PaymentReconciliationBatch.batch_code == batch_code).first()
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="batch_not_found")
    updated = 0
    for tid in transaction_ids:
        tx = db.get(PaymentTransaction, tid)
        if tx:
            tx.reconciliation_batch_id = batch_code
            tx.reconciliation_status = "PENDING"
            updated += 1
    batch.expected_count = (
        db.query(PaymentTransaction)
        .filter(PaymentTransaction.reconciliation_batch_id == batch_code)
        .count()
    )
    db.commit()
    return {"assigned": updated, "expected_count": batch.expected_count}


# --- webhook deliveries ---


def list_webhook_deliveries(
    db: Session, *, endpoint_id: str | None = None, status: str | None = None, limit: int = 100
) -> list[WebhookDelivery]:
    q = db.query(WebhookDelivery)
    if endpoint_id:
        q = q.filter(WebhookDelivery.endpoint_id == endpoint_id)
    if status:
        q = q.filter(WebhookDelivery.status == status.upper())
    return q.order_by(WebhookDelivery.created_at.desc()).limit(limit).all()


def retry_webhook_delivery(db: Session, delivery_id: str) -> WebhookDelivery:
    row = db.get(WebhookDelivery, delivery_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="delivery_not_found")
    row.status = "PENDING"
    row.next_attempt_at = _utcnow()
    row.attempt_count = min(row.attempt_count, row.max_attempts - 1)
    db.commit()
    db.refresh(row)
    return row


# --- partner holds ---


def list_partner_holds(
    db: Session, *, partner_id: str | None = None, status: str | None = None, limit: int = 100
) -> list[PartnerPaymentHold]:
    q = db.query(PartnerPaymentHold)
    if partner_id:
        q = q.filter(PartnerPaymentHold.partner_id == partner_id)
    if status:
        q = q.filter(PartnerPaymentHold.status == status.upper())
    return q.order_by(PartnerPaymentHold.created_at.desc()).limit(limit).all()


def create_partner_hold(db: Session, body: PartnerPaymentHoldIn) -> PartnerPaymentHold:
    row = PartnerPaymentHold(id=body.id or new_id(), **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_partner_hold(db: Session, hold_id: str, body: PartnerPaymentHoldUpdate) -> PartnerPaymentHold:
    row = db.get(PartnerPaymentHold, hold_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="hold_not_found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    if body.status and body.status.upper() == "RELEASED" and not row.released_at:
        row.released_at = _utcnow()
        if body.released_amount_cents is None:
            row.released_amount_cents = row.hold_amount_cents
    db.commit()
    db.refresh(row)
    return row


# --- saved methods ---


def list_saved_methods(db: Session, *, user_id: str | None = None, limit: int = 100) -> list[SavedPaymentMethod]:
    q = db.query(SavedPaymentMethod)
    if user_id:
        q = q.filter(SavedPaymentMethod.user_id == user_id)
    return q.order_by(SavedPaymentMethod.created_at.desc()).limit(limit).all()


def create_saved_method(db: Session, body: SavedPaymentMethodIn) -> SavedPaymentMethod:
    if body.is_default:
        db.query(SavedPaymentMethod).filter(SavedPaymentMethod.user_id == body.user_id).update(
            {SavedPaymentMethod.is_default: False}
        )
    row = SavedPaymentMethod(id=body.id or new_id(), **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def deactivate_saved_method(db: Session, method_id: str) -> SavedPaymentMethod:
    row = db.get(SavedPaymentMethod, method_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="saved_method_not_found")
    row.is_active = False
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def holds_active_cents(db: Session) -> int:
    total = (
        db.query(func.coalesce(func.sum(PartnerPaymentHold.hold_amount_cents), 0))
        .filter(PartnerPaymentHold.status == "HELD")
        .scalar()
    )
    return int(total or 0)
