# 01_source/order_pickup/service/app/service/auth_service.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.security import (
    generate_session_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.auth_session import AuthSession
from app.models.user import User


SESSION_TTL_HOURS = 24


class AuthServiceError(Exception):
    pass


class AuthInvalidCredentialsError(AuthServiceError):
    pass


class AuthEmailAlreadyExistsError(AuthServiceError):
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

def authenticate_user(db: Session, *, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email.lower().strip()).first()
    if not user:
        raise AuthInvalidCredentialsError("invalid_credentials")

    if not verify_password(password, user.password_hash):
        raise AuthInvalidCredentialsError("invalid_credentials")

    if not user.is_active:
        raise AuthInvalidCredentialsError("inactive_user")
    
    user.updated_at = utc_now_naive()
    db.commit()

    return user


def create_auth_session(
    db: Session,
    *,
    user: User,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[str, AuthSession]:
    raw_token = generate_session_token()
    token_hash = hash_token(raw_token)
    now = utc_now_naive()

    session = AuthSession(
        user_id=user.id,
        session_token_hash=token_hash,
        user_agent=user_agent,
        ip_address=ip_address,
        created_at=now,
        expires_at=now + timedelta(hours=SESSION_TTL_HOURS),
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