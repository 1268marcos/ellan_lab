from __future__ import annotations

import hashlib
import secrets
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


def hash_secret(value: str, pepper: str = "") -> str:
    return hashlib.sha256(f"{pepper}{value}".encode()).hexdigest()


def generate_api_key(prefix: str = "cap") -> tuple[str, str]:
    raw = f"{prefix}_{secrets.token_urlsafe(32)}"
    return raw[:16], raw
