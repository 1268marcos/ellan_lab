# 01_source/backend/runtime/app/routers/allocations.py
# RUNTIME = EXECUTOR RESILIENTE
# 01/04/2026
# 10/04/2026 - commit/release por slot específico
# 10/04/2026 - persistência local de allocations + TTL

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
from typing import Optional
import uuid

from app.core.db import get_conn
from app.core.locker_runtime_resolver import resolve_runtime_locker

router = APIRouter(prefix="/locker", tags=["locker"])


# =========================================================
# HELPERS
# =========================================================

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


def _raise(status, *, err_type, message, retryable, **extra):
    detail = {"type": err_type, "message": message, "retryable": retryable}
    if extra:
        detail.update(extra)
    raise HTTPException(status_code=status, detail=detail)


def _parse_positive_ttl(ttl_seconds: Optional[int], default: int = 90) -> int:
    if ttl_seconds is None:
        return default
    ttl = int(ttl_seconds)
    if ttl <= 0:
        raise ValueError("ttl_seconds must be positive")
    return ttl


def _build_expires_at(ttl_seconds: int) -> str:
    return (_now_utc() + timedelta(seconds=ttl_seconds)).isoformat()


def _fetch_allocation_or_raise(conn, allocation_id: str) -> dict:
    row = conn.execute(
        """
        SELECT
            allocation_id,
            machine_id,
            door_id,
            state,
            created_at,
            expires_at,
            sale_id,
            request_id
        FROM allocations
        WHERE allocation_id = ?
        """,
        (allocation_id,),
    ).fetchone()

    if not row:
        _raise(
            404,
            err_type="ALLOCATION_NOT_FOUND",
            message=f"allocation not found: {allocation_id}",
            retryable=False,
            allocation_id=allocation_id,
        )

    return dict(row)


# =========================================================
# MODELS
# =========================================================

class AllocateCommand(BaseModel):
    slot: int
    allocation_id: Optional[str] = None
    ttl_seconds: Optional[int] = 90
    sale_id: Optional[str] = None
    request_id: Optional[str] = None


class CommitCommand(BaseModel):
    slot: Optional[int] = None


class ReleaseCommand(BaseModel):
    slot: Optional[int] = None
    reason: Optional[str] = None


# =========================================================
# ALLOCATE
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
        ttl_seconds = _parse_positive_ttl(payload.ttl_seconds, default=90)
        allocation_id = payload.allocation_id or f"al_{uuid.uuid4().hex}"
        created_at = _now_iso()
        expires_at = _build_expires_at(ttl_seconds)

        conn = get_conn()

        # garante a porta local
        conn.execute(
            """
            INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
            VALUES (?, ?, 'AVAILABLE', NULL, ?)
            ON CONFLICT(machine_id, door_id) DO NOTHING
            """,
            (machine_id, slot, created_at),
        )

        # transição operacional da porta
        res = conn.execute(
            """
            UPDATE door_state
            SET state='RESERVED', updated_at=?
            WHERE machine_id=? AND door_id=? AND state='AVAILABLE'
            """,
            (created_at, machine_id, slot),
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

        # persiste allocation local para commit/release/offline
        conn.execute(
            """
            INSERT INTO allocations (
                allocation_id,
                machine_id,
                door_id,
                state,
                created_at,
                expires_at,
                sale_id,
                request_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                allocation_id,
                machine_id,
                slot,
                "RESERVED",
                created_at,
                expires_at,
                payload.sale_id,
                payload.request_id,
            ),
        )

        conn.commit()

        return {
            "ok": True,
            "allocation_id": allocation_id,
            "slot": slot,
            "locker_id": locker_id,
            "machine_id": machine_id,
            "state": "RESERVED",
            "ttl_seconds": ttl_seconds,
            "expires_at": expires_at,
        }

    except HTTPException:
        raise
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass

        _raise(
            500,
            err_type="RUNTIME_EXECUTION_FAILED",
            message=str(e),
            retryable=True,
            locker_id=locker_id,
            slot=slot,
        )


# =========================================================
# COMMIT
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

        allocation = _fetch_allocation_or_raise(conn, allocation_id)

        allocation_machine_id = allocation["machine_id"]
        slot = int(allocation["door_id"])
        allocation_state = str(allocation["state"] or "").upper()

        if allocation_machine_id != machine_id:
            _raise(
                409,
                err_type="ALLOCATION_LOCKER_MISMATCH",
                message="allocation belongs to a different locker",
                retryable=False,
                allocation_id=allocation_id,
                locker_id=locker_id,
                allocation_machine_id=allocation_machine_id,
                request_machine_id=machine_id,
            )

        if payload.slot is not None and int(payload.slot) != slot:
            _raise(
                409,
                err_type="ALLOCATION_SLOT_MISMATCH",
                message="payload slot does not match persisted allocation",
                retryable=False,
                allocation_id=allocation_id,
                locker_id=locker_id,
                persisted_slot=slot,
                payload_slot=int(payload.slot),
            )

        if allocation_state == "COMMITTED":
            return {
                "ok": True,
                "allocation_id": allocation_id,
                "slot": slot,
                "locker_id": locker_id,
                "state": "COMMITTED",
                "idempotent": True,
            }

        if allocation_state != "RESERVED":
            _raise(
                409,
                err_type="INVALID_ALLOCATION_STATE",
                message=f"cannot commit allocation in state {allocation_state}",
                retryable=False,
                allocation_id=allocation_id,
                locker_id=locker_id,
                slot=slot,
            )

        door_res = conn.execute(
            """
            UPDATE door_state
            SET state='PAID_PENDING_PICKUP', updated_at=?
            WHERE machine_id=? AND door_id=?
            """,
            (_now_iso(), machine_id, slot),
        )

        if door_res.rowcount == 0:
            _raise(
                404,
                err_type="DOOR_STATE_NOT_FOUND",
                message="door_state not found for allocation",
                retryable=True,
                allocation_id=allocation_id,
                locker_id=locker_id,
                slot=slot,
            )

        conn.execute(
            """
            UPDATE allocations
            SET state='COMMITTED'
            WHERE allocation_id=?
            """,
            (allocation_id,),
        )

        conn.commit()

        return {
            "ok": True,
            "allocation_id": allocation_id,
            "slot": slot,
            "locker_id": locker_id,
            "state": "COMMITTED",
        }

    except HTTPException:
        raise
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass

        _raise(
            500,
            err_type="RUNTIME_COMMIT_FAILED",
            message=str(e),
            retryable=True,
            locker_id=locker_id,
            allocation_id=allocation_id,
        )


# =========================================================
# RELEASE
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

        allocation = _fetch_allocation_or_raise(conn, allocation_id)

        allocation_machine_id = allocation["machine_id"]
        slot = int(allocation["door_id"])
        allocation_state = str(allocation["state"] or "").upper()

        if allocation_machine_id != machine_id:
            _raise(
                409,
                err_type="ALLOCATION_LOCKER_MISMATCH",
                message="allocation belongs to a different locker",
                retryable=False,
                allocation_id=allocation_id,
                locker_id=locker_id,
                allocation_machine_id=allocation_machine_id,
                request_machine_id=machine_id,
            )

        if payload.slot is not None and int(payload.slot) != slot:
            _raise(
                409,
                err_type="ALLOCATION_SLOT_MISMATCH",
                message="payload slot does not match persisted allocation",
                retryable=False,
                allocation_id=allocation_id,
                locker_id=locker_id,
                persisted_slot=slot,
                payload_slot=int(payload.slot),
            )

        if allocation_state == "RELEASED":
            return {
                "ok": True,
                "allocation_id": allocation_id,
                "slot": slot,
                "locker_id": locker_id,
                "state": "RELEASED",
                "idempotent": True,
            }

        # regra do runtime: expiração/liberação volta para AVAILABLE
        door_res = conn.execute(
            """
            UPDATE door_state
            SET state='AVAILABLE', product_id=NULL, updated_at=?
            WHERE machine_id=? AND door_id=?
            """,
            (_now_iso(), machine_id, slot),
        )

        if door_res.rowcount == 0:
            _raise(
                404,
                err_type="DOOR_STATE_NOT_FOUND",
                message="door_state not found for allocation",
                retryable=True,
                allocation_id=allocation_id,
                locker_id=locker_id,
                slot=slot,
            )

        conn.execute(
            """
            UPDATE allocations
            SET state='RELEASED'
            WHERE allocation_id=?
            """,
            (allocation_id,),
        )

        conn.commit()

        return {
            "ok": True,
            "allocation_id": allocation_id,
            "slot": slot,
            "locker_id": locker_id,
            "state": "RELEASED",
            "reason": payload.reason,
        }

    except HTTPException:
        raise
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass

        _raise(
            500,
            err_type="RUNTIME_RELEASE_FAILED",
            message=str(e),
            retryable=True,
            locker_id=locker_id,
            allocation_id=allocation_id,
        )


# =========================================================
# TTL / EXPIRE
# =========================================================

@router.post("/allocations/expire")
def expire_allocations(
    request: Request,
    x_locker_id: str | None = Header(default=None, alias="X-Locker-Id"),
):
    locker_ctx = resolve_runtime_locker(x_locker_id)

    machine_id = locker_ctx["machine_id"]
    locker_id = locker_ctx["locker_id"]

    try:
        conn = get_conn()

        now_iso = _now_iso()

        expired_rows = conn.execute(
            """
            SELECT allocation_id, door_id
            FROM allocations
            WHERE machine_id = ?
              AND state = 'RESERVED'
              AND expires_at <= ?
            """,
            (machine_id, now_iso),
        ).fetchall()

        expired = []
        for row in expired_rows:
            allocation_id = row["allocation_id"]
            slot = int(row["door_id"])

            conn.execute(
                """
                UPDATE door_state
                SET state='AVAILABLE', product_id=NULL, updated_at=?
                WHERE machine_id=? AND door_id=?
                """,
                (now_iso, machine_id, slot),
            )

            conn.execute(
                """
                UPDATE allocations
                SET state='RELEASED'
                WHERE allocation_id=?
                """,
                (allocation_id,),
            )

            expired.append(
                {
                    "allocation_id": allocation_id,
                    "slot": slot,
                }
            )

        conn.commit()

        return {
            "ok": True,
            "locker_id": locker_id,
            "machine_id": machine_id,
            "expired_count": len(expired),
            "items": expired,
        }

    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass

        _raise(
            500,
            err_type="RUNTIME_EXPIRE_FAILED",
            message=str(e),
            retryable=True,
            locker_id=locker_id,
        )