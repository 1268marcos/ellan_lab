# 01_source/order_pickup_service/app/core/auth_dev.py
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.services.auth_service import get_user_by_session_token


class DevUser:
    def __init__(self, user_id: str):
        self.id = str(user_id)


def _extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "", 1).strip()
    return token or None


def _is_explicit_dev_bypass(request: Request) -> bool:
    """
    O bypass DEV só pode acontecer quando explicitamente solicitado.
    Isso evita que pedidos ONLINE públicos sejam gravados como dev_user_1
    por ausência de Authorization.
    """
    header_value = (request.headers.get("X-Dev-Bypass-Auth") or "").strip().lower()
    if header_value in {"1", "true", "yes", "on"}:
        return True

    query_value = (request.query_params.get("dev_bypass_auth") or "").strip().lower()
    if query_value in {"1", "true", "yes", "on"}:
        return True

    return False


def get_current_user_or_dev(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Ordem de resolução:
    1. Bearer token público válido -> usuário autenticado por sessão
    2. DEV_BYPASS_AUTH=true + bypass explícito -> usuário fake de desenvolvimento
    3. caso contrário -> 401

    Regra importante:
    - token inválido NÃO cai para dev automaticamente
    - ausência de token NÃO cai para dev automaticamente
    """
    authorization = request.headers.get("authorization")
    raw_token = _extract_bearer_token(authorization)

    if raw_token:
      user = get_user_by_session_token(db, raw_token=raw_token)
      if user:
          return user

      raise HTTPException(
          status_code=401,
          detail="invalid_or_expired_token",
          headers={"WWW-Authenticate": "Bearer"},
      )

    if settings.dev_bypass_auth and _is_explicit_dev_bypass(request):
        return DevUser(user_id=settings.dev_user_id)

    raise HTTPException(
        status_code=401,
        detail="unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )