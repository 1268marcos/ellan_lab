# 01_source/order_pickup_service/app/repositories/order_repository.py
# 13/04/2026

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
import uuid

from sqlalchemy import text

from app.core.db import SessionLocal


def _now() -> datetime:
    return datetime.utcnow()


def _value(v: Any) -> Any:
    return getattr(v, "value", v)


class OrderRepository:
    def create_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = _now()

        row = {
            "id": payload.get("id") or str(uuid.uuid4()),
            "region": payload["region"],
            "totem_id": payload.get("locker_id") or payload.get("totem_id"),
            "locker_id": payload.get("locker_id"),
            "sku_id": payload["sku_id"],
            "amount_cents": int(payload["amount_cents"]),
            "currency": payload.get("currency", "BRL"),
            "payment_method": payload["payment_method"],
            "status": _value(payload.get("status", "PAYMENT_PENDING")),
            "payment_status": _value(payload.get("payment_status", "CREATED")),
            "channel": _value(payload.get("channel", "KIOSK")),
            "user_id": payload.get("user_id"),
            "created_at": payload.get("created_at") or now,
            "updated_at": payload.get("updated_at") or now,
        }

        sql = text(
            """
            INSERT INTO orders (
                id,
                region,
                totem_id,
                locker_id,
                sku_id,
                amount_cents,
                currency,
                payment_method,
                status,
                payment_status,
                channel,
                user_id,
                created_at,
                updated_at
            )
            VALUES (
                :id,
                :region,
                :totem_id,
                :locker_id,
                :sku_id,
                :amount_cents,
                :currency,
                :payment_method,
                :status,
                :payment_status,
                :channel,
                :user_id,
                :created_at,
                :updated_at
            )
            """
        )

        with SessionLocal() as db:
            db.execute(sql, row)
            db.commit()

        return row

    def update_payment_status(self, order_id: str, payment_status: str) -> Dict[str, Any]:
        sql = text(
            """
            UPDATE orders
               SET payment_status = :payment_status,
                   updated_at = :updated_at
             WHERE id = :order_id
            """
        )

        payload = {
            "order_id": str(order_id).strip(),
            "payment_status": payment_status,
            "updated_at": _now(),
        }

        with SessionLocal() as db:
            db.execute(sql, payload)
            db.commit()

        return {
            "order_id": payload["order_id"],
            "payment_status": payment_status,
        }