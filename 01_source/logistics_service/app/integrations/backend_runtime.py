from __future__ import annotations

from typing import Any

import httpx

from app.core.config import get_settings


def get_locker_status(locker_id: str, client: httpx.Client | None = None) -> dict[str, Any]:
    settings = get_settings()
    url = f"{settings.backend_runtime_base_url.rstrip('/')}/lockers/{locker_id}/status"
    try:
        c = client or httpx.Client(timeout=3.0)
        own = client is None
        try:
            r = c.get(url)
            if r.status_code == 200:
                return {"ok": True, "data": r.json()}
        finally:
            if own:
                c.close()
    except Exception:
        pass
    return {"ok": False, "data": None}
