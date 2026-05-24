from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.payments import (
    GatewayEvent,
    Payment,
    PaymentInstruction,
    PaymentSplit,
    PaymentTransaction,
    WebhookEndpoint,
)
from app.schemas.payments import (
    GatewayEventIn,
    PaymentIn,
    PaymentInstructionIn,
    PaymentInstructionUpdate,
    PaymentSplitIn,
    PaymentSplitUpdate,
    PaymentTransactionIn,
    PaymentTransactionUpdate,
    PaymentUpdate,
    WebhookEndpointIn,
    WebhookEndpointUpdate,
    WebhookSecretRotateOut,
)
from app.services.crypto_util import generate_webhook_secret, new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _epoch() -> int:
    return int(time.time())


# --- transactions ---


def list_transactions(
    db: Session,
    *,
    order_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[PaymentTransaction]:
    q = db.query(PaymentTransaction)
    if order_id:
        q = q.filter(PaymentTransaction.order_id == order_id)
    if status:
        q = q.filter(PaymentTransaction.status == status.upper())
    return q.order_by(PaymentTransaction.created_at.desc()).limit(limit).all()


def create_transaction(db: Session, body: PaymentTransactionIn) -> PaymentTransaction:
    tid = body.id or new_id()
    if db.get(PaymentTransaction, tid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="transaction_id_exists")
    row = PaymentTransaction(id=tid, **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_transaction_or_404(db: Session, tx_id: str) -> PaymentTransaction:
    row = db.get(PaymentTransaction, tx_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="transaction_not_found")
    return row


def update_transaction(db: Session, tx_id: str, body: PaymentTransactionUpdate) -> PaymentTransaction:
    row = get_transaction_or_404(db, tx_id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    if body.status and body.status.upper() == "APPROVED" and not row.approved_at:
        row.approved_at = _utcnow()
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_transaction(db: Session, tx_id: str) -> None:
    row = get_transaction_or_404(db, tx_id)
    db.delete(row)
    db.commit()


# --- instructions ---


def list_instructions(db: Session, *, order_id: str | None = None, limit: int = 100) -> list[PaymentInstruction]:
    q = db.query(PaymentInstruction)
    if order_id:
        q = q.filter(PaymentInstruction.order_id == order_id)
    return q.order_by(PaymentInstruction.created_at.desc()).limit(limit).all()


def create_instruction(db: Session, body: PaymentInstructionIn) -> PaymentInstruction:
    iid = body.id or new_id()
    if db.get(PaymentInstruction, iid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="instruction_id_exists")
    row = PaymentInstruction(id=iid, **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_instruction_or_404(db: Session, iid: str) -> PaymentInstruction:
    row = db.get(PaymentInstruction, iid)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="instruction_not_found")
    return row


def update_instruction(db: Session, iid: str, body: PaymentInstructionUpdate) -> PaymentInstruction:
    row = get_instruction_or_404(db, iid)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_instruction(db: Session, iid: str) -> None:
    row = get_instruction_or_404(db, iid)
    db.delete(row)
    db.commit()


# --- splits ---


def list_splits(db: Session, *, order_id: str | None = None, limit: int = 100) -> list[PaymentSplit]:
    q = db.query(PaymentSplit)
    if order_id:
        q = q.filter(PaymentSplit.order_id == order_id)
    return q.order_by(PaymentSplit.created_at.desc()).limit(limit).all()


def create_split(db: Session, body: PaymentSplitIn) -> PaymentSplit:
    sid = body.id or new_id()
    if db.get(PaymentSplit, sid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="split_id_exists")
    row = PaymentSplit(id=sid, **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_split_or_404(db: Session, sid: str) -> PaymentSplit:
    row = db.get(PaymentSplit, sid)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="split_not_found")
    return row


def update_split(db: Session, sid: str, body: PaymentSplitUpdate) -> PaymentSplit:
    row = get_split_or_404(db, sid)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    if body.status and body.status.upper() == "SETTLED" and not row.settled_at:
        row.settled_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_split(db: Session, sid: str) -> None:
    row = get_split_or_404(db, sid)
    db.delete(row)
    db.commit()


# --- payments ---


def list_payments(db: Session, *, order_id: str | None = None, limit: int = 100) -> list[Payment]:
    q = db.query(Payment)
    if order_id:
        q = q.filter(Payment.order_id == order_id)
    return q.order_by(Payment.created_at.desc()).limit(limit).all()


def create_payment(db: Session, body: PaymentIn) -> Payment:
    pid = body.id or new_id()
    if db.get(Payment, pid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="payment_id_exists")
    data = body.model_dump(exclude={"id"})
    data["created_at"] = data.get("created_at") or _epoch()
    row = Payment(id=pid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_payment_or_404(db: Session, pid: str) -> Payment:
    row = db.get(Payment, pid)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment_not_found")
    return row


def update_payment(db: Session, pid: str, body: PaymentUpdate) -> Payment:
    row = get_payment_or_404(db, pid)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


def delete_payment(db: Session, pid: str) -> None:
    row = get_payment_or_404(db, pid)
    db.delete(row)
    db.commit()


# --- webhooks ---


def list_webhooks(
    db: Session, *, partner_type: str | None = None, partner_id: str | None = None, limit: int = 100
) -> list[WebhookEndpoint]:
    q = db.query(WebhookEndpoint)
    if partner_type:
        q = q.filter(WebhookEndpoint.partner_type == partner_type.upper())
    if partner_id:
        q = q.filter(WebhookEndpoint.partner_id == partner_id)
    return q.order_by(WebhookEndpoint.created_at.desc()).limit(limit).all()


def create_webhook(db: Session, body: WebhookEndpointIn) -> WebhookEndpoint:
    wid = body.id or new_id()
    if db.get(WebhookEndpoint, wid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="webhook_id_exists")
    row = WebhookEndpoint(id=wid, **body.model_dump(exclude={"id"}))
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_webhook_or_404(db: Session, wid: str) -> WebhookEndpoint:
    row = db.get(WebhookEndpoint, wid)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="webhook_not_found")
    return row


def update_webhook(db: Session, wid: str, body: WebhookEndpointUpdate) -> WebhookEndpoint:
    row = get_webhook_or_404(db, wid)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    row.updated_at = _utcnow()
    db.commit()
    db.refresh(row)
    return row


def delete_webhook(db: Session, wid: str) -> None:
    row = get_webhook_or_404(db, wid)
    db.delete(row)
    db.commit()


def rotate_webhook_secret(db: Session, wid: str) -> WebhookSecretRotateOut:
    row = get_webhook_or_404(db, wid)
    secret, secret_ref = generate_webhook_secret(row.partner_id)
    row.secret_ref = secret_ref
    row.updated_at = _utcnow()
    db.commit()
    return WebhookSecretRotateOut(endpoint_id=wid, secret=secret, secret_ref=secret_ref)


# --- gateway events ---


def list_gateway_events(
    db: Session, *, order_id: str | None = None, locker_id: str | None = None, limit: int = 100
) -> list[GatewayEvent]:
    q = db.query(GatewayEvent)
    if order_id:
        q = q.filter(GatewayEvent.order_id == order_id)
    if locker_id:
        q = q.filter(GatewayEvent.locker_id == locker_id)
    return q.order_by(GatewayEvent.created_at.desc()).limit(limit).all()


def create_gateway_event(db: Session, body: GatewayEventIn) -> GatewayEvent:
    eid = body.id or new_id()
    if db.get(GatewayEvent, eid):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="event_id_exists")
    data = body.model_dump(exclude={"id"})
    data["created_at"] = data.get("created_at") or _epoch()
    row = GatewayEvent(id=eid, **data)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_gateway_event_or_404(db: Session, eid: str) -> GatewayEvent:
    row = db.get(GatewayEvent, eid)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="gateway_event_not_found")
    return row


def delete_gateway_event(db: Session, eid: str) -> None:
    row = get_gateway_event_or_404(db, eid)
    db.delete(row)
    db.commit()
