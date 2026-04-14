# /home/marcos/ellan_lab/01_source/backend_pt/app/routers/debug.py
import os
import uuid
from fastapi import APIRouter, Header, HTTPException, Query

from app.core.event_log import log_event
from app.core.event_types import EventType, Severity
from app.core.db import get_conn

router = APIRouter(prefix="/debug", tags=["debug"])

MACHINE_ID = os.getenv("MACHINE_ID", "CACIFO-SP-001")
REGION = os.getenv("REGION", "SP").upper()
INTERNAL_TOKEN = os.getenv("INTERNAL_TOKEN")  # opcional

REGION_CURRENCY = {"SP": "BRL", "PT": "EUR"}


def _require_internal_token(x_internal_token: str | None):
    if INTERNAL_TOKEN and x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(
            status_code=401,
            detail={"type": "UNAUTHORIZED", "message": "invalid internal token", "retryable": False},
        )


def _check_chain(events: list[dict]) -> dict:
    """
    Valida que prev_hash do evento i aponta para hash do evento i-1.
    events deve estar em ordem cronológica crescente.
    """
    mismatches = []
    for i in range(1, len(events)):
        expected_prev = events[i - 1].get("hash")
        got_prev = events[i].get("prev_hash")
        if got_prev != expected_prev:
            mismatches.append({
                "i": i,
                "event_id": events[i].get("event_id"),
                "event_type": events[i].get("event_type"),
                "expected_prev_hash": expected_prev,
                "got_prev_hash": got_prev,
            })

    return {
        "chain_ok": (len(mismatches) == 0),
        "mismatches": mismatches,
        "first_prev_hash": events[0].get("prev_hash") if events else None,
        "last_hash": events[-1].get("hash") if events else None,
    }


@router.api_route("/log_sample", methods=["GET", "POST"])
def log_sample(x_internal_token: str | None = Header(default=None)):
    _require_internal_token(x_internal_token)

    correlation_id = str(uuid.uuid4())
    sale_id = f"S-{uuid.uuid4().hex[:8]}"
    command_id = f"CMD-{uuid.uuid4().hex[:8]}"
    door_id = 7

    currency = REGION_CURRENCY.get(REGION, "BRL")

    try:
        events: list[dict] = []

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.SALE_STARTED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"message": "Sale initiated", "region": REGION},
        ))

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.PAYMENT_APPROVED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"amount": 12.5, "currency": currency, "region": REGION},
        ))

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.HW_OPEN_CMD_SENT,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            command_id=command_id,
            payload={"timeout_seconds": 3, "region": REGION},
        ))

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.STATE_CHANGE,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            old_state="AVAILABLE",
            new_state="RESERVED",
            payload={"fsm": "door_state"},
        ))

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.STATE_CHANGE,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            old_state="RESERVED",
            new_state="PAID_PENDING_PICKUP",
            payload={"fsm": "door_state"},
        ))

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.DOOR_OPENED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"sensor": "reed_switch"},
        ))

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.DOOR_CLOSED,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            sale_id=sale_id,
            payload={"sensor": "reed_switch"},
        ))

        events.append(log_event(
            machine_id=MACHINE_ID,
            event_type=EventType.STATE_CHANGE,
            severity=Severity.INFO,
            correlation_id=correlation_id,
            door_id=door_id,
            old_state="PAID_PENDING_PICKUP",
            new_state="PICKED_UP", # PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
            payload={"fsm": "door_state"},
        ))

        chain_report = _check_chain(events)

        chain = [{
            "i": i,
            "event_id": e.get("event_id"),
            "ts": e.get("ts"),
            "event_type": e.get("event_type"),
            "severity": e.get("severity"),
            "door_id": e.get("door_id"),
            "correlation_id": e.get("correlation_id"),
            "sale_id": e.get("sale_id"),
            "command_id": e.get("command_id"),
            "old_state": e.get("old_state"),
            "new_state": e.get("new_state"),
            "prev_hash": e.get("prev_hash"),
            "hash": e.get("hash"),
        } for i, e in enumerate(events)]

        return {
            "ok": True,
            "status": "sample_events_created",
            "machine_id": MACHINE_ID,
            "region": REGION,
            "currency": currency,
            "events_created": len(events),
            "correlation_id": correlation_id,
            "sale_id": sale_id,
            "chain_validation": chain_report,
            "chain": chain,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "DEBUG_SAMPLE_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": MACHINE_ID,
                "region": REGION,
            },
        )


@router.get("/verify_chain")
def verify_chain(
    limit: int = Query(default=200, ge=10, le=5000),
    x_internal_token: str | None = Header(default=None),
):
    """
    Verifica a integridade da cadeia (prev_hash -> hash) dos últimos N eventos
    do SQLite para o MACHINE_ID atual.

    Retorna:
    - chain_ok: bool
    - mismatches: lista com detalhes (event_id, expected_prev_hash, got_prev_hash)
    - scanned: quantos eventos analisados
    - first/last hashes
    """
    _require_internal_token(x_internal_token)

    try:
        conn = get_conn()

        # pega os últimos N em ordem DESC
        cur = conn.execute(
            """
            SELECT id, ts, event_type, severity, door_id, correlation_id, sale_id, command_id,
                   old_state, new_state, prev_hash, hash
            FROM events
            WHERE machine_id=?
            ORDER BY id DESC
            LIMIT ?
            """,
            (MACHINE_ID, limit),
        )
        rows_desc = cur.fetchall()

        if not rows_desc:
            return {
                "ok": True,
                "machine_id": MACHINE_ID,
                "region": REGION,
                "scanned": 0,
                "chain_ok": True,
                "mismatches": [],
                "note": "no events for this machine_id",
            }

        # reverte para ordem crescente (do mais antigo ao mais recente)
        rows = list(reversed(rows_desc))

        events = []
        for r in rows:
            events.append({
                "event_id": r[0],
                "ts": r[1],
                "event_type": r[2],
                "severity": r[3],
                "door_id": r[4],
                "correlation_id": r[5],
                "sale_id": r[6],
                "command_id": r[7],
                "old_state": r[8],
                "new_state": r[9],
                "prev_hash": r[10],
                "hash": r[11],
            })

        mismatches = []
        for i in range(1, len(events)):
            expected_prev = events[i - 1]["hash"]
            got_prev = events[i]["prev_hash"]
            if got_prev != expected_prev:
                mismatches.append({
                    "i": i,
                    "event_id": events[i]["event_id"],
                    "event_type": events[i]["event_type"],
                    "expected_prev_hash": expected_prev,
                    "got_prev_hash": got_prev,
                })

        return {
            "ok": True,
            "machine_id": MACHINE_ID,
            "region": REGION,
            "scanned": len(events),
            "chain_ok": (len(mismatches) == 0),
            "mismatches": mismatches,
            "first_event_id": events[0]["event_id"],
            "last_event_id": events[-1]["event_id"],
            "first_prev_hash": events[0]["prev_hash"],
            "last_hash": events[-1]["hash"],
            # útil para depurar rapidamente sem retornar tudo:
            "sample": events[-10:] if len(events) > 10 else events,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "VERIFY_CHAIN_FAILED",
                "message": str(e),
                "retryable": True,
                "machine_id": MACHINE_ID,
                "region": REGION,
            },
        )