"""Tests for the web UI endpoint (GET /)."""

import sys
import os

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Re-use the test database wiring already established in test_api.py so that
# module-level overrides of db_module.engine / db_module.SessionLocal are not
# applied a second time (which would swap the engine out from under the already-
# running test client and cause "no such table" errors in the lifespan query).
from tests.test_api import (  # noqa: E402
    _test_engine,
    TestingSession,
    override_get_db,
)

from database import Base, get_db
from main import app

app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    Base.metadata.create_all(bind=_test_engine)
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield


# ---------------------------------------------------------------------------
# GET /  –  web UI
# ---------------------------------------------------------------------------

class TestWebUI:
    def test_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_content_type_is_html(self, client):
        resp = client.get("/")
        assert "text/html" in resp.headers["content-type"]

    def test_response_is_non_empty(self, client):
        resp = client.get("/")
        assert len(resp.content) > 0

    def test_page_title_present(self, client):
        resp = client.get("/")
        assert b"Job Scheduler" in resp.content

    def test_jobs_api_reference_present(self, client):
        """The UI JS must reference the /jobs endpoint."""
        resp = client.get("/")
        assert b"/jobs" in resp.content

    def test_history_api_reference_present(self, client):
        """The UI JS must reference the /history endpoint path fragment."""
        resp = client.get("/")
        assert b"history" in resp.content

    def test_ui_loads_independently_of_job_count(self, client):
        """UI should return 200 whether there are jobs or not."""
        resp = client.get("/")
        assert resp.status_code == 200

    def test_ui_loads_with_existing_jobs(self, client):
        """UI endpoint should return 200 even when jobs exist in the DB."""
        client.post(
            "/jobs",
            json={"name": "UI Test Job", "command": "echo ui", "cron_expression": "* * * * *"},
        )
        resp = client.get("/")
        assert resp.status_code == 200

    def test_ui_contains_refresh_control(self, client):
        """Page should provide a way for users to refresh data."""
        resp = client.get("/")
        assert b"Refresh" in resp.content

    def test_ui_contains_trigger_control(self, client):
        """Page should expose a trigger action for running jobs manually."""
        resp = client.get("/")
        assert b"Trigger" in resp.content

    def test_ui_contains_delete_control(self, client):
        """Page should expose a delete action for removing jobs."""
        resp = client.get("/")
        assert b"Delete" in resp.content
