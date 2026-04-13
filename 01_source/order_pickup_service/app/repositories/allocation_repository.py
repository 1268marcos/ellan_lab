# 01_source/order_pickup_service/app/repositories/allocation_repository.py
# 13/04/2026

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict
import uuid

from sqlalchemy import text

from app.core.db import SessionLocal


def _now() -> datetime:
    return datetime.utcnow()


def _allocation_id() -> str:
    return f"al_{uuid.uuid4().hex}"


class AllocationRepository:
    def allocate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        now = _now()
        ttl_seconds = int(payload.get("ttl_seconds") or 900)
        locked_until = now + timedelta(seconds=ttl_seconds)

        row = {
            "id": payload.get("id") or _allocation_id(),
            "order_id": payload["order_id"],
            "locker_id": payload["locker_id"],
            "slot": int(payload["slot"]),
            "state": payload.get("state", "RESERVED_PENDING_PAYMENT"),
            "locked_until": locked_until,
            "created_at": payload.get("created_at") or now,
            "updated_at": payload.get("updated_at") or now,
            "allocated_at": payload.get("allocated_at") or now,
            "slot_size": payload.get("slot_size"),
            "ttl_seconds": ttl_seconds,
        }

        sql = text(
            """
            INSERT INTO allocations (
                id,
                order_id,
                locker_id,
                slot,
                state,
                locked_until,
                created_at,
                updated_at,
                allocated_at,
                slot_size,
                ttl_seconds
            )
            VALUES (
                :id,
                :order_id,
                :locker_id,
                :slot,
                :state,
                :locked_until,
                :created_at,
                :updated_at,
                :allocated_at,
                :slot_size,
                :ttl_seconds
            )
            """
        )

        with SessionLocal() as db:
            db.execute(sql, row)
            db.commit()

        return row
    
