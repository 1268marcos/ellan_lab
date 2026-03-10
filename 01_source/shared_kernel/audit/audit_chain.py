import hashlib


def chain_hash(previous_hash: str, payload: str) -> str:
    raw = f"{previous_hash}|{payload}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()
