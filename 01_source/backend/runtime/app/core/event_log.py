# 01_source/backend/runtime/app/core/event_log.py
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Optional, Dict, Union

from app.core.db import get_conn
from .event_types import EventType, Severity


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_json(payload: Dict[str, Any]) -> str:
    # JSON estável (ordem fixa) para hash consistente
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

# def _sha256_hex(s: str) -> str:
def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _get_last_hash(conn, machine_id: str) -> Optional[str]:
    cur = conn.execute(
        "SELECT hash FROM events WHERE machine_id = ? ORDER BY id DESC LIMIT 1;",
        (machine_id,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def log_event(
    *,
    machine_id: str,
    event_type: Union[EventType, str],
    severity: Union[Severity, str] = Severity.INFO,
    correlation_id: str,
    door_id: Optional[int] = None,
    sale_id: Optional[str] = None,
    command_id: Optional[str] = None,
    old_state: Optional[str] = None,
    new_state: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    # bônus: permite batching transacional (opcional, não quebra)
    conn=None,
) -> Dict[str, Any]:
    """
    Escreve evento IMUTÁVEL na tabela events (append-only) com hash encadeado.
    Retorna também event_id (SQLite AUTOINCREMENT) para debug/auditoria.
    """
    conn = conn or get_conn()
    ts = utc_now_iso()
    payload = payload or {}

    # Normaliza e valida Enum/str
    if isinstance(event_type, EventType):
        event_type_value = event_type.value
    elif isinstance(event_type, str):
        try:
            event_type_value = EventType(event_type).value
        except Exception:
            raise ValueError(f"Invalid event_type: {event_type}")
    else:
        raise TypeError(f"event_type must be EventType or str, got: {type(event_type)}")

    if isinstance(severity, Severity):
        severity_value = severity.value
    elif isinstance(severity, str):
        try:
            severity_value = Severity(severity).value
        except Exception:
            raise ValueError(f"Invalid severity: {severity}")
    else:
        raise TypeError(f"severity must be Severity or str, got: {type(severity)}")

    payload_json = _canonical_json(payload)
    prev_hash = _get_last_hash(conn, machine_id)

    salt = os.getenv("LOG_HASH_SALT", "")

    base = "|".join(
        [
            ts,
            machine_id,
            str(door_id or ""),
            event_type_value,
            severity_value,
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
    # event_hash = "sha256:" + _sha256_hex(base)
    event_hash = "sha256:" + _sha256(base)

    cur = conn.execute(
        """
        INSERT INTO events
        (ts, machine_id, door_id, event_type, severity, correlation_id, sale_id,
         command_id, old_state, new_state, payload_json, prev_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            ts,
            machine_id,
            door_id,
            event_type_value,
            severity_value,
            correlation_id,
            sale_id,
            command_id,
            old_state,
            new_state,
            payload_json,
            prev_hash,
            event_hash,
        ),
    )
    conn.commit()

    event_id = cur.lastrowid  # ✅ nível máximo: id real do SQLite

    return {
        "event_id": event_id,
        "ts": ts,
        "machine_id": machine_id,
        "door_id": door_id,
        "event_type": event_type_value,
        "severity": severity_value,
        "correlation_id": correlation_id,
        "sale_id": sale_id,
        "command_id": command_id,
        "old_state": old_state,
        "new_state": new_state,
        "payload": payload,
        "payload_json": payload_json,  # útil para comparação exata
        "prev_hash": prev_hash,
        "hash": event_hash,
    }