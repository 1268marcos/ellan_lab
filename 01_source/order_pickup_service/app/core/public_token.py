# 01_source/order_pickup_service/app/core/public_token.py
import secrets
import hashlib


def generate_public_token() -> str:
    return secrets.token_urlsafe(32)


def hash_public_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
    