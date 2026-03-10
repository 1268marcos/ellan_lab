import os
import json
import time
import random
import threading
from dataclasses import dataclass

import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt_broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

REGION = os.getenv("REGION", "SP").upper()  # SP ou PT
LOCKER_ID = os.getenv("LOCKER_ID", f"LOCKER_{REGION}_01")
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.12"))  # 12%

# Fallback DEV: abrir porta ao receber evento de pagamento.
# O fluxo oficial da fase V é backend -> MQTT hardware command.
PAYMENT_TRIGGERS_OPEN = os.getenv("PAYMENT_TRIGGERS_OPEN", "false").lower() == "true"
DEBUG_LOGS = os.getenv("DEBUG_LOGS", "true").lower() == "true"

PAY_TOPIC = f"locker/{REGION}/pagamento"
DOOR_EVENTS_TOPIC = f"locker/{REGION}/doors/events"
DOOR_HEARTBEAT_TOPIC = f"locker/{REGION}/doors/heartbeat"
DOOR_CMD_TOPIC = f"locker/{REGION}/doors/cmd"
LIGHT_CMD_TOPIC = f"locker/{REGION}/doors/light/cmd"

STATE_IDLE = "IDLE"
STATE_OPENING = "OPENING"
STATE_OPEN = "OPEN"
STATE_CLOSING = "CLOSING"
STATE_CLOSED = "CLOSED"
STATE_JAMMED = "JAMMED"
STATE_SENSOR_ERROR = "SENSOR_ERROR"
STATE_POWER_FAIL = "POWER_FAIL"

FAIL_STATES = [STATE_JAMMED, STATE_SENSOR_ERROR, STATE_POWER_FAIL]


@dataclass
class Door:
    door_id: int
    state: str = STATE_IDLE
    last_event: str = "BOOT"
    cycles: int = 0


doors = {i: Door(i) for i in range(1, 25)}


def log(msg: str):
    if DEBUG_LOGS:
        print(msg, flush=True)


def publish(client, topic, payload):
    client.publish(topic, json.dumps(payload), qos=0, retain=False)


def now_ms():
    return int(time.time() * 1000)


def valid_door_id(door_id) -> bool:
    try:
        n = int(door_id)
        return 1 <= n <= 24
    except Exception:
        return False


def maybe_fail():
    return random.random() < FAILURE_RATE


def emit_event(client, door_id: int | None, event: str, state: str | None = None, detail: str | None = None, cmd: dict | None = None, extra: dict | None = None):
    payload = {
        "ts": now_ms(),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "event": event,
    }

    if door_id is not None:
        payload["door_id"] = int(door_id)
    if state is not None:
        payload["state"] = state
    if detail is not None:
        payload["detail"] = detail
    if cmd is not None:
        payload["cmd"] = cmd
    if extra:
        payload.update(extra)

    publish(client, DOOR_EVENTS_TOPIC, payload)


def reset_door(door: Door):
    door.state = STATE_IDLE
    door.last_event = "RESET"


def do_open_cycle(client, door: Door, command_payload: dict):
    door.state = STATE_OPENING
    door.last_event = "OPEN_CMD"

    emit_event(
        client,
        door_id=door.door_id,
        event="OPENING",
        state=door.state,
        cmd=command_payload,
    )

    time.sleep(random.uniform(0.2, 1.5))

    if maybe_fail():
        door.state = random.choice(FAIL_STATES)
        door.last_event = "OPEN_FAIL"
        emit_event(
            client,
            door_id=door.door_id,
            event="FAULT",
            state=door.state,
            detail="Falha durante abertura",
            cmd=command_payload,
        )
        return

    door.state = STATE_OPEN
    door.last_event = "OPENED"
    emit_event(
        client,
        door_id=door.door_id,
        event="OPENED",
        state=door.state,
    )

    time.sleep(random.uniform(1.5, 6.0))

    door.state = STATE_CLOSING
    door.last_event = "CLOSE_CMD"
    emit_event(
        client,
        door_id=door.door_id,
        event="CLOSING",
        state=door.state,
    )

    time.sleep(random.uniform(0.2, 1.2))

    if maybe_fail():
        door.state = random.choice([STATE_JAMMED, STATE_SENSOR_ERROR])
        door.last_event = "CLOSE_FAIL"
        emit_event(
            client,
            door_id=door.door_id,
            event="FAULT",
            state=door.state,
            detail="Falha durante fechamento",
        )
        return

    door.state = STATE_CLOSED
    door.last_event = "CLOSED"
    door.cycles += 1
    emit_event(
        client,
        door_id=door.door_id,
        event="CLOSED",
        state=door.state,
        extra={"cycles": door.cycles},
    )


def heartbeat_loop(client):
    while True:
        snapshot = [
            {
                "door_id": d.door_id,
                "state": d.state,
                "last_event": d.last_event,
                "cycles": d.cycles,
            }
            for d in doors.values()
        ]
        publish(
            client,
            DOOR_HEARTBEAT_TOPIC,
            {
                "ts": now_ms(),
                "locker_id": LOCKER_ID,
                "region": REGION,
                "doors": snapshot,
            },
        )
        time.sleep(10)


def random_faults_loop(client):
    while True:
        time.sleep(random.uniform(15, 40))
        if random.random() < FAILURE_RATE:
            door = random.choice(list(doors.values()))
            door.state = random.choice(FAIL_STATES)
            door.last_event = "AUTO_FAULT"
            emit_event(
                client,
                door_id=door.door_id,
                event="AUTO_FAULT",
                state=door.state,
                detail="Falha randômica injetada",
            )


def on_connect(client, userdata, flags, rc):
    topics = [DOOR_CMD_TOPIC, LIGHT_CMD_TOPIC]
    if PAYMENT_TRIGGERS_OPEN:
        topics.append(PAY_TOPIC)

    for topic in topics:
        client.subscribe(topic)

    log(f"[{REGION}] MQTT conectado rc={rc}. Subscrito em: {topics}")


def on_message(client, userdata, msg):
    raw = msg.payload.decode(errors="ignore")

    try:
        payload = json.loads(raw) if raw else {}
    except Exception:
        payload = {"raw": raw}

    log(f"[{REGION}] RX topic={msg.topic} payload={payload}")

    if msg.topic == DOOR_CMD_TOPIC:
        cmd = (payload.get("command") or "").upper()
        door_id = payload.get("door_id")

        if cmd != "OPEN":
            log(f"[{REGION}] Ignorado (cmd != OPEN): {payload}")
            return

        if not valid_door_id(door_id):
            emit_event(
                client,
                door_id=None,
                event="INVALID_DOOR_ID",
                detail="door_id must be 1..24",
                cmd=payload,
                extra={"door_id_received": door_id},
            )
            return

        door = doors.get(int(door_id))
        if not door:
            emit_event(
                client,
                door_id=int(door_id),
                event="UNKNOWN_DOOR",
                cmd=payload,
            )
            return

        t = threading.Thread(target=do_open_cycle, args=(client, door, payload), daemon=True)
        t.start()
        return

    if msg.topic == LIGHT_CMD_TOPIC:
        cmd = (payload.get("command") or "").upper()
        door_id = payload.get("door_id")

        if cmd != "LIGHT_ON":
            log(f"[{REGION}] Ignorado (cmd != LIGHT_ON): {payload}")
            return

        if not valid_door_id(door_id):
            emit_event(
                client,
                door_id=None,
                event="INVALID_DOOR_ID",
                detail="door_id must be 1..24",
                cmd=payload,
                extra={"door_id_received": door_id},
            )
            return

        current_state = doors[int(door_id)].state
        emit_event(
            client,
            door_id=int(door_id),
            event="LIGHT_ON",
            state=current_state,
            detail="Luz ligada (simulado)",
            cmd=payload,
        )
        return

    if msg.topic == PAY_TOPIC and PAYMENT_TRIGGERS_OPEN:
        status = payload.get("status") or payload.get("gateway_status")
        if status not in ["approved", "aprovado", "Aprovado", "aprovado_antifraude"]:
            log(f"[{REGION}] Pagamento ignorado (status={status})")
            return

        porta = payload.get("porta") or payload.get("door_id")
        if porta and valid_door_id(porta):
            door = doors.get(int(porta))
        else:
            available = [d for d in doors.values() if d.state in [STATE_IDLE, STATE_CLOSED]]
            door = random.choice(available) if available else None

        if not door:
            emit_event(
                client,
                door_id=None,
                event="NO_FREE_DOOR",
                detail="Sem portas livres",
            )
            return

        t = threading.Thread(target=do_open_cycle, args=(client, door, payload), daemon=True)
        t.start()
        return

    log(f"[{REGION}] Ignorado (tópico não tratado): {msg.topic}")


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_HOST, MQTT_PORT, 60)

    threading.Thread(target=heartbeat_loop, args=(client,), daemon=True).start()
    threading.Thread(target=random_faults_loop, args=(client,), daemon=True).start()

    client.loop_forever()


if __name__ == "__main__":
    print(
        f"Simulador 24 portas iniciado: "
        f"region={REGION} locker={LOCKER_ID} failure_rate={FAILURE_RATE} "
        f"payment_triggers_open={PAYMENT_TRIGGERS_OPEN} debug_logs={DEBUG_LOGS}",
        flush=True,
    )
    main()