from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.auth_dep import get_current_public_user, require_user_roles
from app.core.db import Base, get_db
from app.models.user import User
from app.routers.public_auth import router as public_auth_router
from app.services.user_roles_service import list_active_user_roles, user_has_any_role


def _seed_user(db):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    user = User(
        id="user-role-1",
        full_name="User Role",
        email="role.user@example.com",
        phone=None,
        password_hash="x",
        is_active=True,
        email_verified=True,
        phone_verified=False,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _prepare_db():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}",
        future=True,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine, tables=[User.__table__])
    Session = sessionmaker(bind=engine, future=True)
    db = Session()
    db.execute(
        text(
            """
            CREATE TABLE user_roles (
              id TEXT PRIMARY KEY,
              user_id TEXT NOT NULL,
              role TEXT NOT NULL,
              scope_type TEXT NULL,
              scope_id TEXT NULL,
              is_active BOOLEAN NOT NULL,
              granted_at DATETIME NULL,
              revoked_at DATETIME NULL
            )
            """
        )
    )
    db.commit()
    return engine, db, path


def test_user_roles_service_filters_active_roles():
    engine, db, db_path = _prepare_db()
    try:
        user = _seed_user(db)
        db.execute(
            text(
                """
                INSERT INTO user_roles (id, user_id, role, scope_type, scope_id, is_active, granted_at, revoked_at)
                VALUES
                  ('r1', :user_id, 'admin_operacao', 'tenant', 'A', 1, CURRENT_TIMESTAMP, NULL),
                  ('r2', :user_id, 'auditoria', NULL, NULL, 0, CURRENT_TIMESTAMP, NULL),
                  ('r3', :user_id, 'suporte', NULL, NULL, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {"user_id": user.id},
        )
        db.commit()

        roles = list_active_user_roles(db, user_id=user.id)
        assert len(roles) == 1
        assert roles[0]["role"] == "admin_operacao"
        assert user_has_any_role(db, user_id=user.id, allowed_roles={"admin_operacao"}) is True
        assert user_has_any_role(db, user_id=user.id, allowed_roles={"suporte"}) is False
    finally:
        db.close()
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_public_auth_me_roles_endpoint_returns_roles():
    engine, db, db_path = _prepare_db()
    try:
        user = _seed_user(db)
        db.execute(
            text(
                """
                INSERT INTO user_roles (id, user_id, role, scope_type, scope_id, is_active, granted_at, revoked_at)
                VALUES ('r10', :user_id, 'auditoria', 'tenant', 'B', 1, CURRENT_TIMESTAMP, NULL)
                """
            ),
            {"user_id": user.id},
        )
        db.commit()

        app = FastAPI()
        app.include_router(public_auth_router)

        Session = sessionmaker(bind=engine, future=True)

        def override_db():
            local_db = Session()
            try:
                yield local_db
            finally:
                local_db.close()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_public_user] = lambda: type(
            "CurrentUser",
            (),
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "is_active": True,
                "email_verified": True,
                "phone_verified": False,
            },
        )()
        client = TestClient(app)

        response = client.get("/public/auth/me/roles")
        assert response.status_code == 200
        payload = response.json()
        assert payload["user_id"] == user.id
        assert len(payload["roles"]) == 1
        assert payload["roles"][0]["role"] == "auditoria"
    finally:
        db.close()
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_require_user_roles_dependency_blocks_and_allows():
    engine, db, db_path = _prepare_db()
    try:
        user = _seed_user(db)
        Session = sessionmaker(bind=engine, future=True)

        app = FastAPI()

        @app.get("/secure")
        def secure_route(
            _user=Depends(require_user_roles(allowed_roles={"admin_operacao"})),
        ):
            return {"ok": True}

        def override_db():
            local_db = Session()
            try:
                yield local_db
            finally:
                local_db.close()

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_public_user] = lambda: type(
            "CurrentUser",
            (),
            {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "is_active": True,
                "email_verified": True,
                "phone_verified": False,
            },
        )()
        client = TestClient(app)

        denied = client.get("/secure")
        assert denied.status_code == 403

        db.execute(
            text(
                """
                INSERT INTO user_roles (id, user_id, role, scope_type, scope_id, is_active, granted_at, revoked_at)
                VALUES ('r20', :user_id, 'admin_operacao', NULL, NULL, 1, CURRENT_TIMESTAMP, NULL)
                """
            ),
            {"user_id": user.id},
        )
        db.commit()

        allowed = client.get("/secure")
        assert allowed.status_code == 200
        assert allowed.json().get("ok") is True
    finally:
        db.close()
        engine.dispose()
        try:
            os.unlink(db_path)
        except OSError:
            pass
