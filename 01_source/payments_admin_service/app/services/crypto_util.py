from __future__ import annotations

import hashlib
import secrets
import uuid

from app.core.config import get_settings


def hash_secret(raw: str) -> str:
    pepper = get_settings().api_key_pepper
    return hashlib.sha256(f"{pepper}:{raw}".encode("utf-8")).hexdigest()


def generate_webhook_secret(partner_id: str) -> tuple[str, str]:
    token = secrets.token_urlsafe(24)
    secret = f"whsec_{partner_id[:8].lower()}_{token}"
    return secret, hash_secret(secret)


def new_id() -> str:
    return str(uuid.uuid4())
