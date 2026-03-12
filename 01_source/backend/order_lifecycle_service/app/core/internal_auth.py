from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    if not settings.internal_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal token not configured",
        )

    if x_internal_token != settings.internal_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid internal token",
        )