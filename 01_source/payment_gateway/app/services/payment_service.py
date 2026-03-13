# 01_source/payment_gateway/app/services/payment_service.py
import hashlib
import json
import time
import uuid

import redis
import paho.mqtt.publish as publish
from fastapi import Request

from app.core.config import settings
from app.core.hashing import canonical_json, sha256_prefixed, hash_with_pepper_version
from app.core.locker_registry import (
    LockerRegistryError,
    locker_registry,
)
from app.core.risk_engine import evaluate_risk
from app.services.sqlite_service import SQLiteService
from app.services.idempotency_service import IdempotencyService
from app.services.device_registry_service import DeviceRegistryService
from app.services.locker_backend_client import LockerBackendClient
from app.core.event_log import GatewayEventLogger
from app.core.policies import get_policy_by_region


_logger = GatewayEventLogger(
    gateway_id=settings.GATEWAY_ID,
    log_dir=settings.GATEWAY_LOG_DIR,
    log_hash_salt=settings.LOG_HASH_SALT,
)

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True,
)


def _now_ts() -> float:
    return time.time()


def _epoch() -> int:
    return int(time.time())


def _gen_request_id() -> str:
    return f"req_{uuid.uuid4().hex}"


def _gen_audit_event_id() -> str:
    return f"ae_{uuid.uuid4().hex}"


def _gen_tx_id(region: str) -> str:
    return f"tx_{region}_{uuid.uuid4().hex[:12]}"


def _get_client_ip(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for")
    if xff:
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
    ttl = 300
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
    r.lpush("transacoes", json.dumps(result, ensure_ascii=False))
    r.ltrim("transacoes", 0, 199)

    publish.single(
        f"locker/{regiao}/pagamento",
        json.dumps(result, ensure_ascii=False),
        hostname=settings.MQTT_HOST,
    )


def _insert_risk_event(sqlite: SQLiteService, data: dict):
    with sqlite.session() as conn:
        conn.execute(
            """
            INSERT INTO risk_events
            (id, request_id, event_type, decision, score, policy_id, region, locker_id, porta, created_at,
             reasons_json, signals_json, audit_event_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["request_id"],
                data["event_type"],
                data["decision"],
                data["score"],
                data["policy_id"],
                data["region"],
                data["locker_id"],
                data["porta"],
                data["created_at"],
                json.dumps(data["reasons"], ensure_ascii=False, separators=(",", ":")),
                json.dumps(data["signals"], ensure_ascii=False, separators=(",", ":")),
                data["audit_event_id"],
            ),
        )


def _attach_audit_from_event(resp: dict, ev: dict) -> None:
    if not isinstance(resp, dict):
        return

    audit = resp.setdefault("audit", {})
    chain = ev.get("chain") if isinstance(ev, dict) else None
    event_id = ev.get("event_id") if isinstance(ev, dict) else None

    if chain is not None:
        audit["chain"] = chain
    if event_id is not None:
        audit["log_event_id"] = event_id


def _resolve_locker_context(data, region: str, canal: str, metodo: str):
    requested_locker_id = getattr(data, "locker_id", None)

    locker_id = locker_registry.resolve_locker_id(
        locker_id=requested_locker_id,
        region=region,
        allow_legacy_fallback=True,
    )

    locker_cfg = locker_registry.validate_context(
        locker_id=locker_id,
        region=region,
        channel=canal,
        payment_method=metodo,
        require_active=True,
    )

    return locker_id, locker_cfg


def _resolve_currency(region: str, incoming_currency: str | None) -> tuple[str, str | None]:
    region_currency = {
        "SP": "BRL",
        "PT": "EUR",
    }
    expected_currency = region_currency.get(region, "BRL")
    normalized_incoming = (incoming_currency or "").upper().strip() or None
    return expected_currency, normalized_incoming


def _integration_status_for_method(metodo: str) -> str:
    metodo_u = (metodo or "").upper()

    if metodo_u in {"NFC", "APPLE_PAY", "GOOGLE_PAY", "MERCADO_PAGO_WALLET"}:
        return "PLANNED"

    return "ACTIVE"


def _build_pix_payload(region: str, valor: float, porta: int, locker_id: str, req_id: str) -> dict:
    expires_in_sec = 900
    expires_at_epoch = _epoch() + expires_in_sec
    qr_text = (
        f"PIX|region={region}|locker={locker_id}|porta={porta}|"
        f"valor={valor:.2f}|request_id={req_id}|exp={expires_at_epoch}"
    )
    return {
        "payment_status": "PENDING_CUSTOMER_ACTION",
        "instruction_type": "DISPLAY_QR",
        "expires_in_sec": expires_in_sec,
        "expires_at_epoch": expires_at_epoch,
        "qr_code_text": qr_text,
        "qr_code_image_base64": None,
        "copy_paste_code": qr_text,
        "instruction": "Escaneie o QRCode PIX ou copie o código para concluir o pagamento.",
    }


def _build_mbway_payload(customer_phone: str | None) -> dict:
    expires_in_sec = 900
    expires_at_epoch = _epoch() + expires_in_sec
    return {
        "payment_status": "PENDING_PROVIDER_CONFIRMATION",
        "instruction_type": "PHONE_APPROVAL",
        "expires_in_sec": expires_in_sec,
        "expires_at_epoch": expires_at_epoch,
        "customer_phone": customer_phone,
        "instruction": "Autorize o pagamento na aplicação MB WAY.",
    }


def _deterministic_digits(seed: str, length: int) -> str:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    digits = "".join(ch for ch in digest if ch.isdigit())

    while len(digits) < length:
        digest = hashlib.sha256((digest + seed).encode("utf-8")).hexdigest()
        digits += "".join(ch for ch in digest if ch.isdigit())

    return digits[:length]


def _build_multibanco_payload(valor: float, req_id: str, locker_id: str, porta: int) -> dict:
    expires_in_sec = 3600
    expires_at_epoch = _epoch() + expires_in_sec

    entity_seed = f"MB_ENTITY|{locker_id}|{porta}|{req_id}"
    reference_seed = f"MB_REFERENCE|{locker_id}|{porta}|{req_id}|{valor:.2f}"

    entity_digits = _deterministic_digits(entity_seed, 5)
    reference_digits = _deterministic_digits(reference_seed, 9)

    entity = entity_digits
    reference = reference_digits

    return {
        "payment_status": "PENDING_CUSTOMER_ACTION",
        "instruction_type": "DISPLAY_REFERENCE",
        "expires_in_sec": expires_in_sec,
        "expires_at_epoch": expires_at_epoch,
        "entity": entity,
        "reference": reference,
        "amount": round(valor, 2),
        "instruction": "Utilize a entidade e referência Multibanco para concluir o pagamento.",
    }


def _build_awaiting_integration_payload(metodo: str) -> dict:
    return {
        "payment_status": "AWAITING_INTEGRATION",
        "instruction_type": "AWAITING_INTEGRATION",
        "instruction": f"O método {metodo} está preparado no sistema, mas ainda aguarda integração completa.",
    }


def _make_base_response(
    *,
    req_id: str,
    region: str,
    endpoint: str,
    audit_event_id: str,
) -> dict:
    return {
        "request_id": req_id,
        "region": region,
        "service": "payment_gateway",
        "endpoint": endpoint,
        "timestamp": _now_ts(),
        "audit": {
            "audit_event_id": audit_event_id,
            "chain": {
                "prev_hash": None,
                "hash": None,
                "salt_fingerprint": None,
            },
        },
    }


def _store_risk_event(
    *,
    sqlite: SQLiteService,
    req_id: str,
    risk: dict,
    region: str,
    locker_id: str,
    porta: int,
    audit_event_id: str,
):
    _insert_risk_event(
        sqlite,
        {
            "id": f"re_{uuid.uuid4().hex}",
            "request_id": req_id,
            "event_type": "PAYMENT_CREATE",
            "decision": risk["decision"],
            "score": risk["score"],
            "policy_id": risk["policy"]["policy_id"],
            "region": region,
            "locker_id": locker_id,
            "porta": porta,
            "created_at": _epoch(),
            "reasons": risk["reasons"],
            "signals": risk["signals"],
            "audit_event_id": audit_event_id,
        },
    )


def _call_backend_paid_pending_pickup(locker_id: str, porta: int) -> tuple[str, dict]:
    backend_url = locker_registry.get_backend_url(locker_id)
    client = LockerBackendClient(backend_url, timeout_sec=5)
    locker_effect = client.set_state(porta=porta, state="PAID_PENDING_PICKUP")
    return backend_url, {"status": "ok", "locker": locker_effect}


def process_payment(data, request: Request, idempotency_key: str, device_fp: str, request_id: str | None):
    sqlite = SQLiteService(settings.SQLITE_PATH)
    sqlite.migrate()

    idem = IdempotencyService(sqlite, ttl_sec=settings.IDEMPOTENCY_TTL_SEC)
    devreg = DeviceRegistryService(sqlite)

    region = data.regiao.upper()
    canal = data.canal.upper()
    metodo = data.metodo.upper()
    valor = float(data.valor)
    porta = int(data.porta)
    card_type = getattr(data, "card_type", None)
    customer_phone = getattr(data, "customer_phone", None)

    endpoint = "/gateway/pagamento"
    req_id = request_id or _gen_request_id()

    try:
        locker_id, locker_cfg = _resolve_locker_context(data, region, canal, metodo)
    except LockerRegistryError as exc:
        audit_event_id = _gen_audit_event_id()
        resp = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        resp.update(
            {
                "result": "rejected",
                "error": {
                    "type": "LOCKER_CONTEXT_INVALID",
                    "message": str(exc),
                    "retryable": False,
                },
                "anti_replay": {
                    "status": "not_evaluated",
                    "idempotency_key": idempotency_key,
                    "payload_hash": None,
                },
                "severity": "HIGH",
                "severity_code": "LOCKER_CONTEXT_INVALID_V1",
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_LOCKER_CONTEXT_REJECTED",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "canal": canal,
                    "metodo": metodo,
                    "locker_id": getattr(data, "locker_id", None),
                    "error": str(exc),
                },
            }
        )
        _attach_audit_from_event(resp, ev)
        _persist_and_publish(region, resp)
        return resp

    currency_iso, incoming_currency = _resolve_currency(region, getattr(data, "currency", None))

    _logger.append_event(
        event={
            "event_type": "GATEWAY_PAYMENT_RECEIVED",
            "request_id": req_id,
            "region": region,
            "payload": {
                "endpoint": endpoint,
                "porta": porta,
                "canal": canal,
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "currency": currency_iso,
                "incoming_currency": incoming_currency,
                "currency_mismatch": bool(incoming_currency and incoming_currency != currency_iso),
                "idempotency_key": idempotency_key,
                "locker_id": locker_id,
                "order_id": getattr(data, "order_id", None),
                "locker_site_id": locker_cfg.site_id,
                "locker_backend_region": locker_cfg.backend_region,
            },
        }
    )

    payload_obj = data.model_dump() if hasattr(data, "model_dump") else data.dict()
    payload_canon = canonical_json(payload_obj)
    payload_hash = sha256_prefixed(payload_canon)

    idem_check = idem.check(endpoint, idempotency_key, payload_hash)
    if idem_check["hit"] and idem_check["status"] == "replayed":
        stored = idem_check["stored_response"]
        stored.setdefault("anti_replay", {})
        stored["anti_replay"].update(
            {
                "status": "replayed",
                "idempotency_key": idempotency_key,
                "payload_hash": payload_hash,
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_IDEMPOTENCY_REPLAY",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                    "anti_replay_status": "replayed",
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(stored, ev)
        return stored

    if idem_check["hit"] and idem_check["status"] == "payload_mismatch":
        audit_event_id = _gen_audit_event_id()
        policy = get_policy_by_region(region)

        resp = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        resp.update(
            {
                "result": "rejected",
                "error": {
                    "type": "FRAUD_SUSPECTED",
                    "message": "Operação bloqueada por risco elevado.",
                    "retryable": False,
                },
                "anti_replay": {
                    "status": "payload_mismatch",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                    "original_payload_hash": idem_check["original_payload_hash"],
                },
                "risk": {
                    "decision": "BLOCK",
                    "score": 100,
                    "score_range": "0-100",
                    "reasons": [
                        {
                            "code": "IDEMPOTENCY_PAYLOAD_MISMATCH",
                            "weight": 90,
                            "detail": "Idempotency-Key reutilizada com payload diferente",
                        }
                    ],
                    "policy": policy,
                    "policy_explicity": {
                        "policy_id": policy["policy_id"],
                        "thresholds": policy["thresholds"],
                    },
                },
                "severity": "HIGH",
                "severity_code": "RISK_BLOCK_V1",
            }
        )

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
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(resp, ev)
        _persist_and_publish(region, resp)
        return resp

    pepper_version = (settings.ANTIFRAUD_ACTIVE_PEPPER_VERSION or "v1").strip().lower()
    if pepper_version == "v2":
        pepper = settings.ANTIFRAUD_PEPPER_V2
        pepper_version = "v2"
    else:
        pepper = settings.ANTIFRAUD_PEPPER_V1
        pepper_version = "v1"

    if not pepper:
        raise RuntimeError(
            "ANTIFRAUD pepper não configurado. Defina ANTIFRAUD_PEPPER_V1 "
            "(e/ou ANTIFRAUD_PEPPER_V2) via env/.env (não comitar)."
        )

    ip = _get_client_ip(request)
    ip_hash = hash_with_pepper_version(ip, pepper, pepper_version)
    device_hash = hash_with_pepper_version(device_fp, pepper, pepper_version)

    dev = devreg.touch(device_hash=device_hash, version=settings.DEVICE_FP_VERSION)
    device_known = bool(dev["known"])

    velocity = _bump_velocity(region, ip_hash, device_hash, porta)
    integration_status = _integration_status_for_method(metodo)

    risk = evaluate_risk(
        region=region,
        canal=canal,
        metodo=metodo,
        valor=valor,
        porta=porta,
        device_known=device_known,
        velocity=velocity,
        anti_replay_status="new",
        ip_hash=ip_hash,
        device_hash=device_hash,
        card_type=card_type,
        integration_status=integration_status,
    )

    _logger.append_event(
        event={
            "event_type": "GATEWAY_RISK_DECIDED",
            "request_id": req_id,
            "region": region,
            "payload": {
                "decision": risk["decision"],
                "score": risk["score"],
                "policy_id": risk["policy"]["policy_id"],
                "top_reasons": [r.get("code") for r in (risk.get("reasons") or [])][:6],
                "locker_id": locker_id,
            },
        }
    )

    audit_event_id = _gen_audit_event_id()
    locker_summary = locker_registry.get_public_summary(locker_id)

    if risk["decision"] == "BLOCK":
        resp = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        resp.update(
            {
                "result": "rejected",
                "error": {
                    "type": "FRAUD_SUSPECTED",
                    "message": "Operação bloqueada por risco elevado.",
                    "retryable": False,
                },
                "anti_replay": {
                    "status": "new",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                },
                "risk": risk,
                "locker": locker_summary,
                "severity": "HIGH",
                "severity_code": "RISK_BLOCK_V1",
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_BLOCKED",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "decision": "BLOCK",
                    "score": risk["score"],
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(resp, ev)

        _store_risk_event(
            sqlite=sqlite,
            req_id=req_id,
            risk=risk,
            region=region,
            locker_id=locker_id,
            porta=porta,
            audit_event_id=audit_event_id,
        )

        _persist_and_publish(region, resp)

        chain = _logger.append_event(
            event={
                "event_type": "PAYMENT_CREATE",
                "decision": "BLOCK",
                "request_id": req_id,
                "audit_event_id": audit_event_id,
                "region": region,
                "locker_id": locker_id,
                "porta": porta,
                "canal": canal,
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "risk_score": risk["score"],
            }
        )
        resp["audit"]["chain"] = chain
        return resp

    if risk["decision"] == "CHALLENGE":
        resp = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        resp.update(
            {
                "result": "requires_confirmation",
                "payment": {
                    "status": "PENDING_CUSTOMER_ACTION",
                    "metodo": metodo,
                    "card_type": card_type,
                    "valor": valor,
                    "currency": currency_iso,
                    "porta": porta,
                },
                "anti_replay": {
                    "status": "new",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                },
                "risk": risk,
                "locker": locker_summary,
                "actions": [{"type": "CONFIRMATION_CODE", "expires_in_sec": 300}],
                "severity": "MEDIUM",
                "severity_code": "RISK_CHALLENGE_V1",
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_CHALLENGE",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "decision": "CHALLENGE",
                    "score": risk["score"],
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(resp, ev)

        _store_risk_event(
            sqlite=sqlite,
            req_id=req_id,
            risk=risk,
            region=region,
            locker_id=locker_id,
            porta=porta,
            audit_event_id=audit_event_id,
        )

        idem.store(endpoint, idempotency_key, payload_hash, resp, status="stored")
        _persist_and_publish(region, resp)

        chain = _logger.append_event(
            event={
                "event_type": "PAYMENT_CREATE",
                "decision": "CHALLENGE",
                "request_id": req_id,
                "audit_event_id": audit_event_id,
                "region": region,
                "locker_id": locker_id,
                "porta": porta,
                "canal": canal,
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "risk_score": risk["score"],
            }
        )
        resp["audit"]["chain"] = chain
        return resp

    if metodo == "PIX":
        payment_payload = _build_pix_payload(region, valor, porta, locker_id, req_id)

        result = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        result.update(
            {
                "result": "pending_customer_action",
                "payment": {
                    "status": payment_payload["payment_status"],
                    "gateway_status": "awaiting_customer_payment",
                    "metodo": metodo,
                    "valor": valor,
                    "currency": currency_iso,
                    "porta": porta,
                    "transaction_id": _gen_tx_id(region),
                    "instruction_type": payment_payload["instruction_type"],
                    "payload": payment_payload,
                },
                "anti_replay": {
                    "status": "new",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                },
                "risk": risk,
                "locker": locker_summary,
                "severity": "INFO",
                "severity_code": "PAYMENT_PENDING_PIX_V1",
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_PIX_CREATED",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "decision": "ALLOW",
                    "score": risk["score"],
                    "payment_status": payment_payload["payment_status"],
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(result, ev)

        _store_risk_event(
            sqlite=sqlite,
            req_id=req_id,
            risk=risk,
            region=region,
            locker_id=locker_id,
            porta=porta,
            audit_event_id=audit_event_id,
        )

        idem.store(endpoint, idempotency_key, payload_hash, result, status="stored")
        _persist_and_publish(region, result)

        chain = _logger.append_event(
            event={
                "event_type": "PAYMENT_CREATE",
                "decision": "ALLOW",
                "request_id": req_id,
                "audit_event_id": audit_event_id,
                "region": region,
                "locker_id": locker_id,
                "porta": porta,
                "canal": canal,
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "risk_score": risk["score"],
                "payment_status": payment_payload["payment_status"],
            }
        )
        result["audit"]["chain"] = chain
        return result

    if metodo == "MBWAY":
        payment_payload = _build_mbway_payload(customer_phone)

        result = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        result.update(
            {
                "result": "pending_provider_confirmation",
                "payment": {
                    "status": payment_payload["payment_status"],
                    "gateway_status": "awaiting_provider_confirmation",
                    "metodo": metodo,
                    "valor": valor,
                    "currency": currency_iso,
                    "porta": porta,
                    "transaction_id": _gen_tx_id(region),
                    "instruction_type": payment_payload["instruction_type"],
                    "payload": payment_payload,
                },
                "anti_replay": {
                    "status": "new",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                },
                "risk": risk,
                "locker": locker_summary,
                "severity": "INFO",
                "severity_code": "PAYMENT_PENDING_MBWAY_V1",
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_MBWAY_CREATED",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "decision": "ALLOW",
                    "score": risk["score"],
                    "payment_status": payment_payload["payment_status"],
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(result, ev)

        _store_risk_event(
            sqlite=sqlite,
            req_id=req_id,
            risk=risk,
            region=region,
            locker_id=locker_id,
            porta=porta,
            audit_event_id=audit_event_id,
        )

        idem.store(endpoint, idempotency_key, payload_hash, result, status="stored")
        _persist_and_publish(region, result)

        chain = _logger.append_event(
            event={
                "event_type": "PAYMENT_CREATE",
                "decision": "ALLOW",
                "request_id": req_id,
                "audit_event_id": audit_event_id,
                "region": region,
                "locker_id": locker_id,
                "porta": porta,
                "canal": canal,
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "risk_score": risk["score"],
                "payment_status": payment_payload["payment_status"],
            }
        )
        result["audit"]["chain"] = chain
        return result

    if metodo == "MULTIBANCO_REFERENCE":
        payment_payload = _build_multibanco_payload(valor, req_id, locker_id, porta)

        result = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        result.update(
            {
                "result": "pending_customer_action",
                "payment": {
                    "status": payment_payload["payment_status"],
                    "gateway_status": "awaiting_customer_payment",
                    "metodo": metodo,
                    "valor": valor,
                    "currency": currency_iso,
                    "porta": porta,
                    "transaction_id": _gen_tx_id(region),
                    "instruction_type": payment_payload["instruction_type"],
                    "payload": payment_payload,
                },
                "anti_replay": {
                    "status": "new",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                },
                "risk": risk,
                "locker": locker_summary,
                "severity": "INFO",
                "severity_code": "PAYMENT_PENDING_MULTIBANCO_V1",
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_MULTIBANCO_CREATED",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "decision": "ALLOW",
                    "score": risk["score"],
                    "payment_status": payment_payload["payment_status"],
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(result, ev)

        _store_risk_event(
            sqlite=sqlite,
            req_id=req_id,
            risk=risk,
            region=region,
            locker_id=locker_id,
            porta=porta,
            audit_event_id=audit_event_id,
        )

        idem.store(endpoint, idempotency_key, payload_hash, result, status="stored")
        _persist_and_publish(region, result)

        chain = _logger.append_event(
            event={
                "event_type": "PAYMENT_CREATE",
                "decision": "ALLOW",
                "request_id": req_id,
                "audit_event_id": audit_event_id,
                "region": region,
                "locker_id": locker_id,
                "porta": porta,
                "canal": canal,
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "risk_score": risk["score"],
                "payment_status": payment_payload["payment_status"],
            }
        )
        result["audit"]["chain"] = chain
        return result

    if metodo in {"NFC", "APPLE_PAY", "GOOGLE_PAY", "MERCADO_PAGO_WALLET"}:
        payment_payload = _build_awaiting_integration_payload(metodo)

        result = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        result.update(
            {
                "result": "awaiting_integration",
                "payment": {
                    "status": payment_payload["payment_status"],
                    "gateway_status": "awaiting_integration",
                    "metodo": metodo,
                    "valor": valor,
                    "currency": currency_iso,
                    "porta": porta,
                    "transaction_id": _gen_tx_id(region),
                    "instruction_type": payment_payload["instruction_type"],
                    "payload": payment_payload,
                },
                "anti_replay": {
                    "status": "new",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                },
                "risk": risk,
                "locker": locker_summary,
                "severity": "INFO",
                "severity_code": "PAYMENT_AWAITING_INTEGRATION_V1",
            }
        )

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_PAYMENT_AWAITING_INTEGRATION",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "decision": "ALLOW",
                    "score": risk["score"],
                    "metodo": metodo,
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(result, ev)

        _store_risk_event(
            sqlite=sqlite,
            req_id=req_id,
            risk=risk,
            region=region,
            locker_id=locker_id,
            porta=porta,
            audit_event_id=audit_event_id,
        )

        idem.store(endpoint, idempotency_key, payload_hash, result, status="stored")
        _persist_and_publish(region, result)

        chain = _logger.append_event(
            event={
                "event_type": "PAYMENT_CREATE",
                "decision": "ALLOW",
                "request_id": req_id,
                "audit_event_id": audit_event_id,
                "region": region,
                "locker_id": locker_id,
                "porta": porta,
                "canal": canal,
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "risk_score": risk["score"],
                "payment_status": payment_payload["payment_status"],
            }
        )
        result["audit"]["chain"] = chain
        return result

    try:
        backend_url, backend_json = _call_backend_paid_pending_pickup(locker_id, porta)
    except Exception as e:
        resp = _make_base_response(
            req_id=req_id,
            region=region,
            endpoint=endpoint,
            audit_event_id=audit_event_id,
        )
        resp.update(
            {
                "result": "rejected",
                "error": {
                    "type": "BACKEND_UNAVAILABLE",
                    "message": f"Falha ao chamar backend regional: {str(e)}",
                    "retryable": True,
                },
                "anti_replay": {
                    "status": "new",
                    "idempotency_key": idempotency_key,
                    "payload_hash": payload_hash,
                },
                "risk": risk,
                "locker": locker_summary,
                "severity": "HIGH",
                "severity_code": "BACKEND_CALL_FAILED",
            }
        )

        idem.store(endpoint, idempotency_key, payload_hash, resp, status="stored")

        ev = _logger.append_event(
            event={
                "event_type": "GATEWAY_BACKEND_FAILED",
                "request_id": req_id,
                "region": region,
                "payload": {
                    "backend_url": locker_registry.get_backend_url(locker_id),
                    "error": str(e),
                    "locker_id": locker_id,
                },
            }
        )
        _attach_audit_from_event(resp, ev)
        _persist_and_publish(region, resp)
        return resp

    result = _make_base_response(
        req_id=req_id,
        region=region,
        endpoint=endpoint,
        audit_event_id=audit_event_id,
    )
    result.update(
        {
            "result": "approved",
            "payment": {
                "status": "APPROVED",
                "gateway_status": "approved",
                "metodo": metodo,
                "card_type": card_type,
                "valor": valor,
                "currency": currency_iso,
                "porta": porta,
                "backend": {"url": backend_url, "timeout_sec": 5},
                "locker_effect": backend_json.get("locker"),
                "transaction_id": backend_json.get("transaction_id", _gen_tx_id(region)),
            },
            "anti_replay": {
                "status": "new",
                "idempotency_key": idempotency_key,
                "payload_hash": payload_hash,
            },
            "risk": risk,
            "locker": locker_summary,
            "severity": "INFO",
            "severity_code": "RISK_ALLOW_V1",
        }
    )

    ev = _logger.append_event(
        event={
            "event_type": "GATEWAY_PAYMENT_APPROVED",
            "request_id": req_id,
            "region": region,
            "payload": {
                "decision": "ALLOW",
                "score": risk["score"],
                "locker_id": locker_id,
            },
        }
    )
    _attach_audit_from_event(result, ev)

    _store_risk_event(
        sqlite=sqlite,
        req_id=req_id,
        risk=risk,
        region=region,
        locker_id=locker_id,
        porta=porta,
        audit_event_id=audit_event_id,
    )

    idem.store(endpoint, idempotency_key, payload_hash, result, status="stored")
    _persist_and_publish(region, result)

    chain = _logger.append_event(
        event={
            "event_type": "PAYMENT_CREATE",
            "decision": "ALLOW",
            "request_id": req_id,
            "audit_event_id": audit_event_id,
            "region": region,
            "locker_id": locker_id,
            "porta": porta,
            "canal": canal,
            "metodo": metodo,
            "card_type": card_type,
            "valor": valor,
            "risk_score": risk["score"],
            "payment_status": "APPROVED",
        }
    )
    result["audit"]["chain"] = chain
    return result