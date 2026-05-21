from __future__ import annotations

import hashlib
import secrets

from app.core.config import get_settings


def hash_secret(raw: str) -> str:
    pepper = get_settings().api_key_pepper
    return hashlib.sha256(f"{pepper}:{raw}".encode("utf-8")).hexdigest()


def generate_api_key(locker_id: str) -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    api_key = f"lk_{locker_id[:8].lower()}_{token}"
    prefix = api_key[:12]
    return api_key, prefix, hash_secret(api_key)
