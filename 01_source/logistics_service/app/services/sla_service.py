from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


def fetch_compliance(client: httpx.Client | None = None) -> dict[str, Any]:
    settings = get_settings()
    url = f"{settings.order_lifecycle_base_url.rstrip('/')}/sla/compliance"
    default: dict[str, Any] = {"ok": False, "compliance_pct": 0.0, "deadlines": []}
    try:
        c = client or httpx.Client(timeout=3.0)
        own = client is None
        try:
            r = c.get(url)
            if r.status_code != 200:
                return default
            body = r.json()
            if not isinstance(body, dict):
                return default
            return {"ok": True, **body}
        finally:
            if own:
                c.close()
    except Exception:
        return default
