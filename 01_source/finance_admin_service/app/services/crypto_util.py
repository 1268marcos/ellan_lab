from __future__ import annotations

import hashlib
import secrets
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def hash_secret(raw: str, pepper: str = "") -> str:
    payload = f"{pepper}:{raw}".encode()
    return hashlib.sha256(payload).hexdigest()


def generate_partner_api_key(partner_code: str) -> tuple[str, str, str]:
    """Returns (full_key, prefix, hash)."""
    token = secrets.token_urlsafe(32)
    full = f"fin_{partner_code}_{token}"
    prefix = full[:16]
    return full, prefix, hash_secret(full)
