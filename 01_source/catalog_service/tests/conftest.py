import os
import tempfile

_fd, _DB_PATH = tempfile.mkstemp(suffix="catalog_api_test.db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_DB_PATH}"

import fakeredis
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from events import publishers
from main import app
from models import Category, PartnerProductRule


@pytest.fixture(scope="session", autouse=True)
def _fake_redis():
    r = fakeredis.FakeRedis(decode_responses=True)
    publishers.set_redis_client(r)
    yield r
    publishers.set_redis_client(None)


@pytest.fixture
def redis_client(_fake_redis):
    _fake_redis.flushall()
    return _fake_redis


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        db.add(Category(id="CAT", name="General", description=None))
        db.add(Category(id="ELECTRONICS_ACCESSORIES", name="Accessories", description="acc"))
        db.add(
            PartnerProductRule(
                partner_id="p-restrict",
                category_id=None,
                allowed_temperature_zones_json='["AMBIENT"]',
                max_weight_g=100,
                requires_signature=None,
                is_hazardous_allowed=False,
                overrides_global=False,
            )
        )
        db.commit()
    finally:
        db.close()
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def pytest_sessionfinish(session, exitstatus) -> None:
    try:
        os.unlink(_DB_PATH)
    except OSError:
        pass
