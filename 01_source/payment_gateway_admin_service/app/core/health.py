from __future__ import annotations


def health_payload() -> dict:
    return {"status": "ok", "service": "payment-gateway-admin"}
