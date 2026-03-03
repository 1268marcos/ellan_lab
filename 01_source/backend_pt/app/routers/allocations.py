# /home/marcos/ellan_lab/01_source/backend_pt/app/routers/allocations.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
import os

from app.core.db import get_conn

# router = APIRouter(prefix="/locker", tags=["locker-allocations"])
router = APIRouter(prefix="/locker", tags=["locker"])

# --------- helpers ---------

def _now() -> datetime:
    return datetime.now(timezone.utc)

def _now_iso() -> str:
    return _now().isoformat()

def _machine_id() -> str:
    # defina MACHINE_ID=CACIFO-SP-001 / CACIFO-PT-001 no docker-compose
    return os.getenv("MACHINE_ID", "CACIFO-XX-001")

def _ensure_slot_range(slot: int) -> None:
    if slot < 1 or slot > 24:
        raise HTTPException(status_code=400, detail="slot must be 1..24")

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
    # garante as 24 portas existirem
    for i in range(1, 25):
        cur = conn.execute(
            "SELECT 1 FROM door_state WHERE machine_id=? AND door_id=?",
            (machine_id, i),
        )
        if cur.fetchone() is None:
            _door_state_upsert(conn, machine_id, i, "AVAILABLE", None)
    conn.commit()

def _expire_old_allocations(conn, machine_id: str) -> int:
    """
    Marca como EXPIRED o que venceu e solta a porta (volta AVAILABLE),
    mas só se a porta ainda estiver RESERVED (não mexe em PAID_PENDING_PICKUP etc.)
    """
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
        # libera porta se ainda estiver RESERVED
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
    # opcional, para quando você tiver SKU/bolo diferente
    product_id: Optional[str] = None
    ttl_sec: int = 120
    request_id: Optional[str] = None

class AllocateOut(BaseModel):
    allocation_id: str
    machine_id: str
    door_id: int
    state: str
    expires_at: str

class CommitIn(BaseModel):
    sale_id: Optional[str] = None
    request_id: Optional[str] = None

class ReleaseIn(BaseModel):
    request_id: Optional[str] = None

# --------- endpoints ---------

@router.post("/allocate", response_model=AllocateOut)
def allocate(payload: AllocateIn):
    conn = get_conn()
    machine_id = _machine_id()

    _bootstrap_24(conn, machine_id)
    _expire_old_allocations(conn, machine_id)

    ttl = int(payload.ttl_sec)
    ttl = max(30, min(ttl, 600))

    # ✅ IDPOTÊNCIA: se o mesmo request_id repetir, devolve a mesma allocation ativa
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
                door_id=int(door_id),
                state=st,
                expires_at=expires_at,
            )

    # escolhe a primeira porta AVAILABLE
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
        raise HTTPException(status_code=409, detail="no AVAILABLE slots")

    door_id = int(row[0])

    # claim atômico: só reserva se ainda estava AVAILABLE
    updated_at = _now_iso()
    res = conn.execute(
        """
        UPDATE door_state
        SET state='RESERVED', product_id=?, updated_at=?
        WHERE machine_id=? AND door_id=? AND state='AVAILABLE'
        """,
        (payload.product_id, updated_at, machine_id, door_id),
    )
    if res.rowcount == 0:
        conn.rollback()
        raise HTTPException(status_code=409, detail="slot was taken, retry")

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
        # rollback de segurança: desfaz a reserva no door_state
        # (só se ainda RESERVED)
        st = _door_state_get(conn, machine_id, door_id)
        if st == "RESERVED":
            _door_state_upsert(conn, machine_id, door_id, "AVAILABLE", None)
        conn.commit()
        raise HTTPException(status_code=409, detail=f"allocation insert failed: {str(e)}")

    conn.commit()

    return AllocateOut(
        allocation_id=allocation_id,
        machine_id=machine_id,
        door_id=door_id,
        state="RESERVED",
        expires_at=expires_at,
    )

@router.post("/allocations/{allocation_id}/commit")
def commit(allocation_id: str, payload: CommitIn):
    conn = get_conn()
    machine_id = _machine_id()

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
        raise HTTPException(status_code=404, detail="allocation not found")

    door_id, st, expires_at = int(row[0]), row[1], row[2]
    if st in ("RELEASED", "EXPIRED"):
        raise HTTPException(status_code=409, detail=f"allocation not active (state={st})")

    # se expirou, trata como expired
    if expires_at < _now_iso():
        conn.execute("UPDATE allocations SET state='EXPIRED' WHERE allocation_id=?", (allocation_id,))
        # libera porta se ainda RESERVED
        if _door_state_get(conn, machine_id, door_id) == "RESERVED":
            _door_state_upsert(conn, machine_id, door_id, "AVAILABLE", None)
        conn.commit()
        raise HTTPException(status_code=409, detail="allocation expired")

    # Commit mantém a porta RESERVED; o pagamento depois vira PAID_PENDING_PICKUP via set-state
    conn.execute(
        """
        UPDATE allocations
        SET state='COMMITTED', sale_id=?, request_id=?
        WHERE allocation_id=? AND machine_id=?
        """,
        (payload.sale_id, payload.request_id, allocation_id, machine_id),
    )
    conn.commit()

    return {"ok": True, "allocation_id": allocation_id, "machine_id": machine_id, "door_id": door_id, "state": "COMMITTED"}

@router.post("/allocations/{allocation_id}/release")
def release(allocation_id: str, payload: ReleaseIn):
    conn = get_conn()
    machine_id = _machine_id()

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
        raise HTTPException(status_code=404, detail="allocation not found")

    door_id, st = int(row[0]), row[1]
    if st in ("RELEASED", "EXPIRED"):
        return {"ok": True, "allocation_id": allocation_id, "state": st, "door_id": door_id}

    # libera porta se estiver RESERVED (não mexe se já pagou/retirou)
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

    return {"ok": True, "allocation_id": allocation_id, "machine_id": machine_id, "door_id": door_id, "state": "RELEASED"}