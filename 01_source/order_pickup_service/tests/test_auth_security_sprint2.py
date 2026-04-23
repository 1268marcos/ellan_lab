from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.core.security import verify_password
from app.models.user import User
from app.services.auth_service import (
    AuthCurrentPasswordMismatchError,
    AuthWeakPasswordError,
    change_user_password,
    confirm_user_email_verification,
    create_email_verification_token,
)


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
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
