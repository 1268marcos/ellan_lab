# 01_source/order_pickup_service/app/core/security.py
# Segurança do token (QR) - token opaco + hash
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import jwt

from app.core.config import settings

# Compatibilidade retroativa para módulos legados que ainda importam constantes
JWT_SECRET = settings.jwt_secret
JWT_ALG = settings.jwt_alg
JWT_ACCESS_TTL_MIN = settings.jwt_access_ttl_min


def create_access_token(subject: str, extra: Optional[Dict[str, Any]] = None) -> str:
    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_ACCESS_TTL_MIN)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def generate_otp_6() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()