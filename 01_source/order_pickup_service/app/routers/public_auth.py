# 01_source/order_pickup_service/app/routers/public_auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user
from app.core.db import get_db
from app.schemas.public_auth import (
    PublicAuthMeOut,
    PublicAuthRolesOut,
    PublicAuthTokenOut,
    PublicChangePasswordIn,
    PublicChangePasswordOut,
    PublicEmailVerificationConfirmOut,
    PublicEmailVerificationSendOut,
    PublicLoginIn,
    PublicRegisterIn,
    PublicUserRoleOut,
    PublicUserOut,
)
from app.services.auth_service import (
    AuthCurrentPasswordMismatchError,
    AuthEmailDeliveryError,
    AuthEmailAlreadyExistsError,
    AuthEmailVerificationTokenError,
    AuthInvalidCredentialsError,
    AuthWeakPasswordError,
    authenticate_user,
    change_user_password,
    confirm_user_email_verification,
    create_auth_session,
    register_user,
    send_email_verification,
)
from app.services.user_roles_service import list_active_user_roles

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


@router.get("/me/roles", response_model=PublicAuthRolesOut)
def public_me_roles(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_public_user),
):
    roles = list_active_user_roles(db, user_id=current_user.id)
    items = [PublicUserRoleOut.model_validate(item) for item in roles]
    return PublicAuthRolesOut(user_id=current_user.id, roles=items)


@router.post("/change-password", response_model=PublicChangePasswordOut)
def public_change_password(
    payload: PublicChangePasswordIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_public_user),
):
    try:
        change_user_password(
            db,
            user=current_user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
        return PublicChangePasswordOut(ok=True, message="password_updated")
    except AuthCurrentPasswordMismatchError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AuthWeakPasswordError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/email-verification/resend", response_model=PublicEmailVerificationSendOut)
def public_resend_email_verification(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_public_user),
):
    try:
        result = send_email_verification(db, user=current_user)
        return PublicEmailVerificationSendOut(
            ok=True,
            already_verified=bool(result.get("already_verified")),
            delivery=str(result.get("delivery") or "unknown"),
            verification_link=result.get("verification_link"),
        )
    except AuthEmailDeliveryError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/email-verification/confirm", response_model=PublicEmailVerificationConfirmOut)
def public_confirm_email_verification(
    token: str = Query(..., min_length=16),
    db: Session = Depends(get_db),
):
    try:
        user = confirm_user_email_verification(db, token=token)
        return PublicEmailVerificationConfirmOut(
            ok=True,
            message="email_verified",
            user=PublicUserOut.model_validate(user),
        )
    except AuthEmailVerificationTokenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc