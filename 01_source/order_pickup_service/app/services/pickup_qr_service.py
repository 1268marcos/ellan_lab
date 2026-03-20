# 01_source/order_pickup_service/app/services/pickup_qr_service.py
from __future__ import annotations

import base64
import hashlib
import hmac
import json

from app.core.config import settings


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _sign(payload_bytes: bytes) -> str:
    secret = settings.jwt_secret.encode("utf-8")
    digest = hmac.new(secret, payload_bytes, hashlib.sha256).digest()
    return _b64url(digest)


def build_public_pickup_qr_value(
    *,
    order_id: str,
    token_id: str,
    expires_at_iso: str | None,
) -> str:
    payload = {
        "kind": "pickup_qr",
        "order_id": order_id,
        "token_id": token_id,
        "expires_at": expires_at_iso,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = _sign(payload_bytes)
    return f"{_b64url(payload_bytes)}.{sig}"