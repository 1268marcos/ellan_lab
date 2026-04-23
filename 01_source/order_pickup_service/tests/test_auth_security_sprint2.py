from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.core.security import verify_password
from app.models.auth_session import AuthSession
from app.models.user import User
from app.services.auth_service import (
    AuthCurrentPasswordMismatchError,
    AuthPasswordResetTokenError,
    AuthWeakPasswordError,
    change_user_password,
    confirm_user_email_verification,
    create_auth_session,
    create_email_verification_token,
    create_password_reset_token,
    reset_password_with_token,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[User.__table__, AuthSession.__table__])
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _seed_user(db_session):
    from app.core.security import hash_password

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user = User(
        id="user-sprint2",
        full_name="Usuário Teste",
        email="user.sprint2@example.com",
        phone=None,
        password_hash=hash_password("SenhaAtual1"),
        is_active=True,
        email_verified=False,
        phone_verified=False,
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_change_password_requires_current_password(db_session):
    user = _seed_user(db_session)
    with pytest.raises(AuthCurrentPasswordMismatchError):
        change_user_password(
            db_session,
            user=user,
            current_password="SenhaErrada1",
            new_password="NovaSenha2",
        )


def test_change_password_applies_policy_and_updates_hash(db_session):
    user = _seed_user(db_session)
    with pytest.raises(AuthWeakPasswordError):
        change_user_password(
            db_session,
            user=user,
            current_password="SenhaAtual1",
            new_password="fraca",
        )

    updated = change_user_password(
        db_session,
        user=user,
        current_password="SenhaAtual1",
        new_password="NovaSenha2",
    )
    assert verify_password("NovaSenha2", updated.password_hash)
    assert not verify_password("SenhaAtual1", updated.password_hash)


def test_email_verification_token_confirms_user(db_session):
    user = _seed_user(db_session)
    token = create_email_verification_token(user=user)
    assert user.email_verified is False

    confirmed = confirm_user_email_verification(db_session, token=token)
    assert confirmed.email_verified is True


def test_create_auth_session_respects_remember_me_ttl(db_session):
    user = _seed_user(db_session)
    _, short_session = create_auth_session(
        db_session,
        user=user,
        user_agent="pytest",
        ip_address="127.0.0.1",
        remember_me=False,
    )
    _, long_session = create_auth_session(
        db_session,
        user=user,
        user_agent="pytest",
        ip_address="127.0.0.1",
        remember_me=True,
    )
    assert long_session.expires_at > short_session.expires_at


def test_reset_password_with_token_updates_hash(db_session):
    user = _seed_user(db_session)
    token = create_password_reset_token(user=user)
    updated = reset_password_with_token(
        db_session,
        token=token,
        new_password="SenhaNova2",
    )
    assert verify_password("SenhaNova2", updated.password_hash)


def test_reset_password_with_invalid_token_fails(db_session):
    _seed_user(db_session)
    with pytest.raises(AuthPasswordResetTokenError):
        reset_password_with_token(
            db_session,
            token="token-invalido",
            new_password="SenhaNova2",
        )
