import os

# Must be set before any app modules are imported so database.py picks up the
# test URL and the lifespan skips starting APScheduler.
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///./test_scheduler.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

_engine = create_engine(
    os.environ["DATABASE_URL"], connect_args={"check_same_thread": False}
)
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=_engine)
    yield
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c
