# 01_source/backend/runtime/app/services/hardware_command_service.py
from __future__ import annotations

import hashlib
import json
import traceback
import uuid
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.publish as publish
from fastapi import HTTPException, Request

from app.core.config import settings
from app.core.constants.slot_states import is_slot_occupied
from app.core.mqtt_topics import door_command_topic, light_command_topic
from app.core.slot_topology import ensure_valid_slot
from app.core.locker_runtime_resolver import resolve_runtime_locker
from app.core.db import get_conn

from app.core.datetime_utils import to_iso_utc



def _build_error(
    *,
    err_type: str,
    message: str,
    retryable: bool,
    **extra,
) -> dict:
    detail = {
        "type": err_type,
        "message": message,
        "retryable": retryable,
    }
    if extra:
        detail.update(extra)
    return detail


# def _now_iso() -> str:
#     return datetime.now(timezone.utc).isoformat()

def _now_iso() -> str:
    return to_iso_utc(datetime.now(timezone.utc))

def _now_epoch_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _canonical_json(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _get_last_hash(conn, machine_id: str) -> str | None:
    cur = conn.execute(
        "SELECT hash FROM events WHERE machine_id=? ORDER BY id DESC LIMIT 1",
        (machine_id,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _insert_event(
    conn,
    *,
    machine_id: str,
    locker_id: str,
    region: str,
    door_id: int,
    event_type: str,
    severity: str,
    correlation_id: str,
    command_id: str,
    payload: dict[str, Any],
) -> None:
    ts = _now_iso()
    payload_json = _canonical_json(payload)
    prev_hash = _get_last_hash(conn, machine_id)
    salt = getattr(settings, "log_hash_salt", "") or ""

    material = _canonical_json(
        {
            "ts": ts,
            "machine_id": machine_id,
            "door_id": door_id,
            "event_type": event_type,
            "severity": severity,
            "correlation_id": correlation_id,
            "command_id": command_id,
            "payload_json": payload_json,
            "prev_hash": prev_hash,
            "salt": salt,
        }
    )
    h = "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()

    conn.execute(
        """
        INSERT INTO events
        (
            ts,
            machine_id,
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
            hash
        )
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, ?, ?, ?)
        """,
        (
            ts,
            machine_id,
            door_id,
            event_type,
            severity,
            correlation_id,
            command_id,
            payload_json,
            prev_hash,
            h,
        ),
    )


def _get_slot_row(conn, *, machine_id: str, slot: int) -> dict | None:
    cur = conn.execute(
        """
        SELECT state, product_id, updated_at
        FROM door_state
        WHERE machine_id=? AND door_id=?
        """,
        (machine_id, slot),
    )
    row = cur.fetchone()
    if not row:
        return None

    return {
        "state": row[0],
        "product_id": row[1],
        "updated_at": row[2],
    }


def _upsert_slot(
    conn,
    *,
    machine_id: str,
    slot: int,
    state: str,
    product_id: str | None,
) -> dict:
    now = _now_iso()
    conn.execute(
        """
        INSERT INTO door_state(machine_id, door_id, state, product_id, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(machine_id, door_id)
        DO UPDATE SET
            state=excluded.state,
            product_id=excluded.product_id,
            updated_at=excluded.updated_at
        """,
        (machine_id, slot, state, product_id, now),
    )
    return {
        "slot": slot,
        "state": state,
        "product_id": product_id,
        "updated_at": now,
    }


def _ensure_slot_exists(conn, *, machine_id: str, slot: int) -> dict:
    row = _get_slot_row(conn, machine_id=machine_id, slot=slot)
    if row is not None:
        return row

    created = _upsert_slot(
        conn,
        machine_id=machine_id,
        slot=slot,
        state="AVAILABLE",
        product_id=None,
    )
    conn.commit()
    return created


def _resolve_topics(*, region: str, locker_id: str) -> dict[str, str]:
    return {
        "open": door_command_topic(region=region, locker_id=locker_id),
        "light_on": light_command_topic(region=region, locker_id=locker_id),
    }


def _publish_single(
    *,
    topic: str,
    payload: dict[str, Any],
) -> None:
    publish.single(
        topic,
        json.dumps(payload, ensure_ascii=False),
        hostname=settings.mqtt_host,
        port=int(settings.mqtt_port),
    )


def _build_command_payload(
    *,
    locker_ctx: dict,
    slot: int,
    command: str,
    command_id: str,
) -> dict[str, Any]:
    return {
        "ts": _now_epoch_ms(),
        "locker_id": locker_ctx["locker_id"],
        "machine_id": locker_ctx["machine_id"],
        "region": locker_ctx["region"],
        "door_id": slot,
        "slot": slot,
        "command": command,
        "command_id": command_id,
        "origin": "backend_runtime",
    }


def execute_hardware_command(
    *,
    request: Request,
    x_locker_id: str | None,
    slot: int,
    command: str,
) -> dict[str, Any]:
    locker_ctx = resolve_runtime_locker(x_locker_id)
    locker_id = locker_ctx["locker_id"]
    machine_id = locker_ctx["machine_id"]
    region = locker_ctx["region"]

    ensure_valid_slot(locker_ctx, slot)

    topics = _resolve_topics(region=region, locker_id=locker_id)

    if command == "OPEN":
        topic = topics["open"]
    elif command == "LIGHT_ON":
        topic = topics["light_on"]
    else:
        raise HTTPException(
            status_code=400,
            detail=_build_error(
                err_type="UNSUPPORTED_HARDWARE_COMMAND",
                message="Unsupported hardware command.",
                retryable=False,
                command=command,
                locker_id=locker_id,
                machine_id=machine_id,
                allowed_commands=["OPEN", "LIGHT_ON"],
            ),
        )

    conn = None
    try:
        conn = get_conn()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="DB_CONNECTION_FAILED",
                message="Failed to connect to runtime database.",
                retryable=True,
                locker_id=locker_id,
                machine_id=machine_id,
                region=region,
                endpoint=str(request.url.path),
                error=str(exc),
            ),
        ) from exc

    slot_row = _ensure_slot_exists(conn, machine_id=machine_id, slot=slot)
    current_state = str(slot_row["state"])

    # Regra operacional:
    # - OPEN só faz sentido quando há algo reservado/pago para pickup
    # - LIGHT_ON pode ser usado como auxílio mesmo com slot disponível
    if command == "OPEN" and not is_slot_occupied(current_state):
        raise HTTPException(
            status_code=409,
            detail=_build_error(
                err_type="SLOT_NOT_READY_FOR_OPEN",
                message="Slot is not reserved for pickup/open operation.",
                retryable=False,
                locker_id=locker_id,
                machine_id=machine_id,
                region=region,
                slot=slot,
                current_state=current_state,
                expected_states=["RESERVED", "PAID_PENDING_PICKUP"],
            ),
        )

    command_id = f"cmd_{uuid.uuid4().hex}"
    correlation_id = command_id
    cmd_payload = _build_command_payload(
        locker_ctx=locker_ctx,
        slot=slot,
        command=command,
        command_id=command_id,
    )

    requested_type = f"DOOR_{command}_COMMAND_REQUESTED"
    published_type = f"DOOR_{command}_COMMAND_PUBLISHED"
    failed_type = f"DOOR_{command}_COMMAND_FAILED"

    try:
        _insert_event(
            conn,
            machine_id=machine_id,
            locker_id=locker_id,
            region=region,
            door_id=slot,
            event_type=requested_type,
            severity="INFO",
            correlation_id=correlation_id,
            command_id=command_id,
            payload={
                "endpoint": str(request.url.path),
                "locker_id": locker_id,
                "machine_id": machine_id,
                "region": region,
                "topic": topic,
                "command_payload": cmd_payload,
                "current_state": current_state,
            },
        )
        conn.commit()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=_build_error(
                err_type="DB_EVENT_LOG_FAILED",
                message="Failed to persist requested hardware command event.",
                retryable=True,
                locker_id=locker_id,
                machine_id=machine_id,
                region=region,
                endpoint=str(request.url.path),
                slot=slot,
                command=command,
                command_id=command_id,
                error=str(exc),
            ),
        ) from exc

    try:
        _publish_single(topic=topic, payload=cmd_payload)
    except Exception as exc:
        tb = traceback.format_exc(limit=5)

        try:
            _insert_event(
                conn,
                machine_id=machine_id,
                locker_id=locker_id,
                region=region,
                door_id=slot,
                event_type=failed_type,
                severity="HIGH",
                correlation_id=correlation_id,
                command_id=command_id,
                payload={
                    "endpoint": str(request.url.path),
                    "locker_id": locker_id,
                    "machine_id": machine_id,
                    "region": region,
                    "topic": topic,
                    "command_payload": cmd_payload,
                    "error": str(exc),
                    "trace": tb,
                },
            )
            conn.commit()
        except Exception:
            pass

        raise HTTPException(
            status_code=502,
            detail=_build_error(
                err_type="MQTT_PUBLISH_FAILED",
                message="Failed to publish hardware command to MQTT.",
                retryable=True,
                locker_id=locker_id,
                machine_id=machine_id,
                region=region,
                endpoint=str(request.url.path),
                slot=slot,
                command=command,
                command_id=command_id,
                mqtt_host=settings.mqtt_host,
                mqtt_port=int(settings.mqtt_port),
                topic=topic,
                error=str(exc),
            ),
        ) from exc

    try:
        _insert_event(
            conn,
            machine_id=machine_id,
            locker_id=locker_id,
            region=region,
            door_id=slot,
            event_type=published_type,
            severity="INFO",
            correlation_id=correlation_id,
            command_id=command_id,
            payload={
                "endpoint": str(request.url.path),
                "locker_id": locker_id,
                "machine_id": machine_id,
                "region": region,
                "topic": topic,
                "command_payload": cmd_payload,
            },
        )
        conn.commit()
    except Exception:
        # não derruba a operação se publicação já ocorreu
        pass

    return {
        "ok": True,
        "service": "backend_runtime",
        "locker_id": locker_id,
        "machine_id": machine_id,
        "region": region,
        "slot": slot,
        "command": command,
        "command_id": command_id,
        "topic": topic,
        "created_at": _now_iso(),
        "state_before_command": current_state,
    }