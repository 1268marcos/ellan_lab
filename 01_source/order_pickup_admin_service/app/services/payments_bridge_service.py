from __future__ import annotations

from datetime import datetime, timezone

import httpx
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.order_ops import PaymentTransactionRecord
from app.services.crypto_util import new_id

CAPTURED_STATUSES = frozenset({"APPROVED", "CAPTURED", "SETTLED", "PAID"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _upsert_tx(db: Session, payload: dict, *, source: str) -> PaymentTransactionRecord:
    now = _utcnow()
    tx_id = str(payload["id"])
    row = db.get(PaymentTransactionRecord, tx_id)
    approved_raw = payload.get("approved_at")
    approved_at = None
    if approved_raw:
        if isinstance(approved_raw, datetime):
            approved_at = approved_raw
        else:
            approved_at = datetime.fromisoformat(str(approved_raw).replace("Z", "+00:00"))
    fields = dict(
        order_id=str(payload["order_id"]),
        gateway=str(payload.get("gateway") or "UNKNOWN"),
        gateway_transaction_id=payload.get("gateway_transaction_id"),
        amount_cents=int(payload["amount_cents"]),
        currency=str(payload.get("currency") or "BRL"),
        payment_method=str(payload.get("payment_method") or "CARD"),
        status=str(payload.get("status") or "INITIATED").upper(),
        gateway_fee_cents=int(payload.get("gateway_fee_cents") or 0),
        net_amount_cents=payload.get("net_amount_cents"),
        reconciliation_status=str(payload.get("reconciliation_status") or "PENDING").upper(),
        approved_at=approved_at,
        synced_at=now,
        source=source,
        updated_at=now,
    )
    if row:
        for k, v in fields.items():
            setattr(row, k, v)
    else:
        row = PaymentTransactionRecord(id=tx_id, created_at=now, **fields)
        db.add(row)
    return row


def list_payment_transactions(
    db: Session, *, order_id: str | None, status: str | None, limit: int, offset: int
) -> tuple[list[PaymentTransactionRecord], int]:
    q = db.query(PaymentTransactionRecord)
    if order_id:
        q = q.filter(PaymentTransactionRecord.order_id == order_id)
    if status:
        q = q.filter(PaymentTransactionRecord.status == status.upper())
    total = q.count()
    rows = q.order_by(PaymentTransactionRecord.created_at.desc()).offset(offset).limit(limit).all()
    return rows, total


def captured_totals_for_order(db: Session, order_id: str) -> tuple[int, int, str | None] | None:
    """Soma transações capturadas do espelho gateway. None se não houver txs."""
    txs = db.query(PaymentTransactionRecord).filter(PaymentTransactionRecord.order_id == order_id).all()
    if not txs:
        return None
    captured = 0
    fees = 0
    refs: list[str] = []
    for tx in txs:
        if tx.status in CAPTURED_STATUSES:
            captured += tx.amount_cents
            fees += tx.gateway_fee_cents or 0
            refs.append(tx.id)
    payment_ref = refs[0] if len(refs) == 1 else f"multi:{len(refs)}"
    return captured, fees, payment_ref


def sync_from_payments_admin(db: Session, order_id: str | None = None) -> dict[str, int]:
    """Pull payment-transactions do payments-admin para o espelho local."""
    base = get_settings().payments_admin_base_url
    if not base:
        return {"synced": 0, "skipped": 0, "error": "PAYMENTS_ADMIN_BASE_URL not configured"}
    base = base.rstrip("/")
    params: dict[str, str | int] = {"limit": 500}
    if order_id:
        params["order_id"] = order_id
    url = f"{base}/payment-transactions"
    synced = 0
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        return {"synced": 0, "skipped": 0, "error": str(exc)}
    items = data.get("items") or []
    for item in items:
        _upsert_tx(db, item, source="PAYMENTS_ADMIN")
        synced += 1
    db.commit()
    return {"synced": synced, "skipped": 0}


def seed_payment_transaction_demo(db: Session, order_id: str, *, amount_cents: int = 4990) -> None:
    tx_id = f"pay-tx-{order_id[:20]}"
    if db.get(PaymentTransactionRecord, tx_id):
        return
    now = _utcnow()
    db.add(
        PaymentTransactionRecord(
            id=tx_id,
            order_id=order_id,
            gateway="STRIPE",
            gateway_transaction_id=f"ch_{order_id[:12]}",
            amount_cents=amount_cents,
            currency="BRL",
            payment_method="PIX",
            status="APPROVED",
            gateway_fee_cents=max(1, int(amount_cents * 0.029)),
            net_amount_cents=amount_cents - max(1, int(amount_cents * 0.029)),
            reconciliation_status="PENDING",
            approved_at=now,
            synced_at=now,
            source="SEED",
            created_at=now,
            updated_at=now,
        )
    )
