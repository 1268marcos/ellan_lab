# 01_source/backend/runtime/app/services/mqtt_listener.py
import os, json, threading
import paho.mqtt.client as mqtt
from app.core.db import get_conn
from datetime import datetime, timezone
import hashlib

from app.core.datetime_utils import to_iso_utc




MQTT_HOST = os.getenv("MQTT_HOST", "mqtt_broker")
REGION = os.getenv("REGION", "SP")
MACHINE_ID = os.getenv("MACHINE_ID", "CACIFO-SP-001")

DOOR_EVENTS_TOPIC = f"locker/{REGION}/doors/events"
LOG_HASH_SALT = os.getenv("LOG_HASH_SALT", "")  # opcional (melhor ter)

# def _now_iso() -> str:
#     return datetime.now(timezone.utc).isoformat()

def _now_iso() -> str:
    return to_iso_utc(datetime.now(timezone.utc))    

def _canonical_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _get_last_hash(conn, machine_id: str) -> str | None:
    cur = conn.execute(
        "SELECT hash FROM events WHERE machine_id=? ORDER BY id DESC LIMIT 1",
        (machine_id,),
    )
    row = cur.fetchone()
    return row[0] if row else None

def _append_event(
    conn,
    *,
    machine_id: str,
    door_id: int | None,
    event_type: str,
    severity: str,
    correlation_id: str,
    sale_id: str | None,
    command_id: str | None,
    old_state: str | None,
    new_state: str | None,
    payload: dict,
) -> dict:
    ts = _now_iso()
    payload_json = _canonical_json(payload)

    prev_hash = _get_last_hash(conn, machine_id)

    # Hash encadeado simples: prev_hash + campos + salt
    material = _canonical_json({
        "ts": ts,
        "machine_id": machine_id,
        "door_id": door_id,
        "event_type": event_type,
        "severity": severity,
        "correlation_id": correlation_id,
        "sale_id": sale_id,
        "command_id": command_id,
        "old_state": old_state,
        "new_state": new_state,
        "payload_json": payload_json,
        "prev_hash": prev_hash,
        "salt": LOG_HASH_SALT,
    })
    h = "sha256:" + _sha256_hex(material)

    conn.execute(
        """
        INSERT INTO events
        (ts, machine_id, door_id, event_type, severity, correlation_id,
         sale_id, command_id, old_state, new_state, payload_json, prev_hash, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
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
            h,
        ),
    )
    return {"ts": ts, "prev_hash": prev_hash, "hash": h}

def _mark_picked_up_from_closed(payload: dict) -> None:
    door_id = payload.get("door_id")
    if not door_id:
        return

    door_id = int(door_id)
    now_iso = _now_iso()

    # correlation: tenta usar command_id/request_id, senão cria um
    correlation_id = (
        payload.get("command_id")
        or payload.get("request_id")
        or payload.get("payment", {}).get("request_id")
        or f"corr_{door_id}_{int(datetime.now(timezone.utc).timestamp()*1000)}"
    )

    conn = get_conn()

    # Ver estado atual antes (pra auditar old_state real)
    cur = conn.execute(
        "SELECT state FROM door_state WHERE machine_id=? AND door_id=?",
        (MACHINE_ID, door_id),
    )
    row = cur.fetchone()
    current_state = row[0] if row else None

    # Só muda se estava PAID_PENDING_PICKUP (regra correta)
    # PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
    res = conn.execute(
        """
        UPDATE door_state
        SET state='PICKED_UP', updated_at=?
        WHERE machine_id=? AND door_id=? AND state='PAID_PENDING_PICKUP'
        """,
        (now_iso, MACHINE_ID, door_id),
    )

    if res.rowcount == 1:
        # Audit event: CLOSED → PICKED_UP
        # PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
        chain = _append_event(
            conn,
            machine_id=MACHINE_ID,
            door_id=door_id,
            event_type="DOOR_CLOSED_PICKED_UP",
            severity="INFO",
            correlation_id=correlation_id,
            sale_id=payload.get("sale_id"),
            command_id=payload.get("command_id"),
            old_state=current_state,
            new_state="PICKED_UP",
            payload=payload,
        )
        conn.commit()
    else:
        # Não mudou estado: ainda assim registra evento de “CLOSED observado” se quiser.
        # (opcional; eu recomendo para diagnóstico)
        chain = _append_event(
            conn,
            machine_id=MACHINE_ID,
            door_id=door_id,
            event_type="DOOR_CLOSED_IGNORED",
            severity="DEBUG",
            correlation_id=correlation_id,
            sale_id=payload.get("sale_id"),
            command_id=payload.get("command_id"),
            old_state=current_state,
            new_state=current_state,
            payload=payload,
        )
        conn.commit()

def _set_picked_up(door_id: int):
    conn = get_conn()
    # só marca PICKED_UP se estava PAID_PENDING_PICKUP (evita bagunçar)
    # PICKED_UP, provalvemente bug - isso depende de sensor OU confirmação humana - correto: DISPENSED, máquina liberou - pickup.door_opened
    now_iso = _now_iso()
    conn.execute(
        """
        UPDATE door_state
        SET state='PICKED_UP', updated_at=?
        WHERE machine_id=? AND door_id=? AND state='PAID_PENDING_PICKUP'
        """,
        (now_iso, MACHINE_ID, door_id),
    )
    conn.commit()

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return

    if payload.get("event") == "CLOSED":
        _mark_picked_up_from_closed(payload)

def run_listener():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect(MQTT_HOST, 1883, 60)
    client.subscribe(DOOR_EVENTS_TOPIC)
    client.loop_forever()

def start():
    t = threading.Thread(target=run_listener, daemon=True)
    t.start()