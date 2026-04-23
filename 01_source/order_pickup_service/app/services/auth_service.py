# 01_source/order_pickup/service/app/service/auth_service.py

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from jose import JWTError, jwt

from sqlalchemy.orm import Session

from app.core.security import (
    generate_session_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.core.config import settings
from app.models.auth_session import AuthSession
from app.models.user import User
from app.services.email_notification_service import EmailNotificationError, send_email


SESSION_TTL_HOURS = 24
SESSION_TTL_REMEMBER_DAYS = 30
EMAIL_VERIFICATION_TTL_MIN = 60 * 24
PASSWORD_RESET_TTL_MIN = 30
PASSWORD_MIN_LENGTH = 8
logger = logging.getLogger(__name__)


class AuthServiceError(Exception):
    pass


class AuthInvalidCredentialsError(AuthServiceError):
    pass


class AuthEmailAlreadyExistsError(AuthServiceError):
    pass


class AuthWeakPasswordError(AuthServiceError):
    pass


class AuthCurrentPasswordMismatchError(AuthServiceError):
    pass


class AuthEmailVerificationTokenError(AuthServiceError):
    pass


class AuthEmailDeliveryError(AuthServiceError):
    pass


class AuthPasswordResetTokenError(AuthServiceError):
    pass


def utc_now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def register_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    phone: str | None,
    password: str,
) -> User:
    existing = db.query(User).filter(User.email == email.lower().strip()).first()
    if existing:
        raise AuthEmailAlreadyExistsError("email_already_exists")

    now = utc_now_naive()

    user = User(
        full_name=full_name.strip(),
        email=email.lower().strip(),
        phone=normalize_phone(phone),
        password_hash=hash_password(password),
        is_active=True,
        email_verified=False,
        phone_verified=False,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    return phone.replace(" ", "").replace("-", "")


def validate_password_policy(password: str) -> None:
    if len(password or "") < PASSWORD_MIN_LENGTH:
        raise AuthWeakPasswordError("password_too_short")
    if not any(ch.isupper() for ch in password):
        raise AuthWeakPasswordError("password_missing_uppercase")
    if not any(ch.islower() for ch in password):
        raise AuthWeakPasswordError("password_missing_lowercase")
    if not any(ch.isdigit() for ch in password):
        raise AuthWeakPasswordError("password_missing_digit")

def authenticate_user(db: Session, *, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        raise AuthInvalidCredentialsError("invalid_credentials")

    try:
        password_ok = verify_password(password, user.password_hash)
    except Exception:
        logger.exception(
            "verify_password_failed",
            extra={"user_id": getattr(user, "id", None), "email": email.lower().strip()},
        )
        raise AuthInvalidCredentialsError("invalid_credentials")

    if not password_ok:
        raise AuthInvalidCredentialsError("invalid_credentials")

    if not user.is_active:
        raise AuthInvalidCredentialsError("inactive_user")
    
    user.updated_at = utc_now_naive()
    db.commit()

    return user


def change_user_password(
    db: Session,
    *,
    user: User,
    current_password: str,
    new_password: str,
) -> User:
    if not verify_password(current_password, user.password_hash):
        raise AuthCurrentPasswordMismatchError("current_password_invalid")
    validate_password_policy(new_password)
    if verify_password(new_password, user.password_hash):
        raise AuthWeakPasswordError("new_password_must_be_different")

    user.password_hash = hash_password(new_password)
    user.updated_at = utc_now_naive()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _build_email_verification_html(*, full_name: str, verification_link: str) -> str:
    safe_name = (full_name or "").strip() or "usuário"
    return f"""
    <div style="font-family: Arial, sans-serif; line-height:1.55; color:#111;">
      <h2>Confirme seu e-mail</h2>
      <p>Olá, {safe_name}.</p>
      <p>Para concluir a segurança da sua conta, confirme seu endereço de e-mail clicando no botão abaixo:</p>
      <p style="margin:20px 0;">
        <a href="{verification_link}" style="background:#2563eb;color:#fff;padding:12px 16px;border-radius:8px;text-decoration:none;font-weight:700;">
          Confirmar e-mail
        </a>
      </p>
      <p>Se o botão não funcionar, copie e cole este link no navegador:</p>
      <p><a href="{verification_link}">{verification_link}</a></p>
      <hr/>
      <small>Este link expira em 24 horas.</small>
    </div>
    """


def _build_password_reset_html(*, full_name: str, reset_link: str) -> str:
    safe_name = (full_name or "").strip() or "usuário"
    return f"""
    <div style="font-family: Arial, sans-serif; line-height:1.55; color:#111;">
      <h2>Redefinição de senha</h2>
      <p>Olá, {safe_name}.</p>
      <p>Recebemos uma solicitação para redefinir sua senha.</p>
      <p style="margin:20px 0;">
        <a href="{reset_link}" style="background:#0f172a;color:#fff;padding:12px 16px;border-radius:8px;text-decoration:none;font-weight:700;">
          Redefinir senha
        </a>
      </p>
      <p>Se você não solicitou, ignore este e-mail.</p>
      <p>Se o botão não funcionar, use este link:</p>
      <p><a href="{reset_link}">{reset_link}</a></p>
      <hr/>
      <small>Este link expira em 30 minutos.</small>
    </div>
    """


def create_email_verification_token(*, user: User, ttl_min: int = EMAIL_VERIFICATION_TTL_MIN) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": str(user.email).lower().strip(),
        "purpose": "email_verification",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_min)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_password_reset_token(*, user: User, ttl_min: int = PASSWORD_RESET_TTL_MIN) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user.id),
        "email": str(user.email).lower().strip(),
        "purpose": "password_reset",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ttl_min)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_email_verification_token(*, token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError as exc:
        raise AuthEmailVerificationTokenError("email_verification_token_invalid_or_expired") from exc

    if payload.get("purpose") != "email_verification":
        raise AuthEmailVerificationTokenError("email_verification_token_invalid_purpose")
    if not payload.get("sub") or not payload.get("email"):
        raise AuthEmailVerificationTokenError("email_verification_token_invalid_payload")
    return payload


def decode_password_reset_token(*, token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError as exc:
        raise AuthPasswordResetTokenError("password_reset_token_invalid_or_expired") from exc

    if payload.get("purpose") != "password_reset":
        raise AuthPasswordResetTokenError("password_reset_token_invalid_purpose")
    if not payload.get("sub") or not payload.get("email"):
        raise AuthPasswordResetTokenError("password_reset_token_invalid_payload")
    return payload


def send_email_verification(
    db: Session,
    *,
    user: User,
    frontend_base_url: str | None = None,
) -> dict:
    token = create_email_verification_token(user=user)
    base = (frontend_base_url or settings.frontend_base_url or "").rstrip("/")
    if not base:
        raise AuthEmailDeliveryError("frontend_base_url_not_configured")

    query = urlencode({"token": token})
    verification_link = f"{base}/verificar-email?{query}"

    if user.email_verified:
        return {
            "already_verified": True,
            "delivery": "not_sent_already_verified",
            "verification_link": None,
        }

    if not settings.email_enabled:
        return {
            "already_verified": False,
            "delivery": "disabled_preview_only",
            "verification_link": verification_link,
        }

    try:
        send_email(
            to_email=user.email,
            subject="Confirme seu e-mail",
            html=_build_email_verification_html(
                full_name=user.full_name,
                verification_link=verification_link,
            ),
        )
    except EmailNotificationError as exc:
        raise AuthEmailDeliveryError(str(exc)) from exc

    user.updated_at = utc_now_naive()
    db.add(user)
    db.commit()

    return {
        "already_verified": False,
        "delivery": "sent",
        "verification_link": None,
    }


def confirm_user_email_verification(db: Session, *, token: str) -> User:
    payload = decode_email_verification_token(token=token)
    user_id = str(payload["sub"])
    token_email = str(payload["email"]).lower().strip()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthEmailVerificationTokenError("email_verification_user_not_found")
    if str(user.email).lower().strip() != token_email:
        raise AuthEmailVerificationTokenError("email_verification_email_mismatch")

    if not user.email_verified:
        user.email_verified = True
        user.updated_at = utc_now_naive()
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def request_password_reset(
    db: Session,
    *,
    email: str,
    frontend_base_url: str | None = None,
) -> dict:
    normalized_email = str(email or "").lower().strip()
    user = db.query(User).filter(User.email == normalized_email).first()
    base = (frontend_base_url or settings.frontend_base_url or "").rstrip("/")
    if not base:
        logger.warning("password_reset_frontend_base_url_missing")
        return {"accepted": True}

    if not user:
        # Resposta indistinguível para evitar enumeração de usuário.
        return {"accepted": True}

    reset_token = create_password_reset_token(user=user)
    reset_link = f"{base}/recuperar-senha?token={urlencode({'token': reset_token})[6:]}"

    if not settings.email_enabled:
        logger.info("password_reset_email_disabled_preview_link=%s", reset_link)
        return {"accepted": True}

    try:
        send_email(
            to_email=user.email,
            subject="Redefinir senha da sua conta",
            html=_build_password_reset_html(full_name=user.full_name, reset_link=reset_link),
        )
    except EmailNotificationError as exc:
        logger.exception("password_reset_email_failed")
        raise AuthEmailDeliveryError(str(exc)) from exc

    return {"accepted": True}


def reset_password_with_token(
    db: Session,
    *,
    token: str,
    new_password: str,
) -> User:
    payload = decode_password_reset_token(token=token)
    user_id = str(payload["sub"])
    token_email = str(payload["email"]).lower().strip()

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise AuthPasswordResetTokenError("password_reset_user_not_found")
    if str(user.email).lower().strip() != token_email:
        raise AuthPasswordResetTokenError("password_reset_email_mismatch")

    validate_password_policy(new_password)
    if verify_password(new_password, user.password_hash):
        raise AuthWeakPasswordError("new_password_must_be_different")

    user.password_hash = hash_password(new_password)
    user.updated_at = utc_now_naive()
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_auth_session(
    db: Session,
    *,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
    remember_me: bool = False,
) -> tuple[str, AuthSession]:
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    now = utc_now_naive()

    expires_delta = timedelta(days=SESSION_TTL_REMEMBER_DAYS) if remember_me else timedelta(hours=SESSION_TTL_HOURS)
    session = AuthSession(
        user_id=user.id,
        session_token_hash=token_hash,
        user_agent=user_agent,
        ip_address=ip_address,
        created_at=now,
        expires_at=now + expires_delta,
        revoked_at=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return raw_token, session


def get_user_by_session_token(db: Session, *, raw_token: str) -> User | None:
    token_hash = hash_token(raw_token)
    now = utc_now_naive()

    session = (
        db.query(AuthSession)
        .filter(AuthSession.session_token_hash == token_hash)
        .filter(AuthSession.revoked_at.is_(None))
        .filter(AuthSession.expires_at > now)
        .first()
        # ABAIXO NAO FUNCIONOU : Limite de 1 sessão ativa por usuário - comportamento tipo apps modernos
        # db.query(AuthSession).filter(
        #     AuthSession.user_id == user.id
        # ).filter(
        #     AuthSession.revoked_at.is_(None)
        # ).update({
        #     AuthSession.revoked_at: utc_now_naive()
        # })
    )
    if not session:
        return None

    # user = db.query(User).filter(User.id == session.user_id).first()
    # if not user or not user.is_active:
    #     return None

    user = (
        db.query(User)
        .filter(User.id == session.user_id)
        .filter(User.is_active == True)
        .first()
    )
    if not user:
        return None

    return user