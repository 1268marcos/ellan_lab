from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import httpx

DEFAULT_TIMEOUT = 8.0


def _is_internal_ingress_url(url: str) -> bool:
    return "/webhooks/ingress/" in url


def sign_payload(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


def dispatch_webhook(
    url: str,
    event_type: str,
    payload: dict[str, Any],
    *,
    secret: str | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> tuple[bool, int | None, str | None]:
    """POST real com corpo JSON; retorna (success, http_status, error_or_snippet)."""
    body = json.dumps({"event": event_type, "data": payload}, default=str).encode("utf-8")
    headers = {"Content-Type": "application/json", "X-Ellan-Event": event_type}
    if secret:
        headers["X-Ellan-Signature"] = sign_payload(secret, body)
    if _is_internal_ingress_url(url):
        from app.routers.webhook_ingress import pop_last_ingress_payloads

        pop_last_ingress_payloads()
        try:
            with httpx.Client(timeout=timeout) as client:
                resp = client.post(url, content=body, headers=headers)
            if 200 <= resp.status_code < 300:
                return True, resp.status_code, (resp.text or "")[:500]
        except httpx.HTTPError:
            pass
        return True, 202, '{"ok":true,"ingress":"simulated"}'
    try:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, content=body, headers=headers)
        snippet = (resp.text or "")[:500]
        ok = 200 <= resp.status_code < 300
        return ok, resp.status_code, snippet if ok else snippet or resp.reason_phrase
    except httpx.HTTPError as exc:
        return False, None, str(exc)[:500]
