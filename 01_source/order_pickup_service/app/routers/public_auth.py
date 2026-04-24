# 01_source/order_pickup_service/app/routers/public_auth.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.auth_dep import get_current_public_user
from app.core.authorization_policy import AUTHORIZATION_POLICY_MD
from app.core.db import get_db
from app.schemas.public_auth import (
    PublicAuthorizationPolicyOut,
    PublicAuthMeOut,
    PublicAuthRolesOut,
    PublicAuthTokenOut,
    PublicChangePasswordIn,
    PublicChangePasswordOut,
    PublicEmailVerificationConfirmOut,
    PublicEmailVerificationSendOut,
    PublicFiscalProfileIn,
    PublicFiscalProfileOut,
    PublicForgotPasswordIn,
    PublicForgotPasswordOut,
    PublicLoginIn,
    PublicRegisterIn,
    PublicResetPasswordIn,
    PublicResetPasswordOut,
    PublicUserRoleOut,
    PublicUserOut,
)
from app.services.auth_service import (
    AuthServiceError,
    AuthCurrentPasswordMismatchError,
    AuthEmailDeliveryError,
    AuthEmailAlreadyExistsError,
    AuthEmailVerificationTokenError,
    AuthInvalidCredentialsError,
    AuthPasswordResetTokenError,
    AuthWeakPasswordError,
    authenticate_user,
    change_user_password,
    confirm_user_email_verification,
    create_auth_session,
    request_password_reset,
    register_user,
    reset_password_with_token,
    send_email_verification,
    fiscal_profile_completeness,
    update_user_fiscal_profile,
)
from app.services.fiscal_invoice_snapshot_sync_service import (
    sync_billing_invoice_snapshots_after_fiscal_profile,
)
from app.services.user_roles_service import list_active_user_roles

router = APIRouter(prefix="/public/auth", tags=["public-auth"])


def _public_user_payload(user) -> PublicUserOut:
    payload = PublicUserOut.model_validate(user).model_dump()
    payload["fiscal_profile_completeness"] = fiscal_profile_completeness(user)
    return PublicUserOut.model_validate(payload)


@router.get("/authorization-policy", response_model=PublicAuthorizationPolicyOut)
def public_authorization_policy():
    return PublicAuthorizationPolicyOut(
        ok=True,
        title="Politica de autorizacao (fonte unica)",
        markdown=AUTHORIZATION_POLICY_MD.strip(),
    )


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
            user=_public_user_payload(user),
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
            remember_me=bool(payload.remember_me),
        )

        return PublicAuthTokenOut(
            access_token=raw_token,
            user=_public_user_payload(user),
        )

    except AuthInvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.get("/me", response_model=PublicAuthMeOut)
def public_me(current_user=Depends(get_current_public_user)):
    return PublicAuthMeOut(
        authenticated=True,
        user=_public_user_payload(current_user),
    )


@router.put("/me/fiscal-profile", response_model=PublicFiscalProfileOut)
def public_upsert_fiscal_profile(
    payload: PublicFiscalProfileIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_public_user),
):
    try:
        updated_user = update_user_fiscal_profile(
            db,
            user=current_user,
            tax_country=payload.tax_country,
            tax_document_type=payload.tax_document_type,
            tax_document_value=payload.tax_document_value,
            fiscal_email=str(payload.fiscal_email),
            fiscal_phone=payload.fiscal_phone,
            fiscal_address_line1=payload.fiscal_address_line1,
            fiscal_address_line2=payload.fiscal_address_line2,
            fiscal_address_city=payload.fiscal_address_city,
            fiscal_address_state=payload.fiscal_address_state,
            fiscal_address_postal_code=payload.fiscal_address_postal_code,
            fiscal_address_country=payload.fiscal_address_country,
            fiscal_data_consent=payload.fiscal_data_consent,
        )
        sync_summary = sync_billing_invoice_snapshots_after_fiscal_profile(db, user_id=updated_user.id)
        return PublicFiscalProfileOut(
            ok=True,
            user=_public_user_payload(updated_user),
            snapshot_rebuild=sync_summary,
        )
    except AuthServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@router.post("/forgot-password", response_model=PublicForgotPasswordOut)
def public_forgot_password(
    payload: PublicForgotPasswordIn,
    db: Session = Depends(get_db),
):
    try:
        request_password_reset(db, email=payload.email)
        return PublicForgotPasswordOut()
    except AuthEmailDeliveryError:
        # Mesmo comportamento para não expor existência de conta.
        return PublicForgotPasswordOut()


@router.post("/reset-password", response_model=PublicResetPasswordOut)
def public_reset_password(
    payload: PublicResetPasswordIn,
    db: Session = Depends(get_db),
):
    try:
        reset_password_with_token(
            db,
            token=payload.token,
            new_password=payload.new_password,
        )
        return PublicResetPasswordOut(ok=True, message="password_reset_success")
    except AuthPasswordResetTokenError as exc:
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
            user=_public_user_payload(user),
        )
    except AuthEmailVerificationTokenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc