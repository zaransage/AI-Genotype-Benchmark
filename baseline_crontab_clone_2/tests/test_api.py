"""Unit tests for the Job Scheduler REST API."""
import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_job(client: TestClient, name="backup", command="echo hello", cron="* * * * *"):
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
        assert data["name"] == "backup"
        assert data["command"] == "echo hello"
        assert data["cron_expression"] == "* * * * *"
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    def test_invalid_cron_expression(self, client):
        resp = client.post(
            "/jobs",
            json={"name": "bad", "command": "echo hi", "cron_expression": "not-valid"},
        )
        assert resp.status_code == 422

    def test_duplicate_name_returns_409(self, client):
        _create_job(client, name="dup")
        resp = _create_job(client, name="dup")
        assert resp.status_code == 409

    def test_various_valid_cron_expressions(self, client):
        expressions = [
            ("job1", "0 * * * *"),    # every hour
            ("job2", "0 0 * * *"),    # daily midnight
            ("job3", "*/5 * * * *"),  # every 5 minutes
            ("job4", "0 9 * * 1"),    # monday 9am
        ]
        for name, cron in expressions:
            resp = _create_job(client, name=name, cron=cron)
            assert resp.status_code == 201, f"Failed for cron {cron!r}: {resp.json()}"


# ---------------------------------------------------------------------------
# GET /jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_empty(self, client):
        resp = client.get("/jobs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_all_jobs(self, client):
        _create_job(client, name="job_a")
        _create_job(client, name="job_b")
        resp = client.get("/jobs")
        assert resp.status_code == 200
        names = {j["name"] for j in resp.json()}
        assert names == {"job_a", "job_b"}

    def test_response_schema(self, client):
        _create_job(client)
        job = client.get("/jobs").json()[0]
        assert all(k in job for k in ("id", "name", "command", "cron_expression", "created_at", "is_active"))


# ---------------------------------------------------------------------------
# DELETE /jobs/{job_id}
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_delete_existing(self, client):
        job_id = _create_job(client).json()["id"]
        resp = client.delete(f"/jobs/{job_id}")
        assert resp.status_code == 204
        assert client.get("/jobs").json() == []

    def test_delete_nonexistent_returns_404(self, client):
        resp = client.delete("/jobs/does-not-exist")
        assert resp.status_code == 404

    def test_delete_removes_history(self, client):
        job_id = _create_job(client).json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        client.delete(f"/jobs/{job_id}")
        # Job is gone; history endpoint returns 404
        assert client.get(f"/jobs/{job_id}/history").status_code == 404


# ---------------------------------------------------------------------------
# GET /jobs/{job_id}/history
# ---------------------------------------------------------------------------

class TestJobHistory:
    def test_empty_history(self, client):
        job_id = _create_job(client).json()["id"]
        resp = client.get(f"/jobs/{job_id}/history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_nonexistent_job_returns_404(self, client):
        resp = client.get("/jobs/nonexistent/history")
        assert resp.status_code == 404

    def test_history_populated_after_trigger(self, client):
        job_id = _create_job(client).json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        resp = client.get(f"/jobs/{job_id}/history")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_history_ordered_newest_first(self, client):
        job_id = _create_job(client).json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        client.post(f"/jobs/{job_id}/trigger")
        history = client.get(f"/jobs/{job_id}/history").json()
        assert len(history) == 2
        assert history[0]["started_at"] >= history[1]["started_at"]

    def test_history_schema(self, client):
        job_id = _create_job(client).json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        entry = client.get(f"/jobs/{job_id}/history").json()[0]
        assert all(k in entry for k in ("id", "job_id", "started_at", "finished_at", "exit_code", "stdout", "stderr", "triggered_manually"))


# ---------------------------------------------------------------------------
# POST /jobs/{job_id}/trigger
# ---------------------------------------------------------------------------

class TestTriggerJob:
    def test_trigger_returns_202(self, client):
        job_id = _create_job(client).json()["id"]
        resp = client.post(f"/jobs/{job_id}/trigger")
        assert resp.status_code == 202

    def test_trigger_nonexistent_returns_404(self, client):
        resp = client.post("/jobs/nonexistent/trigger")
        assert resp.status_code == 404

    def test_trigger_marks_manually(self, client):
        job_id = _create_job(client).json()["id"]
        data = client.post(f"/jobs/{job_id}/trigger").json()
        assert data["triggered_manually"] is True
        assert data["job_id"] == job_id

    def test_trigger_captures_stdout(self, client):
        job_id = _create_job(client, command="echo hello_world").json()["id"]
        data = client.post(f"/jobs/{job_id}/trigger").json()
        assert "hello_world" in data["stdout"]

    def test_trigger_captures_exit_code(self, client):
        job_id = _create_job(client, command="echo ok").json()["id"]
        data = client.post(f"/jobs/{job_id}/trigger").json()
        assert data["exit_code"] == 0

    def test_trigger_nonzero_exit_on_failure(self, client):
        job_id = _create_job(client, command="exit 42", name="fail_job").json()["id"]
        data = client.post(f"/jobs/{job_id}/trigger").json()
        assert data["exit_code"] == 42

    def test_trigger_records_finished_at(self, client):
        job_id = _create_job(client).json()["id"]
        data = client.post(f"/jobs/{job_id}/trigger").json()
        assert data["finished_at"] is not None

    def test_multiple_triggers_accumulate_history(self, client):
        job_id = _create_job(client).json()["id"]
        client.post(f"/jobs/{job_id}/trigger")
        client.post(f"/jobs/{job_id}/trigger")
        history = client.get(f"/jobs/{job_id}/history").json()
        assert len(history) == 2
