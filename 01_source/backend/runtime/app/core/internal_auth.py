# 01_source/backend/runtime/app/core/internal_auth.py
from fastapi import Header, HTTPException
from app.core.config import settings


def require_internal_token(x_internal_token: str | None = Header(default=None)):
    if settings.internal_token and x_internal_token != settings.internal_token:
        raise HTTPException(
            status_code=401,
            detail={
                "type": "UNAUTHORIZED",
                "message": "invalid internal token",
                "retryable": False,
            },
        )