from __future__ import annotations

import time
from typing import Any

import requests

from app.core.config import settings
from app.services.sefaz_svrs_batch_stub_service import (
    query_svrs_issue_batch_stub,
    submit_svrs_issue_batch_stub,
)

import random

def _simulate_stub_scenario(stub_scenario: str, invoice_id: str, payload: dict | None = None, attempts: int = 1) -> dict[str, Any]:
    """
    Simula diferentes cenários de stub para testes.
    stub_scenario pode ser:
      - 'intermittent': falha aleatória (default 30% das vezes; configurável via 'intermittent_rate')
      - 'slow_response': delay artificial de 2-5 segundos (configurável via 'slow_delay_sec')
      - 'partial_success': retorna sucesso mas omite campos opcionais
      - 'rate_limit_then_success': retorna erro 429 (fail_attempts_before_success vezes), depois sucesso

    O comportamento é tornável determinístico por teste usando random.seed(invoice_id).
    Parâmetros podem ser passados via payload:
        - intermittent_rate: float (0.0 a 1.0, default 0.3)
        - slow_delay_sec: float (default random entre 2.0 e 5.0)
        - fail_attempts_before_success: int (rate_limit_then_success; default 2)
    """
    payload = payload or {}
    # Determinismo por invoice_id (ou order_id)
    random.seed(str(invoice_id))
    result = {}

    if stub_scenario == "intermittent":
        rate = float(payload.get("intermittent_rate", 0.3))
        val = random.random()
        if val < rate:
            return {
                "success": False,
                "error": {
                    "code": "PROVIDER_SIM_INTERMITTENT",
                    "message": f"Intermittent failure (rate={rate:.2f}, random={val:.2f})",
                    "retryable": True
                }
            }
        else:
            return {"success": True, "status": "ok", "note": "intermittent passed"}

    elif stub_scenario == "slow_response":
        min_delay = 2.0
        max_delay = 5.0
        delay_sec = float(payload.get("slow_delay_sec", random.uniform(min_delay, max_delay)))
        time.sleep(delay_sec)
        return {"success": True, "status": "ok", "delay_sec": delay_sec}

    elif stub_scenario == "partial_success":
        base_resp = {
            "success": True,
            "invoice_number": f"99999{str(invoice_id)[-3:]}",
            "fiscal_code": f"ABC{str(invoice_id)[-5:]}",
            "extra_field_1": "should be omitted",
            "extra_field_2": "should be omitted",
            "optional_note": "This field is optional",
        }
        # Omite campos opcionais/extra
        del base_resp["extra_field_1"]
        del base_resp["extra_field_2"]
        base_resp.pop("optional_note", None)
        return base_resp

    elif stub_scenario == "rate_limit_then_success":
        fail_count = max(1, int(payload.get("fail_attempts_before_success", 2)))
        # Para determinismo, gerar o mesmo "sequência de falha" por invoice_id e attempts:
        seq = [429] * fail_count + [200] * 10
        # attempts começa em 1, seq é 0-indexed
        idx = int(attempts) - 1
        status = seq[idx] if idx < len(seq) else 200
        if status == 429:
            return {
                "success": False,
                "error": {
                    "code": "PROVIDER_RATE_LIMITED",
                    "message": f"Stub rate limited (429): attempt {attempts} of {fail_count}",
                    "retryable": True
                }
            }
        else:
            return {"success": True, "status": "ok", "attempt": attempts, "note": "rate limited passed"}

    else:
        return {
            "success": False,
            "error": {
                "code": "PROVIDER_STUB_SCENARIO_UNKNOWN",
                "message": f"Unknown stub_scenario: {stub_scenario}",
                "retryable": False
            }
        }


# Exemplos de payload para cada cenário:
#
# 1. Intermittent:
#    {"stub_scenario": "intermittent", "intermittent_rate": 0.5}
#
# 2. Slow response:
#    {"stub_scenario": "slow_response", "slow_delay_sec": 3.2}
#
# 3. Partial success:
#    {"stub_scenario": "partial_success"}
#
# 4. Rate limit then success (3 tentativas):
#    {"stub_scenario": "rate_limit_then_success", "fail_attempts_before_success": 3}
#
# Para testar via endpoint:
# POST /admin/fiscal/providers/stub/svrs/smoke-issue/{order_id}
# Envie no payload JSON, por exemplo:
#   {
#     "stub_scenario": "intermittent",
#     "intermittent_rate": 0.4
#   }
# Ou:
#   {
#     "stub_scenario": "rate_limit_then_success",
#     "fail_attempts_before_success": 2
#   }
# E observe a resposta variando por tentativas e invoice_id especificado.

class RealProviderClientError(Exception):
    def __init__(self, *, code: str, message: str, retryable: bool, attempts: int):
        super().__init__(message)
        self.code = code
        self.message = message
        self.retryable = retryable
        self.attempts = attempts

    def __str__(self) -> str:
        return (
            f"{self.code}: {self.message} "
            f"(retryable={self.retryable}, attempts={self.attempts})"
        )


CANONICAL_PROVIDER_ERROR_CODES = [
    "PROVIDER_TIMEOUT",
    "PROVIDER_RATE_LIMITED",
    "PROVIDER_HTTP_5XX",
    "PROVIDER_AUTH_ERROR",
    "PROVIDER_VALIDATION_ERROR",
    "PROVIDER_REJECTED",
    "PROVIDER_STUB_SCENARIO_UNKNOWN",
    "PROVIDER_HTTP_RETRYABLE",
    "PROVIDER_HTTP_REJECTED",
    "PROVIDER_INVALID_JSON",
    "PROVIDER_RESPONSE_NOT_OBJECT",
    "PROVIDER_BATCH_PROCESSING",
    "PROVIDER_BASE_URL_MISSING",
    "PROVIDER_REQUEST_FAILED",
    "PROVIDER_HEALTH_RETRYABLE",
    "PROVIDER_HEALTH_REJECTED",
    "PROVIDER_HEALTH_FAILED",
]


def list_canonical_error_codes() -> list[str]:
    return list(CANONICAL_PROVIDER_ERROR_CODES)


def _provider_base_url(country: str) -> str:
    c = country.upper()
    if c == "BR":
        return str(settings.fiscal_real_provider_base_url_br or "").strip()
    if c == "PT":
        return str(settings.fiscal_real_provider_base_url_pt or "").strip()
    return ""


def _provider_api_key(country: str) -> str | None:
    c = country.upper()
    if c == "BR":
        return settings.fiscal_real_provider_api_key_br
    if c == "PT":
        return settings.fiscal_real_provider_api_key_pt
    return None


def _headers(country: str) -> dict[str, str]:
    h = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    k = _provider_api_key(country)
    if k:
        h["Authorization"] = f"Bearer {k}"
    return h


def _raise_client_error(*, code: str, message: str, retryable: bool, attempts: int) -> None:
    raise RealProviderClientError(
        code=code,
        message=message,
        retryable=retryable,
        attempts=attempts,
    )


def _simulate_stub_scenario(*, json_payload: dict[str, Any], attempt: int, retries: int) -> dict[str, Any] | None:
    """
    Matriz determinística de falhas para evolução STUB-READY sem provider oficial.
    Cenários disponíveis via payload:
      - stub_scenario=timeout|rate_limit|http_5xx|auth_error|validation_error|provider_rejected
      - stub_success_on_attempt=N (opcional): simula recuperação no N-esimo attempt
    """
    scenario = str(json_payload.get("stub_scenario") or "").strip().lower()
    if not scenario:
        return None

    success_on_attempt = int(json_payload.get("stub_success_on_attempt") or 0)
    current_attempt = attempt + 1
    if scenario == "svrs_batch_async":
        submit_out = submit_svrs_issue_batch_stub(json_payload)
        receipt = str(submit_out.get("receipt_number") or "").strip()
        poll_count = max(1, int(json_payload.get("stub_batch_poll_count") or 1))
        query_out: dict[str, Any] = {}
        for _ in range(poll_count):
            query_out = query_svrs_issue_batch_stub(receipt)
        if str(query_out.get("batch_status") or "").upper() != "PROCESSED":
            _raise_client_error(
                code="PROVIDER_BATCH_PROCESSING",
                message=f"svrs_batch_async not processed yet receipt={receipt}",
                retryable=True,
                attempts=current_attempt,
            )
        result = query_out.get("result") if isinstance(query_out.get("result"), dict) else {}
        return {
            "status": "AUTHORIZED",
            "provider_status": result.get("provider_status") or "AUTHORIZED",
            "provider_code": result.get("provider_code") or "100",
            "provider_message": result.get("provider_message") or "Autorizado por lote assíncrono stub.",
            "protocol_number": result.get("protocol_number"),
            "receipt_number": result.get("receipt_number") or receipt,
            "access_key": result.get("access_key"),
            "batch_status": "PROCESSED",
            "batch_async": True,
        }

    if success_on_attempt > 0 and current_attempt >= success_on_attempt:
        return {
            "status": "AUTHORIZED",
            "provider_status": "AUTHORIZED",
            "provider_code": "100",
            "provider_message": f"Recovered from stub scenario '{scenario}' on attempt {current_attempt}.",
            "protocol_number": f"STUB-PROTOCOL-{current_attempt}",
            "receipt_number": f"STUB-RECEIPT-{current_attempt}",
        }

    if scenario == "timeout":
        _raise_client_error(
            code="PROVIDER_TIMEOUT",
            message="simulated timeout in stub scenario",
            retryable=True,
            attempts=current_attempt,
        )
    if scenario == "rate_limit":
        _raise_client_error(
            code="PROVIDER_RATE_LIMITED",
            message="simulated 429 rate limit in stub scenario",
            retryable=True,
            attempts=current_attempt,
        )
    if scenario == "http_5xx":
        _raise_client_error(
            code="PROVIDER_HTTP_5XX",
            message="simulated 5xx provider failure in stub scenario",
            retryable=True,
            attempts=current_attempt,
        )
    if scenario == "auth_error":
        _raise_client_error(
            code="PROVIDER_AUTH_ERROR",
            message="simulated authentication error in stub scenario",
            retryable=False,
            attempts=current_attempt,
        )
    if scenario == "validation_error":
        _raise_client_error(
            code="PROVIDER_VALIDATION_ERROR",
            message="simulated payload validation error in stub scenario",
            retryable=False,
            attempts=current_attempt,
        )
    if scenario == "provider_rejected":
        _raise_client_error(
            code="PROVIDER_REJECTED",
            message="simulated provider rejection in stub scenario",
            retryable=False,
            attempts=current_attempt,
        )

    _raise_client_error(
        code="PROVIDER_STUB_SCENARIO_UNKNOWN",
        message=f"unknown stub scenario '{scenario}'",
        retryable=False,
        attempts=current_attempt,
    )


def _request_json_with_retry(*, method: str, url: str, json_payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    retries = max(0, int(settings.fiscal_real_provider_retries))
    timeout = max(1, int(settings.fiscal_real_provider_timeout_sec))
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            stub_out = _simulate_stub_scenario(json_payload=json_payload, attempt=attempt, retries=retries)
            if isinstance(stub_out, dict):
                return stub_out
            resp = requests.request(method=method, url=url, json=json_payload, headers=headers, timeout=timeout)
            if resp.status_code >= 500 or resp.status_code == 429:
                _raise_client_error(
                    code="PROVIDER_HTTP_RETRYABLE",
                    message=f"provider_http_status={resp.status_code} body={resp.text[:400]}",
                    retryable=True,
                    attempts=attempt + 1,
                )
            if resp.status_code >= 400:
                _raise_client_error(
                    code="PROVIDER_HTTP_REJECTED",
                    message=f"provider_request_rejected status={resp.status_code} body={resp.text[:400]}",
                    retryable=False,
                    attempts=attempt + 1,
                )
            try:
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                _raise_client_error(
                    code="PROVIDER_INVALID_JSON",
                    message="provider_invalid_json_response",
                    retryable=False,
                    attempts=attempt + 1,
                )
            if not isinstance(data, dict):
                _raise_client_error(
                    code="PROVIDER_RESPONSE_NOT_OBJECT",
                    message="provider_response_not_object",
                    retryable=False,
                    attempts=attempt + 1,
                )
            return data
        except (requests.RequestException, RealProviderClientError) as exc:
            last_exc = exc
            retryable = True
            if isinstance(exc, RealProviderClientError):
                retryable = exc.retryable
            if not retryable:
                break
            if attempt >= retries:
                break
            time.sleep(min(0.5 * (2**attempt), 2.0))
    if isinstance(last_exc, RealProviderClientError):
        raise RealProviderClientError(
            code=last_exc.code,
            message=f"provider_request_failed retries_exhausted error={last_exc.message}",
            retryable=last_exc.retryable,
            attempts=max(1, int(last_exc.attempts or (retries + 1))),
        )
    raise RealProviderClientError(
        code="PROVIDER_REQUEST_FAILED",
        message=f"provider_request_failed retries_exhausted error={last_exc}",
        retryable=True,
        attempts=retries + 1,
    )


def issue_invoice(country: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = _provider_base_url(country)
    if not base:
        _raise_client_error(
            code="PROVIDER_BASE_URL_MISSING",
            message=f"provider_base_url_missing country={country}",
            retryable=False,
            attempts=0,
        )
    url = f"{base.rstrip('/')}/issue"
    return _request_json_with_retry(
        method="POST",
        url=url,
        json_payload=payload,
        headers=_headers(country),
    )


def cancel_invoice(country: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = _provider_base_url(country)
    if not base:
        _raise_client_error(
            code="PROVIDER_BASE_URL_MISSING",
            message=f"provider_base_url_missing country={country}",
            retryable=False,
            attempts=0,
        )
    url = f"{base.rstrip('/')}/cancel"
    return _request_json_with_retry(
        method="POST",
        url=url,
        json_payload=payload,
        headers=_headers(country),
    )


def correction_event(country: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = _provider_base_url(country)
    if not base:
        _raise_client_error(
            code="PROVIDER_BASE_URL_MISSING",
            message=f"provider_base_url_missing country={country}",
            retryable=False,
            attempts=0,
        )
    url = f"{base.rstrip('/')}/correction-event"
    return _request_json_with_retry(
        method="POST",
        url=url,
        json_payload=payload,
        headers=_headers(country),
    )


def health_check(country: str) -> tuple[int | None, dict[str, Any]]:
    base = _provider_base_url(country)
    if not base:
        _raise_client_error(
            code="PROVIDER_BASE_URL_MISSING",
            message=f"provider_base_url_missing country={country}",
            retryable=False,
            attempts=0,
        )
    url = f"{base.rstrip('/')}/health"
    retries = max(0, int(settings.fiscal_real_provider_retries))
    timeout = max(1, int(settings.fiscal_real_provider_timeout_sec))
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, headers=_headers(country), timeout=timeout)
            body: dict[str, Any]
            try:
                parsed = resp.json()
                body = parsed if isinstance(parsed, dict) else {"raw": parsed}
            except Exception:
                body = {"raw_text": resp.text[:400]}
            if resp.status_code >= 500 or resp.status_code == 429:
                _raise_client_error(
                    code="PROVIDER_HEALTH_RETRYABLE",
                    message=f"provider_http_status={resp.status_code}",
                    retryable=True,
                    attempts=attempt + 1,
                )
            if resp.status_code >= 400:
                _raise_client_error(
                    code="PROVIDER_HEALTH_REJECTED",
                    message=f"provider_request_rejected status={resp.status_code}",
                    retryable=False,
                    attempts=attempt + 1,
                )
            return resp.status_code, body
        except (requests.RequestException, RealProviderClientError) as exc:
            last_exc = exc
            retryable = True
            if isinstance(exc, RealProviderClientError):
                retryable = exc.retryable
            if not retryable:
                break
            if attempt >= retries:
                break
            time.sleep(min(0.5 * (2**attempt), 2.0))
    if isinstance(last_exc, RealProviderClientError):
        raise RealProviderClientError(
            code=last_exc.code,
            message=f"provider_health_failed retries_exhausted error={last_exc.message}",
            retryable=last_exc.retryable,
            attempts=max(1, int(last_exc.attempts or (retries + 1))),
        )
    raise RealProviderClientError(
        code="PROVIDER_HEALTH_FAILED",
        message=f"provider_health_failed retries_exhausted error={last_exc}",
        retryable=True,
        attempts=retries + 1,
    )
