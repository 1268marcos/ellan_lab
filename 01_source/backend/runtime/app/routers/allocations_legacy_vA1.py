# 01_source/backend/runtime/app/routers/allocations.py
# RUNTIME = EXECUTOR PURO
# 01/04/2026
# 10/04/2026 - Update em def commit() e def release() atualizado para incluir slot no where

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional
import uuid

from app.core.db import get_conn
from app.core.locker_runtime_resolver import resolve_runtime_locker

router = APIRouter(prefix="/locker", tags=["locker"])


# =========================================================
# HELPERS
# =========================================================

def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _raise(status, *, err_type, message, retryable, **extra):
    detail = {"type": err_type, "message": message, "retryable": retryable}
    if extra:
        detail.update(extra)
    raise HTTPException(status_code=status, detail=detail)


# =========================================================
# MODELS (NOVO CONTRATO)
# =========================================================

class AllocateCommand(BaseModel):
    slot: int
    allocation_id: Optional[str] = None


class CommitCommand(BaseModel):
    pass


class ReleaseCommand(BaseModel):
    pass


# =========================================================
# ALLOCATE (EXECUTE ONLY)
# =========================================================

@router.post("/allocate")
def allocate(
    payload: AllocateCommand,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    locker_ctx = resolve_runtime_locker(x_locker_id)

    locker_id = locker_ctx["locker_id"]
    machine_id = locker_ctx["machine_id"]

    slot = int(payload.slot)

    try:
        conn = get_conn()

        conn.execute(
            """
            INSERT INTO allocations (
                allocation_id,
                machine_id,
                door_id,
                state,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                allocation_id,
                machine_id,
                slot,
                "RESERVED",
                _now_iso(),
                _now_iso(),  # pode ajustar TTL depois
            ),
        )

        conn.execute(
            """
            INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
            VALUES (?, ?, 'AVAILABLE', NULL, ?)
            ON CONFLICT(machine_id, door_id) DO NOTHING
            """,
            (machine_id, slot, _now_iso()),
        )

        res = conn.execute(
            """
            UPDATE door_state
            SET state='RESERVED', updated_at=?
            WHERE machine_id=? AND door_id=? AND state='AVAILABLE'
            """,
            (_now_iso(), machine_id, slot),
        )

        if res.rowcount == 0:
            _raise(
                409,
                err_type="SLOT_NOT_AVAILABLE",
                message="slot not available",
                retryable=True,
                locker_id=locker_id,
                slot=slot,
            )

        allocation_id = payload.allocation_id or f"al_{uuid.uuid4().hex}"

        conn.commit()

        return {
            "ok": True,
            "allocation_id": allocation_id,
            "slot": slot,
            "locker_id": locker_id,
            "state": "RESERVED",
        }

    except HTTPException:
        raise
    except Exception as e:
        _raise(
            500,
            err_type="RUNTIME_EXECUTION_FAILED",
            message=str(e),
            retryable=True,
            locker_id=locker_id,
            slot=slot,
        )


# =========================================================
# COMMIT (EXECUTE ONLY)
# =========================================================

@router.post("/allocations/{allocation_id}/commit")
def commit(
    allocation_id: str,
    payload: CommitCommand,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):

    locker_ctx = resolve_runtime_locker(x_locker_id)

    machine_id = locker_ctx["machine_id"]
    locker_id = locker_ctx["locker_id"]

    try:
        conn = get_conn()

        row = conn.execute(
            """
            SELECT door_id
            FROM allocations
            WHERE allocation_id = ?
            """,
            (allocation_id,)
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Allocation not found"
            )

        slot = row["slot"]

        conn.execute(
            """
            UPDATE door_state
            SET state='PAID_PENDING_PICKUP', updated_at=?
            WHERE machine_id=? AND door_id=?
            """,
            (_now_iso(), machine_id, slot),
        )

        conn.commit()

        return {
            "ok": True,
            "allocation_id": allocation_id,
            "locker_id": locker_id,
            "state": "COMMITTED",
        }

    except Exception as e:
        _raise(
            500,
            err_type="RUNTIME_COMMIT_FAILED",
            message=str(e),
            retryable=True,
            locker_id=locker_id,
        )


# =========================================================
# RELEASE (EXECUTE ONLY)
# =========================================================

@router.post("/allocations/{allocation_id}/release")
def release(
    allocation_id: str,
    payload: ReleaseCommand,
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):

    locker_ctx = resolve_runtime_locker(x_locker_id)

    machine_id = locker_ctx["machine_id"]
    locker_id = locker_ctx["locker_id"]

    try:
        conn = get_conn()

        row = conn.execute(
            """
            SELECT door_id
            FROM allocations
            WHERE allocation_id = ?
            """,
            (allocation_id,)
        ).fetchone()

        slot = row["door_id"]

        conn.execute(
            """
            UPDATE door_state
            SET state='AVAILABLE', product_id=NULL, updated_at=?
            WHERE machine_id=? AND door_id=?
            """,
            (_now_iso(), machine_id, slot),
        )

        conn.commit()

        return {
            "ok": True,
            "allocation_id": allocation_id,
            "locker_id": locker_id,
            "state": "RELEASED",
        }

    except Exception as e:
        _raise(
            500,
            err_type="RUNTIME_RELEASE_FAILED",
            message=str(e),
            retryable=True,
            locker_id=locker_id,
        )