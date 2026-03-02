import os
import json
from fastapi import APIRouter, Query
from typing import Optional, List, Dict, Any

from ..core.db import get_conn
from ..core.event_log import _sha256

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/events")
def list_events(
    machine_id: str = Query(...),
    door_id: Optional[int] = Query(None),
    limit: int = Query(200, ge=1, le=2000),
) -> List[Dict[str, Any]]:
    """
    01_source/backend_pt/app/routers/audity.py
    
    Verifica integridade da cadeia de hash usando LOG_HASH_SALT.
    """
    conn = get_conn()
    if door_id is None:
        cur = conn.execute(
            """
            SELECT id, ts, machine_id, door_id, event_type, severity, correlation_id,
                   sale_id, command_id, old_state, new_state, payload_json, prev_hash, hash
            FROM events
            WHERE machine_id = ?
            ORDER BY id DESC
            LIMIT ?;
            """,
            (machine_id, limit),
        )
    else:
        cur = conn.execute(
            """
            SELECT id, ts, machine_id, door_id, event_type, severity, correlation_id,
                   sale_id, command_id, old_state, new_state, payload_json, prev_hash, hash
            FROM events
            WHERE machine_id = ? AND door_id = ?
            ORDER BY id DESC
            LIMIT ?;
            """,
            (machine_id, door_id, limit),
        )

    rows = cur.fetchall()
    out = []
    for r in rows:
        out.append(
            {
                "id": r[0],
                "ts": r[1],
                "machine_id": r[2],
                "door_id": r[3],
                "event_type": r[4],
                "severity": r[5],
                "correlation_id": r[6],
                "sale_id": r[7],
                "command_id": r[8],
                "old_state": r[9],
                "new_state": r[10],
                "payload": json.loads(r[11]),
                "prev_hash": r[12],
                "hash": r[13],
            }
        )
    return out


@router.get("/verify")
def verify_chain(
    machine_id: str = Query(...),
    max_events: int = Query(5000, ge=1, le=200000),
):
    """
    01_source/backend_pt/app/routers/audity.py

    Verifica integridade da cadeia de hash usando LOG_HASH_SALT.
    """
    conn = get_conn()
    salt = os.getenv("LOG_HASH_SALT", "")

    cur = conn.execute(
        """
        SELECT id, ts, machine_id, door_id, event_type, severity,
               correlation_id, sale_id, command_id,
               old_state, new_state, payload_json,
               prev_hash, hash
        FROM events
        WHERE machine_id = ?
        ORDER BY id ASC
        LIMIT ?;
        """,
        (machine_id, max_events),
    )

    rows = cur.fetchall()

    prev = None

    for r in rows:
        (
            _id,
            ts,
            mid,
            door_id,
            event_type,
            severity,
            correlation_id,
            sale_id,
            command_id,
            old_state,
            new_state,
            payload_json,
            prev_hash,
            h,
        ) = r

        # Verifica encadeamento
        if prev_hash != prev:
            return {
                "ok": False,
                "at_event_id": _id,
                "reason": "prev_hash_mismatch",
            }

        base = "|".join(
            [
                ts,
                mid,
                str(door_id or ""),
                event_type,
                severity,
                correlation_id,
                sale_id or "",
                command_id or "",
                old_state or "",
                new_state or "",
                payload_json,
                prev_hash or "",
                salt,
            ]
        )

        expected = _sha256(base)

        if expected != h:
            return {
                "ok": False,
                "at_event_id": _id,
                "reason": "hash_mismatch",
            }

        prev = h

    return {
        "ok": True,
        "events_checked": len(rows),
        "salt_used": bool(salt),
    }
