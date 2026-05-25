from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["SEED_ON_START"] = "false"

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def clear_settings():
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client():
    from app.core.config import get_settings
    from app.core.database import Base, engine
    from app.main import app

    get_settings.cache_clear()
    from app.models import critical_table_security as _critical_table_security  # noqa: F401
    from app.models import privacy as _privacy  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    from app.services.critical_table_security_service import seed_registry_and_policies
    from app.core.database import SessionLocal

    db = SessionLocal()
    try:
        seed_registry_and_policies(db)
    except Exception:
        db.rollback()
    finally:
        db.close()
    with TestClient(app) as c:
        yield c
