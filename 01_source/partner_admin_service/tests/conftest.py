from __future__ import annotations

import os

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
    # Garante que todos os modelos estejam registrados no metadata antes do create_all.
    from app.models import api_key as _api_key  # noqa: F401
    from app.models import contact as _contact  # noqa: F401
    from app.models import partner as _partner  # noqa: F401
    from app.models import user as _user  # noqa: F401
    from app.models import tenant as _tenant  # noqa: F401
    from app.models import webhook as _webhook  # noqa: F401
    from app.models import partner_domain as _partner_domain  # noqa: F401
    from app.models import partner_extended as _partner_extended  # noqa: F401
    from app.models import partner_ecosystem as _partner_ecosystem  # noqa: F401
    from app.models import partner_ecosystem_professional as _partner_ecosystem_pro  # noqa: F401
    from app.models import partner_capability_webhook as _partner_cap_wh  # noqa: F401
    from app.models import partner_global_ops as _partner_global_ops  # noqa: F401
    from app.models import security as _security  # noqa: F401  # segments, relations, integrations

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
