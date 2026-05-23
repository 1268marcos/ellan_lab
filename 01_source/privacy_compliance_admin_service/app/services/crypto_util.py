from __future__ import annotations

import hashlib
import json
import secrets
import uuid
from datetime import datetime, timezone

from app.core.config import get_settings


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_secret(raw: str) -> str:
    pepper = get_settings().api_key_pepper
    return hashlib.sha256(f"{pepper}:{raw}".encode("utf-8")).hexdigest()


def generate_privacy_api_key(regulation_code: str) -> tuple[str, str, str]:
    token = secrets.token_urlsafe(32)
    code = regulation_code.lower()
    api_key = f"pc_{code}_{token}"
    key_prefix = api_key[:16]
    return api_key, key_prefix, hash_secret(api_key)


def parse_events_json(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
