# Segurança do token (QR) - token opaco + hash
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import jwt
import os

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PROD")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_ACCESS_TTL_MIN = int(os.getenv("JWT_ACCESS_TTL_MIN", "60"))

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
    # 6 dígitos, criptograficamente seguro
    return f"{secrets.randbelow(1_000_000):06d}"

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()