from __future__ import annotations


def health_payload() -> dict[str, str]:
    return {"status": "ok", "service": "privacy-compliance-admin-service"}
