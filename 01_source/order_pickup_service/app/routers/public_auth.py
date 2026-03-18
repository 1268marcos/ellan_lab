# 01_source/order_pickup_service/app/routers/public_auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user
from app.core.db import get_db
from app.schemas.public_auth import (
    PublicAuthMeOut,
    PublicAuthTokenOut,
    PublicLoginIn,
    PublicRegisterIn,
    PublicUserOut,
)
from app.services.auth_service import (
    AuthEmailAlreadyExistsError,
    AuthInvalidCredentialsError,
    authenticate_user,
    create_auth_session,
    register_user,
)

router = APIRouter(prefix="/public/auth", tags=["public-auth"])


@router.post("/register", response_model=PublicAuthTokenOut)
def public_register(
    payload: PublicRegisterIn,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db,
            full_name=payload.full_name,
            email=payload.email,
            phone=payload.phone,
            password=payload.password,
        )

        raw_token, _session = create_auth_session(
            db,
            user=user,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )

        return PublicAuthTokenOut(
            access_token=raw_token,
            user=PublicUserOut.model_validate(user),
        )

    except AuthEmailAlreadyExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/login", response_model=PublicAuthTokenOut)
def public_login(
    payload: PublicLoginIn,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(
            db,
            email=payload.email,
            password=payload.password,
        )

        raw_token, _session = create_auth_session(
            db,
            user=user,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host if request.client else None,
        )

        return PublicAuthTokenOut(
            access_token=raw_token,
            user=PublicUserOut.model_validate(user),
        )

    except AuthInvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=PublicAuthMeOut)
def public_me(current_user=Depends(get_current_public_user)):
    return PublicAuthMeOut(
        authenticated=True,
        user=PublicUserOut.model_validate(current_user),
    )