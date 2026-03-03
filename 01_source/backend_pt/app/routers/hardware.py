# /home/marcos/ellan_lab/01_source/backend_pt/app/routers/hardware.py
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from pydantic import BaseModel
import os, json, uuid
import paho.mqtt.publish as publish

from app.core.db import get_conn

router = APIRouter(prefix="/locker", tags=["locker-hardware"])

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt_broker")
REGION = os.getenv("REGION", "PT")
LOCKER_ID = os.getenv("LOCKER_ID", f"LOCKER_{REGION}_01")

DOOR_CMD_TOPIC = f"locker/{REGION}/doors/cmd"
LIGHT_CMD_TOPIC = f"locker/{REGION}/doors/light/cmd"

class CmdOut(BaseModel):
    ok: bool
    door_id: int
    command_id: str
    topic: str
    sent_at: str

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _machine_id() -> str:
    return os.getenv("MACHINE_ID", "CACIFO-PT-001")

def _ensure_slot_range(slot: int) -> None:
    if slot < 1 or slot > 24:
        raise HTTPException(status_code=400, detail="slot must be 1..24")

class _CmdOut(BaseModel):
    ok: bool
    machine_id: str
    slot: int
    command_id: str
    created_at: str

def _insert_event(conn, machine_id: str, door_id: int, event_type: str, correlation_id: str, payload: dict):
    # Mantém compatível com tua tabela events
    conn.execute(
        """
        INSERT INTO events
        (ts, machine_id, door_id, event_type, severity, correlation_id, sale_id, command_id, old_state, new_state,
         payload_json, prev_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, ?, NULL, ?)
        """,
        (
            _now_iso(),
            machine_id,
            door_id,
            event_type,
            "INFO",
            correlation_id,
            payload.get("command_id"),
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            # hash encadeado você já tem em outros serviços; aqui fica dummy até plugar o event_log do backend
            f"hash_{uuid.uuid4().hex}",
        ),
    )
    conn.commit()

@router.post("/slots/{slot}/open", response_model=_CmdOut)
def open_slot(slot: int):
    _ensure_slot_range(slot)
    command_id = f"cmd_{uuid.uuid4().hex}"

    payload = {
        "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "door_id": slot,
        "command": "OPEN",
        "command_id": command_id,
        "origin": "backend",
    }

    publish.single(DOOR_CMD_TOPIC, json.dumps(payload), hostname=MQTT_HOST)
    return CmdOut(ok=True, door_id=slot, command_id=command_id, topic=DOOR_CMD_TOPIC, sent_at=_now_iso())

    # conn = get_conn()
    # mid = _machine_id()
    # cmd_id = f"cmd_open_{uuid.uuid4().hex}"
    # corr_id = f"corr_{uuid.uuid4().hex}"

    # _insert_event(
    #     conn,
    #     machine_id=mid,
    #     door_id=slot,
    #     event_type="LOCKER_SLOT_OPEN",
    #     correlation_id=corr_id,
    #     payload={"command_id": cmd_id, "slot": slot, "action": "open"},
    # )

    # return _CmdOut(ok=True, machine_id=mid, slot=slot, command_id=cmd_id, created_at=_now_iso())

@router.post("/slots/{slot}/light/on", response_model=_CmdOut)
def light_on(slot: int):
    _ensure_slot_range(slot)
    command_id = f"cmd_{uuid.uuid4().hex}"

    payload = {
        "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "door_id": slot,
        "command": "LIGHT_ON",
        "command_id": command_id,
        "origin": "backend",
    }

    publish.single(LIGHT_CMD_TOPIC, json.dumps(payload), hostname=MQTT_HOST)
    return CmdOut(ok=True, door_id=slot, command_id=command_id, topic=LIGHT_CMD_TOPIC, sent_at=_now_iso())

    # conn = get_conn()
    # mid = _machine_id()
    # cmd_id = f"cmd_light_{uuid.uuid4().hex}"
    # corr_id = f"corr_{uuid.uuid4().hex}"

    # _insert_event(
    #     conn,
    #     machine_id=mid,
    #     door_id=slot,
    #     event_type="LOCKER_SLOT_LIGHT_ON",
    #     correlation_id=corr_id,
    #     payload={"command_id": cmd_id, "slot": slot, "action": "light_on"},
    # )

    # return _CmdOut(ok=True, machine_id=mid, slot=slot, command_id=cmd_id, created_at=_now_iso())
    