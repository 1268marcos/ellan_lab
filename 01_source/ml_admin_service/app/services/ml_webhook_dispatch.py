from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

import httpx

from app.core.config import get_settings

DEFAULT_TIMEOUT = 8.0


def dispatch_webhook(url: str, event_type: str, payload: dict[str, Any], *, secret: str | None = None) -> tuple[bool, int | None, str | None]:
    if not get_settings().webhook_dispatch_enabled:
        return True, 202, "dispatch_disabled_simulated"
    body = json.dumps({"event": event_type, "data": payload}, default=str).encode("utf-8")
    headers = {"Content-Type": "application/json", "X-Ellan-Event": event_type}
    if secret:
        sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers["X-Ellan-Signature"] = sig
    try:
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            resp = client.post(url, content=body, headers=headers)
        snippet = (resp.text or "")[:500]
        return 200 <= resp.status_code < 300, resp.status_code, snippet
    except httpx.HTTPError as exc:
        return False, None, str(exc)[:500]
