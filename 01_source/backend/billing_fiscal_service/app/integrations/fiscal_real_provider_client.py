from __future__ import annotations

import time
from typing import Any

import requests

from app.core.config import settings


class RealProviderClientError(Exception):
    pass


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


def _request_json_with_retry(*, method: str, url: str, json_payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    retries = max(0, int(settings.fiscal_real_provider_retries))
    timeout = max(1, int(settings.fiscal_real_provider_timeout_sec))
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.request(method=method, url=url, json=json_payload, headers=headers, timeout=timeout)
            if resp.status_code >= 500 or resp.status_code == 429:
                raise RealProviderClientError(f"provider_http_status={resp.status_code} body={resp.text[:400]}")
            if resp.status_code >= 400:
                raise RealProviderClientError(f"provider_request_rejected status={resp.status_code} body={resp.text[:400]}")
            try:
                data = resp.json()
            except Exception as exc:  # noqa: BLE001
                raise RealProviderClientError("provider_invalid_json_response") from exc
            if not isinstance(data, dict):
                raise RealProviderClientError("provider_response_not_object")
            return data
        except (requests.RequestException, RealProviderClientError) as exc:
            last_exc = exc
            if attempt >= retries:
                break
            time.sleep(min(0.5 * (2**attempt), 2.0))
    raise RealProviderClientError(f"provider_request_failed retries_exhausted error={last_exc}")


def issue_invoice(country: str, payload: dict[str, Any]) -> dict[str, Any]:
    base = _provider_base_url(country)
    if not base:
        raise RealProviderClientError(f"provider_base_url_missing country={country}")
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
        raise RealProviderClientError(f"provider_base_url_missing country={country}")
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
        raise RealProviderClientError(f"provider_base_url_missing country={country}")
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
        raise RealProviderClientError(f"provider_base_url_missing country={country}")
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
                raise RealProviderClientError(f"provider_http_status={resp.status_code}")
            if resp.status_code >= 400:
                raise RealProviderClientError(f"provider_request_rejected status={resp.status_code}")
            return resp.status_code, body
        except (requests.RequestException, RealProviderClientError) as exc:
            last_exc = exc
            if attempt >= retries:
                break
            time.sleep(min(0.5 * (2**attempt), 2.0))
    raise RealProviderClientError(f"provider_health_failed retries_exhausted error={last_exc}")
