# 01_source/payment_gateway/app/services/payment_service.py
import json
import time
import uuid
import requests
import redis
import paho.mqtt.publish as publish
from fastapi import Request

# 🔥 Opção B: Importar o settings object em vez de variáveis individuais
from app.core.config import settings

# from app.core.hashing import canonical_json, hash_with_pepper, sha256_prefixed
from app.core.hashing import canonical_json, sha256_prefixed, hash_with_pepper_version
from app.core.risk_engine import evaluate_risk
from app.services.sqlite_service import SQLiteService
from app.services.idempotency_service import IdempotencyService
from app.services.device_registry_service import DeviceRegistryService
from app.services.locker_backend_client import LockerBackendClient
from app.core.event_log import GatewayEventLogger
from app.core.policies import get_policy_by_region

# 🔥 Usar settings para todas as configurações
_logger = GatewayEventLogger(
    gateway_id=settings.GATEWAY_ID,
    log_dir=settings.GATEWAY_LOG_DIR,
    log_hash_salt=settings.LOG_HASH_SALT,
)

# Redis com host do settings
# r = redis.Redis(host=settings.REDIS_HOST, port=6379, decode_responses=True)
# Redis com host e porta do settings
r = redis.Redis(
    host=settings.REDIS_HOST, 
    port=settings.REDIS_PORT,  # 🔥 ADICIONAR A PORTA
    decode_responses=True
)

def _now_ts() -> float:
    return time.time()


def _epoch() -> int:
    return int(time.time())


def _gen_request_id() -> str:
    return f"req_{uuid.uuid4().hex}"


def _gen_audit_event_id() -> str:
    return f"ae_{uuid.uuid4().hex}"


def _get_client_ip(request: Request) -> str:
    # Prioriza X-Forwarded-For se existir
    xff = request.headers.get("x-forwarded-for")
    if xff:
        # pega o primeiro IP
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "0.0.0.0"


def _velocity_keys(region: str, ip_hash: str, device_hash: str, porta: int) -> dict:
    reg = (region or "XX").upper()
    return {
        "ip_5m": f"v:{reg}:ip:{ip_hash}:5m",
        "device_5m": f"v:{reg}:dev:{device_hash}:5m",
        "porta_5m": f"v:{reg}:porta:{porta}:5m",
    }


def _bump_velocity(region: str, ip_hash: str, device_hash: str, porta: int) -> dict:
    keys = _velocity_keys(region, ip_hash, device_hash, porta)
    ttl = 300  # 5 minutos
    out = {}

    for name, key in keys.items():
        try:
            val = int(r.incr(key))
            r.expire(key, ttl)
            out[name] = val
        except Exception:
            out[name] = 0

    return out


def _persist_and_publish(regiao: str, result: dict):
    # Mantém tua lógica
    r.lpush("transacoes", json.dumps(result, ensure_ascii=False))
    r.ltrim("transacoes", 0, 199)

    publish.single(
        f"locker/{regiao}/pagamento",
        json.dumps(result, ensure_ascii=False),
        hostname=settings.MQTT_HOST  # 🔥 Usar settings
    )


def _insert_risk_event(sqlite: SQLiteService, data: dict):
    # data deve conter os campos do contrato interno
    with sqlite.session() as conn:
        conn.execute(
            """
            INSERT INTO risk_events
            (id, request_id, event_type, decision, score, policy_id, region, locker_id, porta, created_at,
             reasons_json, signals_json, audit_event_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"], data["request_id"], data["event_type"], data["decision"], data["score"], data["policy_id"],
                data["region"], data["locker_id"], data["porta"], data["created_at"],
                json.dumps(data["reasons"], ensure_ascii=False, separators=(",", ":")),
                json.dumps(data["signals"], ensure_ascii=False, separators=(",", ":")),
                data["audit_event_id"],
            )
        )


def process_payment(data, request: Request, idempotency_key: str, device_fp: str, request_id: str | None):
    # --- Setup (SQLite + migrate) ---
    # 🔥 Usar settings para todas as configurações
    sqlite = SQLiteService(settings.SQLITE_PATH)
    sqlite.migrate()

    idem = IdempotencyService(sqlite, ttl_sec=settings.IDEMPOTENCY_TTL_SEC)
    devreg = DeviceRegistryService(sqlite)

    # --- Normalize ---
    region = data.regiao.upper()
    metodo = data.metodo.upper()
    valor = float(data.valor)
    porta = int(data.porta)

    REGION_CURRENCY = {
        "SP": "BRL",
        "PT": "EUR",
    }

    expected_currency = REGION_CURRENCY.get(region, "BRL")
    incoming_currency = (getattr(data, "currency", None) or "").upper().strip()

    # Regra de domínio:
    # a moeda é definida pela região, não pelo cliente/frontend.
    currencyISO = expected_currency

    endpoint = "/gateway/pagamento"
    req_id = request_id or _gen_request_id()

    ev_received = _logger.append_event(
        event={
            "event_type": "GATEWAY_PAYMENT_RECEIVED",
            "request_id": req_id,
            "region": region,
            "payload": {
                "endpoint": endpoint,
                "porta": porta,
                "metodo": metodo,
                "valor": valor,
                "currency": currencyISO,
                "incoming_currency": incoming_currency or None,
                "currency_mismatch": bool(incoming_currency and incoming_currency != expected_currency),
                "idempotency_key": idempotency_key,
            },
        }
    )

    # Canonical payload hash (idempotency)
    payload_obj = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    payload_canon = canonical_json(payload_obj)
    payload_hash = sha256_prefixed(payload_canon)

    # --- Idempotency check ---
    idem_check = idem.check(endpoint, idempotency_key, payload_hash)
    if idem_check["hit"] and idem_check["status"] == "replayed":
        # Retorna resposta armazenada (replay) + marca anti_replay
        stored = idem_check["stored_response"]
        stored.setdefault("anti_replay", {})
        stored["anti_replay"].update({
            "status": "replayed",
            "idempotency_key": idempotency_key,
            "payload_hash": payload_hash,
        })
        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_IDEMPOTENCY_REPLAY",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                    "anti_replay_status": "replayed",
                },
            }
        )
        _attach_audit_from_event(stored, ev)
        return stored

    if idem_check["hit"] and idem_check["status"] == "payload_mismatch":
        # BLOCK imediato (sinal forte)
        audit_event_id = _gen_audit_event_id()
        
        policy = get_policy_by_region(region)

        resp = {
            "request_id": req_id,
            "region": region,
            "service": "payment_gateway",
            "endpoint": endpoint,
            "timestamp": _now_ts(),
            "result": "rejected",
            "error": {
                "type": "FRAUD_SUSPECTED",
                "message": "Operação bloqueada por risco elevado.",
                "retryable": False
            },
            "anti_replay": {
                "status": "payload_mismatch",
                "idempotency_key": idempotency_key,
                "payload_hash": payload_hash,
                "original_payload_hash": idem_check["original_payload_hash"]
            },
            "risk": {
                "decision": "BLOCK",
                "score": 100,
                "score_range": "0-100",
                "reasons": [
                    {"code": "IDEMPOTENCY_PAYLOAD_MISMATCH", "weight": 90, "detail": "Idempotency-Key reutilizada com payload diferente"}
                ],
                "policy": policy,
                "policy_explicity": {"policy_id": policy["policy_id"], "thresholds": policy["thresholds"]}
            },
            "severity": "HIGH",
            "severity_code": "RISK_BLOCK_V1",
            "audit": {"audit_event_id": audit_event_id, "chain": {"prev_hash": None, "hash": None, "salt_fingerprint": None}}
        }
        
        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_IDEMPOTENCY_MISMATCH",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                    "original_payload_hash": idem_check["original_payload_hash"],
                    "anti_replay_status": "payload_mismatch",
                },
            }
        )
        _attach_audit_from_event(resp, ev)
        _persist_and_publish(region, resp)
        return resp

    # --- Hash device & IP ---
    # Selecionar (Escolher) o pepper ativo (versionado) - produção-ready
    pepper_version = (settings.ANTIFRAUD_ACTIVE_PEPPER_VERSION or "v1").strip().lower()
    if pepper_version == "v2":
        pepper = settings.ANTIFRAUD_PEPPER_V2
        pepper_version = "v2"
    else:
        pepper = settings.ANTIFRAUD_PEPPER_V1
        pepper_version = "v1"
 
    if not pepper:
        # Em dev isso evita hashes fracos; Em produção, isso deve impedir a app de rodar, impede subir sem segredo.
        raise RuntimeError("ANTIFRAUD pepper não configurado. Defina ANTIFRAUD_PEPPER_V1 (e/ou ANTIFRAUD_PEPPER_V2) via env/.env (não comitar).")

    ip = _get_client_ip(request)
    ip_hash = hash_with_pepper_version(ip, pepper, pepper_version)
    device_hash = hash_with_pepper_version(device_fp, pepper, pepper_version)

    # --- Device registry ---
    dev = devreg.touch(device_hash=device_hash, version=settings.DEVICE_FP_VERSION)
    device_known = bool(dev["known"])

    # --- Velocity (Redis) ---
    velocity = _bump_velocity(region, ip_hash, device_hash, porta)

    # --- Risk evaluate ---
    # anti_replay_status: "new" aqui
    risk = evaluate_risk(
        region=region,
        metodo=metodo,
        valor=valor,
        porta=porta,
        device_known=device_known,
        velocity=velocity,
        anti_replay_status="new",
        ip_hash=ip_hash,
        device_hash=device_hash,
    )

    ev_risk = _logger.append_event(
        event={
            "event_type": "GATEWAY_RISK_DECIDED",
            "request_id": req_id,
            "region": region,
            "payload": {
                "decision": risk["decision"],
                "score": risk["score"],
                "policy_id": risk["policy"]["policy_id"],
                "top_reasons": [r.get("code") for r in (risk.get("reasons") or [])][:6],
            },
        }
    )

    audit_event_id = _gen_audit_event_id()

    # --- Decide ---
    if risk["decision"] == "BLOCK":
        resp = {
            "request_id": req_id,
            "region": region,
            "service": "payment_gateway",
            "endpoint": endpoint,
            "timestamp": _now_ts(),
            "result": "rejected",
            "error": {"type": "FRAUD_SUSPECTED", "message": "Operação bloqueada por risco elevado.", "retryable": False},
            "anti_replay": {"status": "new", "idempotency_key": idempotency_key, "payload_hash": payload_hash},
            "risk": risk,
            "severity": "HIGH",
            "severity_code": "RISK_BLOCK_V1",
            "audit": {"audit_event_id": audit_event_id, "chain": {"prev_hash": None, "hash": None, "salt_fingerprint": None}},
        }

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_BLOCKED",
                "request_id": req_id,
                "region": region,
                "payload": {"decision": "BLOCK", "score": risk["score"]},
            }
        )
        _attach_audit_from_event(resp, ev)     

        _insert_risk_event(sqlite, {
            "id": f"re_{uuid.uuid4().hex}",
            "request_id": req_id,
            "event_type": "PAYMENT_CREATE",
            "decision": risk["decision"],
            "score": risk["score"],
            "policy_id": risk["policy"]["policy_id"],
            "region": region,
            "locker_id": f"CACIFO-{region}-001",
            "porta": porta,
            "created_at": _epoch(),
            "reasons": risk["reasons"],
            "signals": risk["signals"],
            "audit_event_id": audit_event_id,
        })

        _persist_and_publish(region, resp)

        chain = _logger.append_event(event={
            "event_type": "PAYMENT_CREATE",
            "decision": "BLOCK",
            "request_id": req_id,
            "audit_event_id": audit_event_id,
            "region": region,
            "porta": porta,
            "metodo": metodo,
            "valor": valor,
            "risk_score": risk["score"],
        })
        resp["audit"]["chain"] = chain
        return resp

    if risk["decision"] == "CHALLENGE":
        resp = {
            "request_id": req_id,
            "region": region,
            "service": "payment_gateway",
            "endpoint": endpoint,
            "timestamp": _now_ts(),
            "result": "requires_confirmation",
            "payment": {"status": "pendente", "metodo": metodo, "valor": valor, "currency": currencyISO, "porta": porta},
            "anti_replay": {"status": "new", "idempotency_key": idempotency_key, "payload_hash": payload_hash},
            "risk": risk,
            "actions": [{"type": "CONFIRMATION_CODE", "expires_in_sec": 300}],
            "severity": "MEDIUM",
            "severity_code": "RISK_CHALLENGE_V1",
            "audit": {"audit_event_id": audit_event_id, "chain": {"prev_hash": None, "hash": None, "salt_fingerprint": None}},
        }

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_CHALLENGE",
                "request_id": req_id,
                "region": region,
                "payload": {"decision": "CHALLENGE", "score": risk["score"]},
            }
        )
        _attach_audit_from_event(resp, ev)

        _insert_risk_event(sqlite, {
            "id": f"re_{uuid.uuid4().hex}",
            "request_id": req_id,
            "event_type": "PAYMENT_CREATE",
            "decision": risk["decision"],
            "score": risk["score"],
            "policy_id": risk["policy"]["policy_id"],
            "region": region,
            "locker_id": f"CACIFO-{region}-001",
            "porta": porta,
            "created_at": _epoch(),
            "reasons": risk["reasons"],
            "signals": risk["signals"],
            "audit_event_id": audit_event_id,
        })

        # Challenge também pode ser idempotente (para evitar spam)
        idem.store(endpoint, idempotency_key, payload_hash, resp, status="stored")
        _persist_and_publish(region, resp)

        chain = _logger.append_event(event={
            "event_type": "PAYMENT_CREATE",
            "decision": "CHALLENGE",
            "request_id": req_id,
            "audit_event_id": audit_event_id,
            "region": region,
            "porta": porta,
            "metodo": metodo,
            "valor": valor,
            "risk_score": risk["score"],
        })
        resp["audit"]["chain"] = chain
        return resp

    # --- ALLOW: chama backend regional para atualizar estado ---
    backend_url = settings.get_regional_url(region)
    client = LockerBackendClient(backend_url, timeout_sec=5)
    
    try:
        # Pagamento aprovado: porta fica reservada para retirada
        # XX  backend_resp = client.set_state(porta=porta, state="PAID_PENDING_PICKUP")
        # XX  backend_json = {"status": "ok", "locker": backend_resp}
        locker_effect = client.set_state(porta=porta, state="PAID_PENDING_PICKUP")
        backend_json = {"status": "ok", "locker": locker_effect}

    except Exception as e:
        # responde em JSON rico (sem derrubar)
        audit_event_id = _gen_audit_event_id()
        resp = {
            "request_id": req_id,
            "region": region,
            "service": "payment_gateway",
            "endpoint": endpoint,
            "timestamp": _now_ts(),
            "result": "rejected",
            "error": {
                "type": "BACKEND_UNAVAILABLE",
                "message": f"Falha ao chamar backend regional: {str(e)}",
                "retryable": True
            },
            "anti_replay": {"status": "new", "idempotency_key": idempotency_key, "payload_hash": payload_hash},
            "risk": risk,
            "severity": "HIGH",
            "severity_code": "BACKEND_CALL_FAILED",
            "audit": {"audit_event_id": audit_event_id, "chain": {"prev_hash": None, "hash": None, "salt_fingerprint": None}},
        }
        # grava idempotency para evitar storm, opcional:
        idem.store(endpoint, idempotency_key, payload_hash, resp, status="stored")
        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_BACKEND_FAILED",
                "request_id": req_id,
                "region": region,
                "payload": {"backend_url": backend_url, "error": str(e)},
            }
        )
        _attach_audit_from_event(resp, ev)
        _persist_and_publish(region, resp)
        return resp


    result = {
        "request_id": req_id,
        "region": region,
        "service": "payment_gateway",
        "endpoint": endpoint,
        "timestamp": _now_ts(),

        "result": "approved",
        "payment": {
            "status": backend_json.get("status", "aprovado"),
            "gateway_status": "aprovado",
            "metodo": metodo,
            "valor": valor,
            "currency": currencyISO,
            "porta": porta,
            "backend": {"url": backend_url, "timeout_sec": 5},
            "locker_effect": backend_json.get("locker"),
            "transaction_id": backend_json.get("transaction_id", f"tx_{region}_{uuid.uuid4().hex[:12]}")
        },

        "anti_replay": {"status": "new", "idempotency_key": idempotency_key, "payload_hash": payload_hash},
        "risk": risk,

        "severity": "INFO",
        "severity_code": "RISK_ALLOW_V1",

        "audit": {"audit_event_id": audit_event_id, "chain": {"prev_hash": None, "hash": None, "salt_fingerprint": None}},
    }

    ev = _logger.append_event(
        event={
            "event_type": "GATEWAY_PAYMENT_APPROVED",
            "request_id": req_id,
            "region": region,
            "payload": {"decision": "ALLOW", "score": risk["score"]},
        }
    )
    _attach_audit_from_event(result, ev)

    _insert_risk_event(sqlite, {
        "id": f"re_{uuid.uuid4().hex}",
        "request_id": req_id,
        "event_type": "PAYMENT_CREATE",
        "decision": risk["decision"],
        "score": risk["score"],
        "policy_id": risk["policy"]["policy_id"],
        "region": region,
        "locker_id": f"CACIFO-{region}-001",
        "porta": porta,
        "created_at": _epoch(),
        "reasons": risk["reasons"],
        "signals": risk["signals"],
        "audit_event_id": audit_event_id,
    })

    idem.store(endpoint, idempotency_key, payload_hash, result, status="stored")
    _persist_and_publish(region, result)

    chain = _logger.append_event(event={
        "event_type": "PAYMENT_CREATE",
        "decision": "ALLOW",
        "request_id": req_id,
        "audit_event_id": audit_event_id,
        "region": region,
        "porta": porta,
        "metodo": metodo,
        "valor": valor,
        "risk_score": risk["score"],
    })
    result["audit"]["chain"] = chain
    return result


# Isso é um helper
def _attach_audit_from_event(resp: dict, ev: dict) -> None:
    """
    Garante audit.chain + audit.log_event_id na resposta.
    Funciona mesmo se resp ainda não tiver 'audit'.
    """
    if not isinstance(resp, dict):
        return

    audit = resp.setdefault("audit", {})
    # mantém audit_event_id se já existir
    chain = ev.get("chain") if isinstance(ev, dict) else None
    event_id = ev.get("event_id") if isinstance(ev, dict) else None

    if chain is not None:
        audit["chain"] = chain
    if event_id is not None:
        audit["log_event_id"] = event_id