"""
Unit tests for the Job Scheduler REST API.

The APScheduler background scheduler is replaced with a MagicMock before
main.py is imported so no real scheduling threads are started during tests.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ── Patch the scheduler singleton before main.py is loaded ──────────────────
import scheduler as sched_module  # noqa: E402

_mock_scheduler = MagicMock()
sched_module.scheduler = _mock_scheduler

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from storage import storage  # noqa: E402

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_storage():
    """Wipe all jobs and history between tests."""
    storage._jobs.clear()
    storage._history.clear()
    _mock_scheduler.reset_mock()
    yield
    storage._jobs.clear()
    storage._history.clear()


# ── Helpers ───────────────────────────────────────────────────────────────────

_VALID_JOB = {"name": "echo-job", "command": "echo hello", "cron_expression": "* * * * *"}


def _create_job(client, payload=None):
    return client.post("/jobs", json=payload or _VALID_JOB)


# ── POST /jobs ────────────────────────────────────────────────────────────────


def test_create_job_returns_201(client):
    resp = _create_job(client)
    assert resp.status_code == 201


def test_create_job_response_fields(client):
    resp = _create_job(client)
    data = resp.json()
    assert data["name"] == _VALID_JOB["name"]
    assert data["command"] == _VALID_JOB["command"]
    assert data["cron_expression"] == _VALID_JOB["cron_expression"]
    assert "id" in data
    assert "created_at" in data
    assert data["enabled"] is True


def test_create_job_stored(client):
    resp = _create_job(client)
    job_id = resp.json()["id"]
    assert storage.get_job(job_id) is not None


def test_create_job_schedules_with_apscheduler(client):
    _create_job(client)
    _mock_scheduler.add_job.assert_called_once()


def test_create_job_invalid_cron_returns_422(client):
    resp = client.post(
        "/jobs",
        json={"name": "bad", "command": "echo", "cron_expression": "not-a-cron"},
    )
    assert resp.status_code == 422


def test_create_job_too_few_cron_fields_returns_422(client):
    resp = client.post(
        "/jobs",
        json={"name": "bad", "command": "echo", "cron_expression": "* * *"},
    )
    assert resp.status_code == 422


# ── GET /jobs ─────────────────────────────────────────────────────────────────


def test_list_jobs_empty(client):
    resp = client.get("/jobs")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_jobs_returns_all(client):
    _create_job(client, {"name": "j1", "command": "echo 1", "cron_expression": "* * * * *"})
    _create_job(client, {"name": "j2", "command": "echo 2", "cron_expression": "0 * * * *"})
    resp = client.get("/jobs")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_jobs_names(client):
    _create_job(client, {"name": "alpha", "command": "echo", "cron_expression": "* * * * *"})
    names = [j["name"] for j in client.get("/jobs").json()]
    assert "alpha" in names


# ── DELETE /jobs/{job_id} ─────────────────────────────────────────────────────


def test_delete_job_returns_204(client):
    job_id = _create_job(client).json()["id"]
    resp = client.delete(f"/jobs/{job_id}")
    assert resp.status_code == 204


def test_delete_job_removes_from_storage(client):
    job_id = _create_job(client).json()["id"]
    client.delete(f"/jobs/{job_id}")
    assert storage.get_job(job_id) is None


def test_delete_job_unschedules(client):
    job_id = _create_job(client).json()["id"]
    client.delete(f"/jobs/{job_id}")
    _mock_scheduler.remove_job.assert_called_once_with(job_id)


def test_delete_nonexistent_job_returns_404(client):
    resp = client.delete("/jobs/does-not-exist")
    assert resp.status_code == 404


def test_delete_job_no_longer_in_list(client):
    job_id = _create_job(client).json()["id"]
    client.delete(f"/jobs/{job_id}")
    ids = [j["id"] for j in client.get("/jobs").json()]
    assert job_id not in ids


# ── GET /jobs/{job_id}/history ────────────────────────────────────────────────


def test_history_empty_after_create(client):
    job_id = _create_job(client).json()["id"]
    resp = client.get(f"/jobs/{job_id}/history")
    assert resp.status_code == 200
    assert resp.json() == []


def test_history_nonexistent_job_returns_404(client):
    resp = client.get("/jobs/no-such-id/history")
    assert resp.status_code == 404


def test_history_records_run(client):
    job_id = _create_job(client).json()["id"]
    client.post(f"/jobs/{job_id}/trigger")
    resp = client.get(f"/jobs/{job_id}/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_history_multiple_runs(client):
    job_id = _create_job(client).json()["id"]
    client.post(f"/jobs/{job_id}/trigger")
    client.post(f"/jobs/{job_id}/trigger")
    assert len(client.get(f"/jobs/{job_id}/history").json()) == 2


# ── POST /jobs/{job_id}/trigger ───────────────────────────────────────────────


def test_trigger_returns_202(client):
    job_id = _create_job(client).json()["id"]
    resp = client.post(f"/jobs/{job_id}/trigger")
    assert resp.status_code == 202


def test_trigger_response_fields(client):
    job_id = _create_job(client).json()["id"]
    data = client.post(f"/jobs/{job_id}/trigger").json()
    assert data["job_id"] == job_id
    assert data["triggered_manually"] is True
    assert "started_at" in data
    assert "finished_at" in data
    assert "exit_code" in data


def test_trigger_echo_exits_zero(client):
    job_id = _create_job(client).json()["id"]
    data = client.post(f"/jobs/{job_id}/trigger").json()
    assert data["exit_code"] == 0


def test_trigger_captures_stdout(client):
    job_id = _create_job(
        client, {"name": "hi", "command": "echo hello-world", "cron_expression": "* * * * *"}
    ).json()["id"]
    data = client.post(f"/jobs/{job_id}/trigger").json()
    assert "hello-world" in data["stdout"]


def test_trigger_failing_command(client):
    job_id = _create_job(
        client, {"name": "fail", "command": "false", "cron_expression": "* * * * *"}
    ).json()["id"]
    data = client.post(f"/jobs/{job_id}/trigger").json()
    assert data["exit_code"] != 0


def test_trigger_nonexistent_job_returns_404(client):
    resp = client.post("/jobs/no-such-id/trigger")
    assert resp.status_code == 404


def test_trigger_run_appears_in_history(client):
    job_id = _create_job(client).json()["id"]
    run_id = client.post(f"/jobs/{job_id}/trigger").json()["id"]
    history = client.get(f"/jobs/{job_id}/history").json()
    assert any(r["id"] == run_id for r in history)
