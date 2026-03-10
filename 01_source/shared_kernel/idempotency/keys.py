import hashlib


def build_idempotency_fingerprint(*parts: str) -> str:
    normalized = "|".join((p or "").strip() for p in parts)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
