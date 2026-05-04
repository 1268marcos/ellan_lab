import os
import tempfile

_fd, _DB_PATH = tempfile.mkstemp(suffix="partner_api_test.db")
os.close(_fd)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{_DB_PATH}"

import pytest
from fastapi.testclient import TestClient

from database import Base, engine
from main import app


@pytest.fixture
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


def pytest_sessionfinish(session, exitstatus) -> None:
    try:
        os.unlink(_DB_PATH)
    except OSError:
        pass
