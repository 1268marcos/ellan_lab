# order_pickup_service/app/core/health/pickup.py
from __future__ import annotations

import time
from typing import Any, Dict

from app.core.config import settings
from app.core.security import generate_otp_6, hash_otp

from app.core.health.exceptions import HealthCheckError


def check_pickup() -> Dict[str, Any]:
    started = time.perf_counter()
    details: Dict[str, Any] = {
        "config": {
            "pickup_window_sec": int(getattr(settings, "pickup_window_sec", 0)),
            "pickup_token_ttl_sec": int(getattr(settings, "pickup_token_ttl_sec", 0)),
        },
        "token": {},
    }

    try:
        win = details["config"]["pickup_window_sec"]
        ttl = details["config"]["pickup_token_ttl_sec"]

        config_ok = True
        config_errors = []

        if win < 300:
            config_ok = False
            config_errors.append("pickup_window_too_small")
        if not (60 <= ttl <= 3600):
            config_ok = False
            config_errors.append("pickup_token_ttl_out_of_range")

        details["config"]["ok"] = config_ok
        if config_errors:
            details["config"]["errors"] = config_errors

        otp = generate_otp_6()
        h = hash_otp(otp)
        token_ok = bool(otp) and len(otp) == 6 and bool(h) and len(h) >= 32

        details["token"] = {
            "ok": token_ok,
            "otp_len": len(otp),
            "hash_len": len(h),
        }

        ok = config_ok and token_ok
        elapsed_ms = int((time.perf_counter() - started) * 1000)

        if not ok:
            raise HealthCheckError(
                "pickup",
                status="degraded",
                details=details,
                elapsed_ms=elapsed_ms,
                http_status_code=503,
            )

        return {"ok": True, "check": "pickup", "status": "ok", "elapsed_ms": elapsed_ms, "details": details}

    except HealthCheckError:
        raise
    except Exception as e:
        details["error"] = {"type": e.__class__.__name__, "message": str(e)}
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        raise HealthCheckError(
            "pickup",
            status="error",
            details=details,
            elapsed_ms=elapsed_ms,
            http_status_code=503,
        )