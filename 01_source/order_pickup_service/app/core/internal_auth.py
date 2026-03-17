# 01_source/order_pickup_service/app/core/internal_auth.py
# Dependência de header interno (2:A)
from fastapi import Header, HTTPException

from app.core.config import settings


def require_internal_token(x_internal_token: str = Header(default="", alias="X-Internal-Token")):
    if not settings.internal_token:
        raise HTTPException(status_code=500, detail="INTERNAL_TOKEN not configured")
    if x_internal_token != settings.internal_token:
        raise HTTPException(status_code=401, detail="Invalid internal token")
    return True