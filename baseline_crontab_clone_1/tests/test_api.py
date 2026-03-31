"""Unit tests for the job scheduler REST API."""

import sys
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Make the project root importable regardless of how pytest is invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db_module
from database import Base, get_db
from main import app

# ---------------------------------------------------------------------------
# Test database – single shared in-memory SQLite instance (StaticPool)
# ---------------------------------------------------------------------------

_test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)

# Redirect ALL database access (API dependency + scheduler SessionLocal +
# lifespan create_all) to the in-memory engine.
db_module.engine = _test_engine
db_module.SessionLocal = TestingSession


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


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
    """Wipe and recreate tables before every test for full isolation."""
    Base.metadata.drop_all(bind=_test_engine)
    Base.metadata.create_all(bind=_test_engine)
    yield


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _create_job(client, name="Test Job", command="echo hello", cron="* * * * *"):
    return client.post(
        "/jobs",
        json={"name": name, "command": command, "cron_expression": cron},
    )


# ---------------------------------------------------------------------------
# POST /jobs
# ---------------------------------------------------------------------------

class TestCreateJob:
    def test_success(self, client):
        resp = _create_job(client)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Test Job"
        assert data["command"] == "echo hello"
        assert data["cron_expression"] == "* * * * *"
        assert data["enabled"] is True
        assert "id" in data
        assert "created_at" in data

    def test_invalid_cron_expression(self, client):
        resp = client.post(
            "/jobs",
            json={"name": "Bad", "command": "echo x", "cron_expression": "not-valid"},
        )
        assert resp.status_code == 422

    def test_missing_field_returns_422(self, client):
        resp = client.post("/jobs", json={"name": "No command"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_empty(self, client):
        resp = client.get("/jobs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_jobs(self, client):
        _create_job(client, name="Job A", cron="0 * * * *")
        _create_job(client, name="Job B", cron="0 0 * * *")
        resp = client.get("/jobs")
        assert resp.status_code == 200
        names = {j["name"] for j in resp.json()}
        assert names == {"Job A", "Job B"}


# ---------------------------------------------------------------------------
# DELETE /jobs/{job_id}
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_success(self, client):
        job_id = _create_job(client).json()["id"]
        resp = client.delete(f"/jobs/{job_id}")
        assert resp.status_code == 204
        assert client.get("/jobs").json() == []

    def test_not_found(self, client):
        resp = client.delete("/jobs/does-not-exist")
        assert resp.status_code == 404

    def test_history_deleted_with_job(self, client):
        job_id = _create_job(client, command="echo hi").json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        client.delete(f"/jobs/{job_id}")
        # After deletion the history endpoint should 404, not return stale rows.
        resp = client.get(f"/jobs/{job_id}/history")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /jobs/{job_id}/trigger
# ---------------------------------------------------------------------------

class TestTriggerJob:
    def test_success(self, client):
        job_id = _create_job(client, command="echo triggered").json()["id"]
        resp = client.post(f"/jobs/{job_id}/trigger")
        assert resp.status_code == 200
        data = resp.json()
        assert data["job_id"] == job_id
        assert data["triggered_manually"] is True
        assert data["exit_code"] == 0
        assert "triggered" in data["stdout"]
        assert data["finished_at"] is not None

    def test_not_found(self, client):
        resp = client.post("/jobs/nonexistent/trigger")
        assert resp.status_code == 404

    def test_failed_command_exit_code_captured(self, client):
        job_id = _create_job(client, command="exit 42").json()["id"]
        resp = client.post(f"/jobs/{job_id}/trigger")
        assert resp.status_code == 200
        assert resp.json()["exit_code"] == 42

    def test_stderr_captured(self, client):
        job_id = _create_job(client, command="echo err >&2; exit 1").json()["id"]
        resp = client.post(f"/jobs/{job_id}/trigger")
        data = resp.json()
        assert data["exit_code"] == 1
        assert "err" in data["stderr"]


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}/history
# ---------------------------------------------------------------------------

class TestJobHistory:
    def test_empty_history(self, client):
        job_id = _create_job(client).json()["id"]
        resp = client.get(f"/jobs/{job_id}/history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_history_grows_with_runs(self, client):
        job_id = _create_job(client, command="echo run").json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        client.post(f"/jobs/{job_id}/trigger")
        resp = client.get(f"/jobs/{job_id}/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_history_ordered_most_recent_first(self, client):
        job_id = _create_job(client, command="echo x").json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        client.post(f"/jobs/{job_id}/trigger")
        runs = client.get(f"/jobs/{job_id}/history").json()
        assert runs[0]["started_at"] >= runs[1]["started_at"]

    def test_not_found(self, client):
        resp = client.get("/jobs/nonexistent/history")
        assert resp.status_code == 404
