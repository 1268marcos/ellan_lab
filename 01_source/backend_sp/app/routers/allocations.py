from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import os

from app.core.db import get_conn

router = APIRouter(prefix="/locker", tags=["locker"])

# --------- helpers ---------

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _now_iso() -> str:
    return _now().isoformat()

def _machine_id() -> str:
    return os.getenv("MACHINE_ID", "CACIFO-PT-001")

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

def _door_state_get(conn, machine_id: str, door_id: int) -> Optional[str]:
    cur = conn.execute(
        "SELECT state FROM door_state WHERE machine_id=? AND door_id=?",
        (machine_id, door_id),
    )
    row = cur.fetchone()
    return row[0] if row else None

def _door_state_upsert(conn, machine_id: str, door_id: int, state: str, product_id: Optional[str] = None) -> None:
    conn.execute(
        """
        INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(machine_id, door_id)
        DO UPDATE SET state=excluded.state, product_id=excluded.product_id, updated_at=excluded.updated_at
        """,
        (machine_id, door_id, state, product_id, _now_iso()),
    )

def _bootstrap_24(conn, machine_id: str) -> None:
    for i in range(1, 25):
        cur = conn.execute(
            "SELECT 1 FROM door_state WHERE machine_id=? AND door_id=?",
            (machine_id, i),
        )
        if cur.fetchone() is None:
            _door_state_upsert(conn, machine_id, i, "AVAILABLE", None)
    conn.commit()

def _expire_old_allocations(conn, machine_id: str) -> int:
    now_iso = _now_iso()
    cur = conn.execute(
        """
        SELECT allocation_id, door_id
        FROM allocations
        WHERE machine_id=? AND state IN ('RESERVED') AND expires_at < ?
        """,
        (machine_id, now_iso),
    )
    rows = cur.fetchall()
    expired = 0
    for allocation_id, door_id in rows:
        st = _door_state_get(conn, machine_id, int(door_id))
        if st == "RESERVED":
            _door_state_upsert(conn, machine_id, int(door_id), "AVAILABLE", None)
        conn.execute(
            "UPDATE allocations SET state='EXPIRED' WHERE allocation_id=?",
            (allocation_id,),
        )
        expired += 1

    if expired:
        conn.commit()
    return expired

# --------- models ---------

class AllocateIn(BaseModel):
    # CONTRATO NOVO (order_pickup_service)
    sku_id: Optional[str] = None

    # COMPAT LEGADO (se algum caller antigo mandar)
    product_id: Optional[str] = None

    ttl_sec: int = 120
    request_id: Optional[str] = None
    desired_slot: Optional[int] = None

class AllocateOut(BaseModel):
    allocation_id: str
    slot: int
    machine_id: str
    state: str
    expires_at: str

class CommitIn(BaseModel):
    sale_id: Optional[str] = None
    request_id: Optional[str] = None

class ReleaseIn(BaseModel):
    request_id: Optional[str] = None

# --------- endpoints ---------

@router.post("/allocate", response_model=AllocateOut)
def allocate(payload: AllocateIn, request: Request):
    machine_id = _machine_id()

    # normaliza o identificador do item (preferindo sku_id)
    prod = payload.sku_id or payload.product_id
    if not prod:
        _raise(
            400,
            err_type="MISSING_SKU_ID",
            message="sku_id is required (or product_id for legacy callers)",
            retryable=False,
            machine_id=machine_id,
            endpoint=str(request.url.path),
        )

    try:
        conn = get_conn()
        _bootstrap_24(conn, machine_id)
        _expire_old_allocations(conn, machine_id)

        ttl = int(payload.ttl_sec)
        ttl = max(30, min(ttl, 600))

        # idempotência por request_id
        if payload.request_id:
            cur = conn.execute(
                """
                SELECT allocation_id, door_id, state, expires_at
                FROM allocations
                WHERE machine_id=? AND request_id=? AND state IN ('RESERVED','COMMITTED')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (machine_id, payload.request_id),
            )
            existing = cur.fetchone()
            if existing:
                allocation_id, door_id, st, expires_at = existing
                return AllocateOut(
                    allocation_id=allocation_id,
                    machine_id=machine_id,
                    slot=int(door_id),
                    state=st,
                    expires_at=expires_at,
                )

        # escolhe slot desejado ou a primeira AVAILABLE
        if payload.desired_slot is not None:
            desired_slot = int(payload.desired_slot)
            _ensure_slot_range(desired_slot)

            cur = conn.execute(
                """
                SELECT door_id
                FROM door_state
                WHERE machine_id=? AND door_id=? AND state='AVAILABLE'
                LIMIT 1
                """,
                (machine_id, desired_slot),
            )
            row = cur.fetchone()
            if not row:
                _raise(
                    409,
                    err_type="DESIRED_SLOT_UNAVAILABLE",
                    message="desired slot is not AVAILABLE",
                    retryable=True,
                    machine_id=machine_id,
                    endpoint=str(request.url.path),
                    slot=desired_slot,
                )
            door_id = desired_slot
        else:
            cur = conn.execute(
                """
                SELECT door_id
                FROM door_state
                WHERE machine_id=? AND state='AVAILABLE'
                ORDER BY door_id
                LIMIT 1
                """,
                (machine_id,),
            )
            row = cur.fetchone()
            if not row:
                _raise(
                    409,
                    err_type="NO_AVAILABLE_SLOTS",
                    message="no AVAILABLE slots",
                    retryable=True,
                    machine_id=machine_id,
                    endpoint=str(request.url.path),
                )

            door_id = int(row[0])

        # claim atômico
        updated_at = _now_iso()
        res = conn.execute(
            """
            UPDATE door_state
            SET state='RESERVED', product_id=?, updated_at=?
            WHERE machine_id=? AND door_id=? AND state='AVAILABLE'
            """,
            (prod, updated_at, machine_id, door_id),
        )
        if res.rowcount == 0:
            conn.rollback()
            _raise(
                409,
                err_type="SLOT_TAKEN",
                message="slot was taken, retry",
                retryable=True,
                machine_id=machine_id,
                endpoint=str(request.url.path),
                slot=door_id,
            )

        allocation_id = f"al_{uuid.uuid4().hex}"
        expires_at = (_now() + timedelta(seconds=ttl)).isoformat()

        try:
            conn.execute(
                """
                INSERT INTO allocations(allocation_id, machine_id, door_id, state, created_at, expires_at, sale_id, request_id)
                VALUES (?, ?, ?, 'RESERVED', ?, ?, NULL, ?)
                """,
                (allocation_id, machine_id, door_id, _now_iso(), expires_at, payload.request_id),
            )
        except Exception as e:
            # desfaz reserva se insert falhar
            st = _door_state_get(conn, machine_id, door_id)
            if st == "RESERVED":
                _door_state_upsert(conn, machine_id, door_id, "AVAILABLE", None)
            conn.commit()
            _raise(
                409,
                err_type="RESOURCE_ALLOCATION_CONFLICT",
                message="allocation insert failed",
                retryable=True,
                machine_id=machine_id,
                endpoint=str(request.url.path),
                slot=door_id,
                allocation_id=allocation_id,
                db_error=str(e),
            )

        conn.commit()

        return AllocateOut(
            allocation_id=allocation_id,
            machine_id=machine_id,
            slot=door_id,
            state="RESERVED",
            expires_at=expires_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        _raise(
            500,
            err_type="DB_OPERATION_FAILED",
            message=str(e),
            retryable=True,
            machine_id=machine_id,
            endpoint=str(request.url.path),
        )

@router.post("/allocations/{allocation_id}/commit")
def commit(allocation_id: str, payload: CommitIn, request: Request):
    machine_id = _machine_id()

    try:
        conn = get_conn()
        _expire_old_allocations(conn, machine_id)

        cur = conn.execute(
            """
            SELECT door_id, state, expires_at
            FROM allocations
            WHERE allocation_id=? AND machine_id=?
            """,
            (allocation_id, machine_id),
        )
        row = cur.fetchone()
        if not row:
            _raise(
                404,
                err_type="ALLOCATION_NOT_FOUND",
                message="allocation not found",
                retryable=False,
                machine_id=machine_id,
                endpoint=str(request.url.path),
                allocation_id=allocation_id,
            )

        door_id, st, expires_at = int(row[0]), row[1], row[2]

        if st in ("RELEASED", "EXPIRED"):
            _raise(
                409,
                err_type="ALLOCATION_NOT_ACTIVE",
                message=f"allocation not active (state={st})",
                retryable=False,
                machine_id=machine_id,
                endpoint=str(request.url.path),
                allocation_id=allocation_id,
                slot=door_id,
                state=st,
            )

        if expires_at < _now_iso():
            conn.execute("UPDATE allocations SET state='EXPIRED' WHERE allocation_id=?", (allocation_id,))
            if _door_state_get(conn, machine_id, door_id) == "RESERVED":
                _door_state_upsert(conn, machine_id, door_id, "AVAILABLE", None)
            conn.commit()
            _raise(
                409,
                err_type="ALLOCATION_EXPIRED",
                message="allocation expired",
                retryable=False,
                machine_id=machine_id,
                endpoint=str(request.url.path),
                allocation_id=allocation_id,
                slot=door_id,
            )

        conn.execute(
            """
            UPDATE allocations
            SET state='COMMITTED', sale_id=?, request_id=?
            WHERE allocation_id=? AND machine_id=?
            """,
            (payload.sale_id, payload.request_id, allocation_id, machine_id),
        )
        conn.commit()

        return {
            "ok": True,
            "machine_id": machine_id,
            "endpoint": str(request.url.path),
            "allocation_id": allocation_id,
            "door_id": door_id,  # legado
            "slot": door_id,     # contrato “amigável”
            "state": "COMMITTED",
        }

    except HTTPException:
        raise
    except Exception as e:
        _raise(
            500,
            err_type="DB_OPERATION_FAILED",
            message=str(e),
            retryable=True,
            machine_id=machine_id,
            endpoint=str(request.url.path),
            allocation_id=allocation_id,
        )

@router.post("/allocations/{allocation_id}/release")
def release(allocation_id: str, payload: ReleaseIn, request: Request):
    machine_id = _machine_id()

    try:
        conn = get_conn()

        cur = conn.execute(
            """
            SELECT door_id, state
            FROM allocations
            WHERE allocation_id=? AND machine_id=?
            """,
            (allocation_id, machine_id),
        )
        row = cur.fetchone()
        if not row:
            _raise(
                404,
                err_type="ALLOCATION_NOT_FOUND",
                message="allocation not found",
                retryable=False,
                machine_id=machine_id,
                endpoint=str(request.url.path),
                allocation_id=allocation_id,
            )

        door_id, st = int(row[0]), row[1]

        if st in ("RELEASED", "EXPIRED"):
            return {
                "ok": True,
                "machine_id": machine_id,
                "endpoint": str(request.url.path),
                "allocation_id": allocation_id,
                "door_id": door_id,  # legado
                "slot": door_id,     # contrato “amigável”
                "state": st,
            }

        if _door_state_get(conn, machine_id, door_id) == "RESERVED":
            _door_state_upsert(conn, machine_id, door_id, "AVAILABLE", None)

        conn.execute(
            """
            UPDATE allocations
            SET state='RELEASED', request_id=?
            WHERE allocation_id=? AND machine_id=?
            """,
            (payload.request_id, allocation_id, machine_id),
        )
        conn.commit()

        return {
            "ok": True,
            "machine_id": machine_id,
            "endpoint": str(request.url.path),
            "allocation_id": allocation_id,
            "door_id": door_id,  # legado
            "slot": door_id,     # contrato “amigável”
            "state": "RELEASED",
        }

    except HTTPException:
        raise
    except Exception as e:
        _raise(
            500,
            err_type="DB_OPERATION_FAILED",
            message=str(e),
            retryable=True,
            machine_id=machine_id,
            endpoint=str(request.url.path),
            allocation_id=allocation_id,
        )