from __future__ import annotations

import os
import sys
from pathlib import Path

_SRC_ROOT = Path(__file__).resolve().parents[2]
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ["SEED_ON_START"] = "false"
os.environ["WEBHOOK_DISPATCH_ENABLED"] = "true"

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
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
