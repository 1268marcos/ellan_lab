# 01_source/order_pickup_service/app/core/auth_dep.py
# Dependências para autenticação unificada baseada em sessão
from __future__ import annotations

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.user import User
from app.services.auth_service import get_user_by_session_token
from app.services.user_roles_service import user_has_any_role


def _extract_bearer_token(authorization: str | None) -> str | None:
    """Extrai token Bearer do header Authorization."""
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "", 1).strip()
    return token or None


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    """
    Obtém o usuário autenticado atual baseado no token de sessão.
    
    Args:
        authorization: Header Authorization com Bearer token
        db: Sessão do banco de dados
        
    Returns:
        User: Usuário autenticado
        
    Raises:
        HTTPException: Se token inválido, ausente ou usuário inativo
    """
    raw_token = _extract_bearer_token(authorization)
    if not raw_token:
        raise HTTPException(
            status_code=401, 
            detail="missing_or_invalid_token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_session_token(db, raw_token=raw_token)
    if not user:
        raise HTTPException(
            status_code=401, 
            detail="invalid_or_expired_session",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=401, 
            detail="user_inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


# Mantido para compatibilidade com código existente, mas recomendamos usar get_current_user
def get_current_public_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    """Alias para get_current_user (mantido por compatibilidade)."""
    return get_current_user(authorization=authorization, db=db)


def get_current_verified_public_user(
    current_user: User = Depends(get_current_public_user),
) -> User:
    """Usuário autenticado com e-mail verificado para ações sensíveis."""
    if not current_user.email_verified:
        raise HTTPException(
            status_code=403,
            detail={
                "type": "EMAIL_NOT_VERIFIED",
                "message": "Confirme seu e-mail para executar esta ação.",
            },
        )
    return current_user


def require_user_roles(
    *,
    allowed_roles: set[str],
    scope_type: str | None = None,
    scope_id: str | None = None,
):
    def _dependency(
        current_user: User = Depends(get_current_public_user),
        db: Session = Depends(get_db),
    ) -> User:
        has_role = user_has_any_role(
            db,
            user_id=current_user.id,
            allowed_roles=allowed_roles,
            scope_type=scope_type,
            scope_id=scope_id,
        )
        if not has_role:
            raise HTTPException(
                status_code=403,
                detail={
                    "type": "ROLE_REQUIRED",
                    "message": "Você não possui permissão de role para acessar este recurso.",
                    "allowed_roles": sorted(allowed_roles),
                },
            )
        return current_user

    return _dependency