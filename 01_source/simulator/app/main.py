import os
import json
import time
import random
import threading
from dataclasses import dataclass
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt_broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))

REGION = os.getenv("REGION", "SP")  # SP ou PT
LOCKER_ID = os.getenv("LOCKER_ID", f"LOCKER_{REGION}_01")
FAILURE_RATE = float(os.getenv("FAILURE_RATE", "0.12"))  # 12%

PAYMENT_TRIGGERS_OPEN = os.getenv("PAYMENT_TRIGGERS_OPEN", "false").lower() == "true"
DEBUG_LOGS = os.getenv("DEBUG_LOGS", "true").lower() == "true"

# Tópicos
PAY_TOPIC = f"locker/{REGION}/pagamento"
DOOR_EVENTS_TOPIC = f"locker/{REGION}/doors/events"
DOOR_HEARTBEAT_TOPIC = f"locker/{REGION}/doors/heartbeat"
DOOR_CMD_TOPIC = f"locker/{REGION}/doors/cmd"
LIGHT_CMD_TOPIC = f"locker/{REGION}/doors/light/cmd"

# Estados possíveis (simples e úteis)
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


def choose_free_door():
    # Porta livre = IDLE ou CLOSED (pronta para novo ciclo)
    free = [d for d in doors.values() if d.state in [STATE_IDLE, STATE_CLOSED]]
    return random.choice(free) if free else None


def maybe_fail():
    return random.random() < FAILURE_RATE


def do_open_cycle(client, door: Door, payment_payload: dict):
    # 1) Abrindo
    door.state = STATE_OPENING
    door.last_event = "OPEN_CMD"

    publish(client, DOOR_EVENTS_TOPIC, {
        "ts": now_ms(),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "door_id": door.door_id,
        "event": "OPENING",
        "state": door.state,
        "payment": payment_payload,
    })

    time.sleep(random.uniform(0.2, 1.5))

    # Falha durante abertura
    if maybe_fail():
        door.state = random.choice(FAIL_STATES)
        door.last_event = "OPEN_FAIL"
        publish(client, DOOR_EVENTS_TOPIC, {
            "ts": now_ms(),
            "locker_id": LOCKER_ID,
            "region": REGION,
            "door_id": door.door_id,
            "event": "FAULT",
            "state": door.state,
            "detail": "Falha durante abertura"
        })
        return

    # 2) Aberta
    door.state = STATE_OPEN
    door.last_event = "OPENED"
    publish(client, DOOR_EVENTS_TOPIC, {
        "ts": now_ms(),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "door_id": door.door_id,
        "event": "OPENED",
        "state": door.state
    })

    # Tempo “usuário pegando produto”
    time.sleep(random.uniform(1.5, 6.0))

    # 3) Fechando
    door.state = STATE_CLOSING
    door.last_event = "CLOSE_CMD"
    publish(client, DOOR_EVENTS_TOPIC, {
        "ts": now_ms(),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "door_id": door.door_id,
        "event": "CLOSING",
        "state": door.state
    })

    time.sleep(random.uniform(0.2, 1.2))

    # Falha durante fechamento
    if maybe_fail():
        door.state = random.choice([STATE_JAMMED, STATE_SENSOR_ERROR])
        door.last_event = "CLOSE_FAIL"
        publish(client, DOOR_EVENTS_TOPIC, {
            "ts": now_ms(),
            "locker_id": LOCKER_ID,
            "region": REGION,
            "door_id": door.door_id,
            "event": "FAULT",
            "state": door.state,
            "detail": "Falha durante fechamento"
        })
        return

    # 4) Fechada
    door.state = STATE_CLOSED
    door.last_event = "CLOSED"
    door.cycles += 1
    publish(client, DOOR_EVENTS_TOPIC, {
        "ts": now_ms(),
        "locker_id": LOCKER_ID,
        "region": REGION,
        "door_id": door.door_id,
        "event": "CLOSED",
        "state": door.state,
        "cycles": door.cycles
    })


def heartbeat_loop(client):
    while True:
        snapshot = [{"door_id": d.door_id, "state": d.state, "cycles": d.cycles} for d in doors.values()]
        publish(client, DOOR_HEARTBEAT_TOPIC, {
            "ts": now_ms(),
            "locker_id": LOCKER_ID,
            "region": REGION,
            "doors": snapshot
        })
        time.sleep(10)


def random_faults_loop(client):
    while True:
        time.sleep(random.uniform(15, 40))
        if random.random() < FAILURE_RATE:
            door = random.choice(list(doors.values()))
            door.state = random.choice(FAIL_STATES)
            door.last_event = "AUTO_FAULT"
            publish(client, DOOR_EVENTS_TOPIC, {
                "ts": now_ms(),
                "locker_id": LOCKER_ID,
                "region": REGION,
                "door_id": door.door_id,
                "event": "AUTO_FAULT",
                "state": door.state,
                "detail": "Falha randômica injetada"
            })


def on_connect(client, userdata, flags, rc):
    # Subscrições sem duplicação
    topics = [DOOR_CMD_TOPIC, LIGHT_CMD_TOPIC]
    if PAYMENT_TRIGGERS_OPEN:
        topics.append(PAY_TOPIC)

    for t in topics:
        client.subscribe(t)

    log(f"[{REGION}] MQTT conectado rc={rc}. Subscrito em: {topics}")


def on_message(client, userdata, msg):
    raw = msg.payload.decode(errors="ignore")

    try:
        payload = json.loads(raw) if raw else {}
    except Exception:
        payload = {"raw": raw}

    # Log de debug (um-liner)
    log(f"[{REGION}] RX topic={msg.topic} payload={payload}")

    # --- OPEN command ---
    if msg.topic == DOOR_CMD_TOPIC:
        cmd = (payload.get("command") or "").upper()
        door_id = payload.get("door_id")

        if cmd != "OPEN":
            log(f"[{REGION}] Ignorado (cmd != OPEN): {payload}")
            return

        if not valid_door_id(door_id):
            publish(client, DOOR_EVENTS_TOPIC, {
                "ts": now_ms(),
                "locker_id": LOCKER_ID,
                "region": REGION,
                "event": "INVALID_DOOR_ID",
                "door_id": door_id,
                "detail": "door_id must be 1..24",
                "cmd": payload,
            })
            return

        door = doors.get(int(door_id))
        if not door:
            publish(client, DOOR_EVENTS_TOPIC, {
                "ts": now_ms(),
                "locker_id": LOCKER_ID,
                "region": REGION,
                "event": "UNKNOWN_DOOR",
                "door_id": int(door_id),
                "cmd": payload,
            })
            return

        t = threading.Thread(target=do_open_cycle, args=(client, door, payload), daemon=True)
        t.start()
        return

    # --- LIGHT_ON command (simulado) ---
    if msg.topic == LIGHT_CMD_TOPIC:
        cmd = (payload.get("command") or "").upper()
        door_id = payload.get("door_id")

        if cmd != "LIGHT_ON":
            log(f"[{REGION}] Ignorado (cmd != LIGHT_ON): {payload}")
            return

        if not valid_door_id(door_id):
            publish(client, DOOR_EVENTS_TOPIC, {
                "ts": now_ms(),
                "locker_id": LOCKER_ID,
                "region": REGION,
                "event": "INVALID_DOOR_ID",
                "door_id": door_id,
                "detail": "door_id must be 1..24",
                "cmd": payload,
            })
            return

        publish(client, DOOR_EVENTS_TOPIC, {
            "ts": now_ms(),
            "locker_id": LOCKER_ID,
            "region": REGION,
            "door_id": int(door_id),
            "event": "LIGHT_ON",
            "state": doors.get(int(door_id), Door(int(door_id))).state,
            "detail": "Luz ligada (simulado)",
            "cmd": payload,
        })
        return

    # --- PAYMENT fallback (desligado por padrão) ---
    if msg.topic == PAY_TOPIC and PAYMENT_TRIGGERS_OPEN:
        status = payload.get("status") or payload.get("gateway_status")
        if status not in ["approved", "aprovado", "Aprovado", "aprovado_antifraude"]:
            log(f"[{REGION}] Pagamento ignorado (status={status})")
            return

        porta = payload.get("porta") or payload.get("door_id")
        door = doors.get(int(porta)) if porta and valid_door_id(porta) else choose_free_door()
        if not door:
            publish(client, DOOR_EVENTS_TOPIC, {
                "ts": now_ms(),
                "locker_id": LOCKER_ID,
                "region": REGION,
                "event": "NO_FREE_DOOR",
                "detail": "Sem portas livres"
            })
            return

        # dispara ciclo em thread para não travar o MQTT
        t = threading.Thread(target=do_open_cycle, args=(client, door, payload), daemon=True)
        t.start()
        return

    # tópico desconhecido (não deve acontecer)
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
        f"Simulador 24 portas iniciado: region={REGION} locker={LOCKER_ID} "
        f"failure_rate={FAILURE_RATE} payment_triggers_open={PAYMENT_TRIGGERS_OPEN} debug_logs={DEBUG_LOGS}"
    )
    main()