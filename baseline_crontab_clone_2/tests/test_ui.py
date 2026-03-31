"""Tests for the web UI endpoint and SQLite persistence."""
import pytest
from fastapi.testclient import TestClient


class TestWebUI:
    def test_get_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_get_root_returns_html(self, client):
        resp = client.get("/")
        assert "text/html" in resp.headers["content-type"]

    def test_ui_contains_jobs_table(self, client):
        resp = client.get("/")
        assert "jobs-table" in resp.text

    def test_ui_contains_history_section(self, client):
        resp = client.get("/")
        assert "history-section" in resp.text

    def test_ui_references_jobs_api(self, client):
        resp = client.get("/")
        assert "/jobs" in resp.text

    def test_ui_contains_expected_column_headers(self, client):
        resp = client.get("/")
        body = resp.text
        for header in ("Name", "Command", "Schedule", "Active"):
            assert header in body, f"Expected column header '{header}' not found in UI"

    def test_ui_contains_trigger_js(self, client):
        resp = client.get("/")
        assert "triggerJob" in resp.text

    def test_ui_contains_history_js(self, client):
        resp = client.get("/")
        assert "loadHistory" in resp.text


class TestSQLitePersistence:
    """Verify that jobs and run history are stored in SQLite and survive in-memory."""

    def test_created_job_is_retrievable(self, client):
        resp = client.post(
            "/jobs",
            json={"name": "persist_test", "command": "echo hi", "cron_expression": "* * * * *"},
        )
        assert resp.status_code == 201
        job_id = resp.json()["id"]

        listed = {j["id"] for j in client.get("/jobs").json()}
        assert job_id in listed

    def test_run_history_is_persisted(self, client):
        job_id = client.post(
            "/jobs",
            json={"name": "hist_persist", "command": "echo stored", "cron_expression": "* * * * *"},
        ).json()["id"]

        client.post(f"/jobs/{job_id}/trigger")
        history = client.get(f"/jobs/{job_id}/history").json()
        assert len(history) == 1
        assert "stored" in history[0]["stdout"]

    def test_multiple_runs_all_persisted(self, client):
        job_id = client.post(
            "/jobs",
            json={"name": "multi_run", "command": "echo x", "cron_expression": "* * * * *"},
        ).json()["id"]

        for _ in range(3):
            client.post(f"/jobs/{job_id}/trigger")

        history = client.get(f"/jobs/{job_id}/history").json()
        assert len(history) == 3

    def test_delete_removes_job_from_db(self, client):
        job_id = client.post(
            "/jobs",
            json={"name": "to_delete", "command": "echo bye", "cron_expression": "* * * * *"},
        ).json()["id"]

        client.delete(f"/jobs/{job_id}")
        ids = {j["id"] for j in client.get("/jobs").json()}
        assert job_id not in ids

    def test_history_cleared_on_job_delete(self, client):
        job_id = client.post(
            "/jobs",
            json={"name": "cascade_del", "command": "echo del", "cron_expression": "* * * * *"},
        ).json()["id"]

        client.post(f"/jobs/{job_id}/trigger")
        client.delete(f"/jobs/{job_id}")
        assert client.get(f"/jobs/{job_id}/history").status_code == 404
