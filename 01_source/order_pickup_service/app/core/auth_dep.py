# 01_source/order_pickup_service/app/core/auth_dep.py
# Dependência para pegar usuário autenticado
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_session_token


bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")

    token = creds.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "", 1).strip()
    return token or None


def get_current_public_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    raw_token = _extract_bearer_token(authorization)
    if not raw_token:
        raise HTTPException(status_code=401, detail="missing_or_invalid_token")

    user = get_user_by_session_token(db, raw_token=raw_token)
    if not user:
        raise HTTPException(status_code=401, detail="invalid_or_expired_session")

    return user