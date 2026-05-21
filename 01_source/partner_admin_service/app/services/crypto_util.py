from __future__ import annotations

import hashlib
import secrets

from app.core.config import get_settings


def hash_secret(raw: str) -> str:
    pepper = get_settings().api_key_pepper
    return hashlib.sha256(f"{pepper}:{raw}".encode("utf-8")).hexdigest()


def generate_partner_api_key(partner_id: str, partner_type: str) -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    prefix_type = "ec" if partner_type.upper() == "ECOMMERCE" else "lg"
    api_key = f"pt_{prefix_type}_{partner_id[:8].lower()}_{token}"
    key_prefix = api_key[:16]
    return api_key, key_prefix, hash_secret(api_key)


def new_id() -> str:
    import uuid

    return str(uuid.uuid4())
