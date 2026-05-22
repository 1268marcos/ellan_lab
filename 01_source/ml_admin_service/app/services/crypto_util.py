from __future__ import annotations

import hashlib
import secrets
import uuid

from app.core.config import get_settings


def hash_secret(raw: str) -> str:
    pepper = get_settings().api_key_pepper
    return hashlib.sha256(f"{pepper}:{raw}".encode("utf-8")).hexdigest()


def generate_ml_api_key(partner_id: str, partner_code: str) -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    api_key = f"ml_{partner_code.lower()[:12]}_{partner_id[:8].lower()}_{token}"
    key_prefix = api_key[:16]
    return api_key, key_prefix, hash_secret(api_key)


def new_id() -> str:
    return str(uuid.uuid4())
