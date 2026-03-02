# order_pickup_service/app/core/health/exceptions.py
from __future__ import annotations

from typing import Any, Dict, Optional


class HealthCheckError(RuntimeError):
    """
    Exceção de healthcheck com payload rico (JSON) para ser retornado pelo router/handler.
    """

    def __init__(
        self,
        name: str,
        *,
        status: str,
        details: Dict[str, Any],
        elapsed_ms: int,
        http_status_code: int = 503,
        message: Optional[str] = None,
    ) -> None:
        self.name = name
        self.status = status
        self.details = details
        self.elapsed_ms = elapsed_ms
        self.http_status_code = http_status_code

        payload = {
            "ok": False,
            "check": name,
            "status": status,
            "elapsed_ms": elapsed_ms,
            "details": details,
        }
        self.payload = payload
        super().__init__(message or f"Health check failed: {name} ({status})")