from __future__ import annotations

from typing import Any


def health_payload() -> dict[str, Any]:
    return {"status": "ok", "service": "partner-service"}
