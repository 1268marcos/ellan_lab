from __future__ import annotations

import json
from typing import Any

from redis import Redis
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.services import wallet_service


def handle_event(db: Session, r: Redis | None, obj: dict[str, Any]) -> None:
    et = obj.get("type")
    pl = obj.get("payload") or {}
    if et == "payment.confirmed":
        uid = str(pl.get("user_id", ""))
        amt = int(pl.get("amount", 0) or 0)
        txid = str(pl.get("transaction_id", et))
        if uid and amt > 0:
            wallet_service.credit_wallet(db, r, uid, amt, txid, tx_type="payment_confirmed")
    elif et == "order.expired":
        uid = str(pl.get("user_id", ""))
        amt = int(pl.get("penalty_amount", 0) or 0)
        txid = str(pl.get("transaction_id", et))
        if uid and amt > 0:
            try:
                wallet_service.debit_wallet(db, r, uid, amt, txid)
            except ValueError:
                pass


def consume_once(r: Redis, db_factory: Any, stream_key: str | None = None) -> int:
    settings = get_settings()
    key = stream_key or settings.wallet_events_stream
    msgs = r.xread({key: "0-0"}, count=5, block=0)
    processed = 0
    for _sk, items in msgs or []:
        for _mid, fields in items:
            data = fields.get(b"data") or fields.get("data")
            if isinstance(data, bytes):
                data = data.decode()
            if not data:
                continue
            try:
                obj = json.loads(data)
            except json.JSONDecodeError:
                continue
            db = db_factory()
            try:
                handle_event(db, r, obj)
                db.commit()
                processed += 1
            finally:
                db.close()
    return processed
