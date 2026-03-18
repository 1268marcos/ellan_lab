# 01_source/order_pickup_service/app/core/auth_dev.py
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.services.auth_service import get_user_by_session_token


class DevUser:
    def __init__(self, user_id: str):
        self.id = user_id


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "", 1).strip()
    return token or None


def get_current_user_or_dev(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Ordem de resolução:
    1. Bearer token público -> usuário autenticado por sessão
    2. DEV_BYPASS_AUTH=true -> usuário fake de desenvolvimento
    3. fallback -> 401
    """
    authorization = request.headers.get("authorization")
    raw_token = _extract_bearer_token(authorization)

    if raw_token:
        user = get_user_by_session_token(db, raw_token=raw_token)
        if user:
            return user

    if settings.dev_bypass_auth:
        return DevUser(user_id=settings.dev_user_id)

    raise HTTPException(
        status_code=401,
        detail="unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )