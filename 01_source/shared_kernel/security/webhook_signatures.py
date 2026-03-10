import hashlib
import hmac


def verify_hmac_sha256(payload: bytes, secret: str, received_signature: str) -> bool:
    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(digest, received_signature)
