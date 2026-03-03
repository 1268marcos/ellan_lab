# 01_source/backend_sp/app/routers/locker_state.py
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Literal, Optional, List

from app.core.db import get_conn

router = APIRouter(prefix="/locker", tags=["locker"])

SlotState = Literal[
    "AVAILABLE",
    "RESERVED",
    "PAID_PENDING_PICKUP",
    "PICKED_UP",
    "OUT_OF_STOCK",
]

class SlotView(BaseModel):
    slot: int
    state: SlotState
    product_id: Optional[str] = None
    updated_at: str

class SetSlotStateIn(BaseModel):
    state: SlotState
    product_id: Optional[str] = None

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _machine_id() -> str:
    import os
    return os.getenv("MACHINE_ID", "CACIFO-SP-001")

def _raise(status: int, *, err_type: str, message: str, retryable: bool, **extra):
    detail = {"type": err_type, "message": message, "retryable": retryable}
    if extra:
        detail.update(extra)
    raise HTTPException(status_code=status, detail=detail)

def _ensure_slot_range(slot: int) -> None:
    if slot < 1 or slot > 24:
        _raise(
            400,
            err_type="INVALID_SLOT",
            message="slot must be 1..24",
            retryable=False,
            slot=slot,
            min_slot=1,
            max_slot=24,
        )

def _get_slot(conn, machine_id: str, slot: int) -> Optional[dict]:
    cur = conn.execute(
        "SELECT state, product_id, updated_at FROM door_state WHERE machine_id=? AND door_id=?",
        (machine_id, slot),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {"state": row[0], "product_id": row[1], "updated_at": row[2]}

def _upsert_slot(conn, machine_id: str, slot: int, state: str, product_id: Optional[str]) -> dict:
    now = _now_iso()
    conn.execute(
        """
        INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(machine_id, door_id)
        DO UPDATE SET state=excluded.state, product_id=excluded.product_id, updated_at=excluded.updated_at
        """,
        (machine_id, slot, state, product_id, now),
    )
    conn.commit()
    return {"slot": slot, "state": state, "product_id": product_id, "updated_at": now}

@router.get("/slots", response_model=List[SlotView])
def list_slots(request: Request):
    mid = _machine_id()
    try:
        conn = get_conn()
    except Exception as e:
        _raise(
            500,
            err_type="DB_CONNECTION_FAILED",
            message=str(e),
            retryable=True,
            service="backend",
            endpoint=str(request.url.path),
            machine_id=mid,
        )

    # bootstrap resiliente
    try:
        for i in range(1, 25):
            if _get_slot(conn, mid, i) is None:
                _upsert_slot(conn, mid, i, "AVAILABLE", None)
    except Exception as e:
        _raise(
            500,
            err_type="DB_BOOTSTRAP_FAILED",
            message=str(e),
            retryable=True,
            service="backend",
            endpoint=str(request.url.path),
            machine_id=mid,
        )

    try:
        cur = conn.execute(
            "SELECT door_id, state, product_id, updated_at FROM door_state WHERE machine_id=? ORDER BY door_id",
            (mid,),
        )
        out = []
        for door_id, state, product_id, updated_at in cur.fetchall():
            out.append(SlotView(slot=int(door_id), state=state, product_id=product_id, updated_at=updated_at))
        return out
    except Exception as e:
        _raise(
            500,
            err_type="DB_QUERY_FAILED",
            message=str(e),
            retryable=True,
            service="backend",
            endpoint=str(request.url.path),
            machine_id=mid,
        )

@router.get("/slots/{slot}", response_model=SlotView)
def get_slot(slot: int, request: Request):
    _ensure_slot_range(slot)
    mid = _machine_id()

    try:
        conn = get_conn()
        row = _get_slot(conn, mid, slot)
        if row is None:
            row = _upsert_slot(conn, mid, slot, "AVAILABLE", None)
        return SlotView(slot=slot, state=row["state"], product_id=row["product_id"], updated_at=row["updated_at"])
    except HTTPException:
        raise
    except Exception as e:
        _raise(
            500,
            err_type="DB_OPERATION_FAILED",
            message=str(e),
            retryable=True,
            service="backend",
            endpoint=str(request.url.path),
            machine_id=mid,
            slot=slot,
        )

@router.post("/slots/{slot}/set-state")
def set_slot_state(slot: int, payload: SetSlotStateIn, request: Request):
    _ensure_slot_range(slot)
    mid = _machine_id()

    try:
        conn = get_conn()
        prev = _get_slot(conn, mid, slot)
        new_row = _upsert_slot(conn, mid, slot, payload.state, payload.product_id)

        return {
            "ok": True,
            "machine_id": mid,
            "endpoint": str(request.url.path),
            "slot": slot,
            "old_state": prev["state"] if prev else None,
            "state": new_row["state"],
            "product_id": new_row["product_id"],
            "updated_at": new_row["updated_at"],
        }
    except HTTPException:
        raise
    except Exception as e:
        _raise(
            500,
            err_type="DB_UPDATE_FAILED",
            message=str(e),
            retryable=True,
            service="backend",
            endpoint=str(request.url.path),
            machine_id=mid,
            slot=slot,
            desired_state=payload.state,
        )