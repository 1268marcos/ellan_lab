from __future__ import annotations

import hashlib
import secrets
import uuid

from app.core.config import get_settings


def hash_secret(raw: str) -> str:
    pepper = get_settings().api_key_pepper
    return hashlib.sha256(f"{pepper}:{raw}".encode("utf-8")).hexdigest()


def generate_issuer_api_key(issuer_id: str, issuer_code: str) -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    api_key = f"fc_{issuer_code.lower()[:12]}_{issuer_id[:8].lower()}_{token}"
    key_prefix = api_key[:16]
    return api_key, key_prefix, hash_secret(api_key)


def new_id() -> str:
    return str(uuid.uuid4())
