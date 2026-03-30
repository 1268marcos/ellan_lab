# 01_source/backend/runtime/app/routers/hardware.py
"""
Objetivo

Transformar para runtime multi-locker:

receber X-Locker-Id
resolver identidade do locker
publicar no tópico MQTT correto para aquele locker
registrar evento com locker_id/machine_id corretos

Sem isso, ONLINE e KIOSK não fecham consistência operacional completa.

Deve publicar comando MQTT para o locker correto, usando resolução dinâmica.

Hoje esse é um dos principais travamentos para unificação real.
"""
from fastapi import APIRouter, HTTPException, Request
from datetime import datetime, timezone
from pydantic import BaseModel
import os, json, uuid, hashlib, traceback

import paho.mqtt.publish as publish

from app.core.db import get_conn

router = APIRouter(prefix="/locker", tags=["locker-hardware"])

# =========================
# MQTT / Identidade
# =========================
# No seu docker-compose, o broker tem container_name: mqtt_broker
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt_broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

# REGION deve vir do compose (backend_sp: SP, backend_pt: PT).
# Fallback inteligente só para rodar fora do compose.
def _default_region() -> str:
    tz = os.getenv("TZ", "").lower()
    if "lisbon" in tz or "portugal" in tz:
        return "PT"
    return "SP"

REGION = os.getenv("REGION", _default_region())
LOCKER_ID = os.getenv("LOCKER_ID", f"LOCKER_{REGION}_01")
MACHINE_ID = os.getenv("MACHINE_ID", f"CACIFO-{REGION}-001")
LOG_HASH_SALT = os.getenv("LOG_HASH_SALT", "")  # opcional

DOOR_CMD_TOPIC = f"locker/{REGION}/doors/cmd"
LIGHT_CMD_TOPIC = f"locker/{REGION}/doors/light/cmd"


class CmdOut(BaseModel):
    ok: bool
    machine_id: str
    region: str
    locker_id: str
    slot: int
    command_id: str
    topic: str
    created_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_slot_range(slot: int) -> None:
    if slot < 1 or slot > 24:
        raise HTTPException(
            status_code=400,
            detail={
                "type": "INVALID_SLOT",
                "message": "slot must be 1..24",
                "retryable": False,
                "slot": slot,
                "min_slot": 1,
                "max_slot": 24,
            },
        )


def _canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _get_last_hash(conn) -> str | None:
    cur = conn.execute(
        "SELECT hash FROM events WHERE machine_id=? ORDER BY id DESC LIMIT 1",
        (MACHINE_ID,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def _insert_event(
    conn,
    *,
    door_id: int,
    event_type: str,
    severity: str,
    correlation_id: str,
    command_id: str,
    payload: dict,
):
    ts = _now_iso()
    payload_json = _canonical_json(payload)
    prev_hash = _get_last_hash(conn)

    material = _canonical_json(
        {
            "ts": ts,
            "machine_id": MACHINE_ID,
            "door_id": door_id,
            "event_type": event_type,
            "severity": severity,
            "correlation_id": correlation_id,
            "command_id": command_id,
            "payload_json": payload_json,
            "prev_hash": prev_hash,
            "salt": LOG_HASH_SALT,
        }
    )
    h = "sha256:" + hashlib.sha256(material.encode("utf-8")).hexdigest()

    conn.execute(
        """
        INSERT INTO events
        (ts, machine_id, door_id, event_type, severity, correlation_id, sale_id, command_id, old_state, new_state,
         payload_json, prev_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, ?, ?, ?)
        """,
        (ts, MACHINE_ID, door_id, event_type, severity, correlation_id, command_id, payload_json, prev_hash, h),
    )


def _publish_with_audit(*, topic: str, slot: int, command: str, request: Request) -> CmdOut:
    _ensure_slot_range(slot)

    command_id = f"cmd_{uuid.uuid4().hex}"
    created_at = _now_iso()

    cmd_payload = {
        "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "door_id": slot,
        "command": command,
        "command_id": command_id,
        "origin": "backend",
    }

    conn = get_conn()

    requested_type = f"DOOR_{command}_COMMAND_REQUESTED"
    published_type = f"DOOR_{command}_COMMAND_PUBLISHED"
    failed_type = f"DOOR_{command}_COMMAND_FAILED"

    # 1) Log REQUESTED (DB)
    try:
        _insert_event(
            conn,
            door_id=slot,
            event_type=requested_type,
            severity="INFO",
            correlation_id=command_id,
            command_id=command_id,
            payload={
                "endpoint": str(request.url.path),
                "region": REGION,
                "locker_id": LOCKER_ID,
                "topic": topic,
                "cmd": cmd_payload,
            },
        )
        conn.commit()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "type": "DB_EVENT_LOG_FAILED",
                "message": str(e),
                "retryable": True,
                "region": REGION,
                "endpoint": str(request.url.path),
                "slot": slot,
                "command_id": command_id,
            },
        )

    # 2) Publish MQTT
    try:
        publish.single(
            topic,
            json.dumps(cmd_payload, ensure_ascii=False),
            hostname=MQTT_HOST,
            port=MQTT_PORT,
        )
    except Exception as e:
        tb = traceback.format_exc(limit=4)

        # tenta logar a falha
        try:
            _insert_event(
                conn,
                door_id=slot,
                event_type=failed_type,
                severity="HIGH",
                correlation_id=command_id,
                command_id=command_id,
                payload={
                    "endpoint": str(request.url.path),
                    "region": REGION,
                    "locker_id": LOCKER_ID,
                    "error": str(e),
                    "trace": tb,
                    "topic": topic,
                    "cmd": cmd_payload,
                },
            )
            conn.commit()
        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail={
                "type": "MQTT_PUBLISH_FAILED",
                "message": str(e),
                "retryable": True,
                "region": REGION,
                "endpoint": str(request.url.path),
                "mqtt": {"host": MQTT_HOST, "port": MQTT_PORT, "topic": topic},
                "slot": slot,
                "command_id": command_id,
            },
        )

    # 3) Log PUBLISHED (DB) - não derruba se falhar
    try:
        _insert_event(
            conn,
            door_id=slot,
            event_type=published_type,
            severity="INFO",
            correlation_id=command_id,
            command_id=command_id,
            payload={
                "endpoint": str(request.url.path),
                "region": REGION,
                "locker_id": LOCKER_ID,
                "topic": topic,
                "cmd": cmd_payload,
            },
        )
        conn.commit()
    except Exception:
        pass

    return CmdOut(
        ok=True,
        machine_id=MACHINE_ID,
        region=REGION,
        locker_id=LOCKER_ID,
        slot=slot,
        command_id=command_id,
        topic=topic,
        created_at=created_at,
    )


@router.post("/slots/{slot}/open", response_model=CmdOut)
def open_slot(slot: int, request: Request):
    return _publish_with_audit(topic=DOOR_CMD_TOPIC, slot=slot, command="OPEN", request=request)


@router.post("/slots/{slot}/light/on", response_model=CmdOut)
def light_on(slot: int, request: Request):
    return _publish_with_audit(topic=LIGHT_CMD_TOPIC, slot=slot, command="LIGHT_ON", request=request)