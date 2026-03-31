"""
Tests for domain/scheduler/adaptors — RestAdaptor (FastAPI routes).

Test contract (ADR 0001, ADR 0004, AI_CONTRACT §1, §5, §6):
- Tests are permanent; never removed.
- Written before implementation.
- Translation tests assert: (1) raw fixture source fields, (2) canonical model result.
"""
import json
import os
import unittest
from datetime import datetime, timezone

FIXTURES_RAW      = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "raw",      "scheduler", "v1")
FIXTURES_EXPECTED = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "expected", "scheduler", "v1")


def _load(base: str, filename: str) -> dict:
    with open(os.path.join(base, filename)) as fh:
        return json.load(fh)


def _make_test_client():
    """Build a synchronous TestClient wired with an in-memory repo."""
    from fastapi import FastAPI
    from starlette.testclient import TestClient
    from domain.scheduler.ports.in_memory_job_repository import InMemoryJobRepository
    from domain.scheduler.core.commands import (
        CreateJobCommand,
        ListJobsCommand,
        DeleteJobCommand,
        TriggerJobCommand,
        GetRunHistoryCommand,
    )
    from domain.scheduler.adaptors.rest_adaptor import build_router

    repo = InMemoryJobRepository()
    router = build_router(
        create_cmd=CreateJobCommand(repo=repo),
        list_cmd=ListJobsCommand(repo=repo),
        delete_cmd=DeleteJobCommand(repo=repo),
        trigger_cmd=TriggerJobCommand(repo=repo),
        history_cmd=GetRunHistoryCommand(repo=repo),
    )
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestRestAdaptorTranslation(unittest.TestCase):
    """Assert fixture integrity and canonical model correctness at the REST boundary."""

    def test_create_job_raw_fixture_has_required_fields(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        self.assertIn("name",            raw)
        self.assertIn("command",         raw)
        self.assertIn("cron_expression", raw)

    def test_expected_job_fixture_has_required_fields(self):
        exp = _load(FIXTURES_EXPECTED, "job.0.0.1.json")
        self.assertIn("name",            exp)
        self.assertIn("command",         exp)
        self.assertIn("cron_expression", exp)
        self.assertIn("enabled",         exp)

    def test_create_job_returns_canonical_fields(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        exp = _load(FIXTURES_EXPECTED, "job.0.0.1.json")

        client = _make_test_client()
        response = client.post("/jobs", json=raw)

        self.assertEqual(response.status_code, 201)
        body = response.json()

        # Assert canonical model fields are present and match expected fixture
        self.assertEqual(body["name"],            exp["name"])
        self.assertEqual(body["command"],         exp["command"])
        self.assertEqual(body["cron_expression"], exp["cron_expression"])
        self.assertEqual(body["enabled"],         exp["enabled"])
        self.assertIn("id",         body)
        self.assertIn("created_at", body)

    def test_trigger_job_raw_fixture_has_required_fields(self):
        raw = _load(FIXTURES_RAW, "trigger_job.0.0.1.json")
        self.assertIn("job_id", raw)

    def test_expected_run_record_fixture_has_required_fields(self):
        exp = _load(FIXTURES_EXPECTED, "run_record.0.0.1.json")
        self.assertIn("job_id", exp)
        self.assertIn("status", exp)
        self.assertIn("output", exp)


class TestRestAdaptorEndpoints(unittest.TestCase):
    """Integration tests for each REST endpoint."""

    def setUp(self):
        self.client = _make_test_client()

    def test_list_jobs_empty(self):
        r = self.client.get("/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), [])

    def test_create_then_list(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        self.client.post("/jobs", json=raw)
        r = self.client.get("/jobs")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_create_invalid_cron_returns_422(self):
        r = self.client.post("/jobs", json={"name": "bad", "command": "x", "cron_expression": "not-valid"})
        self.assertEqual(r.status_code, 422)

    def test_delete_job(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        created = self.client.post("/jobs", json=raw).json()
        r = self.client.delete(f"/jobs/{created['id']}")
        self.assertEqual(r.status_code, 204)

    def test_delete_nonexistent_job_returns_404(self):
        r = self.client.delete("/jobs/ghost-id")
        self.assertEqual(r.status_code, 404)

    def test_trigger_job(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        created = self.client.post("/jobs", json=raw).json()
        r = self.client.post(f"/jobs/{created['id']}/trigger")
        self.assertEqual(r.status_code, 201)
        body = r.json()
        self.assertEqual(body["job_id"], created["id"])
        self.assertIn(body["status"], ("success", "failure"))
        self.assertIn("id",           body)
        self.assertIn("triggered_at", body)

    def test_trigger_nonexistent_job_returns_404(self):
        r = self.client.post("/jobs/ghost-id/trigger")
        self.assertEqual(r.status_code, 404)

    def test_get_run_history(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        created = self.client.post("/jobs", json=raw).json()
        self.client.post(f"/jobs/{created['id']}/trigger")
        self.client.post(f"/jobs/{created['id']}/trigger")
        r = self.client.get(f"/jobs/{created['id']}/history")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 2)

    def test_get_history_nonexistent_job_returns_404(self):
        r = self.client.get("/jobs/ghost-id/history")
        self.assertEqual(r.status_code, 404)


def _make_ui_test_client():
    """Build a TestClient wired with an in-memory repo and the web UI router."""
    from fastapi import FastAPI
    from starlette.testclient import TestClient
    from domain.scheduler.ports.in_memory_job_repository import InMemoryJobRepository
    from domain.scheduler.core.commands import (
        CreateJobCommand,
        ListJobsCommand,
        GetRunHistoryCommand,
        TriggerJobCommand,
        DeleteJobCommand,
    )
    from domain.scheduler.adaptors.web_ui_adaptor import build_ui_router
    from domain.scheduler.adaptors.rest_adaptor import build_router

    repo = InMemoryJobRepository()
    app = FastAPI()
    app.include_router(
        build_router(
            create_cmd=CreateJobCommand(repo=repo),
            list_cmd=ListJobsCommand(repo=repo),
            delete_cmd=DeleteJobCommand(repo=repo),
            trigger_cmd=TriggerJobCommand(repo=repo),
            history_cmd=GetRunHistoryCommand(repo=repo),
        )
    )
    app.include_router(
        build_ui_router(
            list_cmd=ListJobsCommand(repo=repo),
            history_cmd=GetRunHistoryCommand(repo=repo),
        )
    )
    return TestClient(app), repo


class TestWebUIAdaptor(unittest.TestCase):
    """Integration tests for the /ui HTML dashboard endpoint."""

    def setUp(self):
        self.client, self._repo = _make_ui_test_client()

    def test_ui_returns_200_with_html_content_type(self):
        r = self.client.get("/ui")
        self.assertEqual(r.status_code, 200)
        self.assertIn("text/html", r.headers["content-type"])

    def test_ui_empty_shows_no_jobs_message(self):
        r = self.client.get("/ui")
        self.assertEqual(r.status_code, 200)
        self.assertIn("No jobs scheduled", r.text)

    def test_ui_shows_job_name_after_creation(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        self.client.post("/jobs", json=raw)
        r = self.client.get("/ui")
        self.assertEqual(r.status_code, 200)
        self.assertIn(raw["name"], r.text)

    def test_ui_shows_job_command_after_creation(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        self.client.post("/jobs", json=raw)
        r = self.client.get("/ui")
        self.assertIn(raw["command"], r.text)

    def test_ui_shows_cron_expression_after_creation(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        self.client.post("/jobs", json=raw)
        r = self.client.get("/ui")
        self.assertIn(raw["cron_expression"], r.text)

    def test_ui_shows_no_runs_yet_before_trigger(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        self.client.post("/jobs", json=raw)
        r = self.client.get("/ui")
        self.assertIn("No runs yet", r.text)

    def test_ui_shows_run_history_after_trigger(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        created = self.client.post("/jobs", json=raw).json()
        self.client.post(f"/jobs/{created['id']}/trigger")
        r = self.client.get("/ui")
        # status should appear in the history table
        self.assertTrue(
            "success" in r.text or "failure" in r.text,
            "Expected run status in dashboard HTML",
        )

    def test_ui_shows_run_history_section_heading(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        created = self.client.post("/jobs", json=raw).json()
        self.client.post(f"/jobs/{created['id']}/trigger")
        r = self.client.get("/ui")
        self.assertIn("Run History", r.text)

    def test_ui_shows_multiple_jobs(self):
        self.client.post("/jobs", json={"name": "job-alpha", "command": "echo a", "cron_expression": "* * * * *"})
        self.client.post("/jobs", json={"name": "job-beta",  "command": "echo b", "cron_expression": "0 * * * *"})
        r = self.client.get("/ui")
        self.assertIn("job-alpha", r.text)
        self.assertIn("job-beta",  r.text)

    def test_web_ui_adaptor_implements_interface(self):
        """build_ui_router returns an APIRouter (web UI adaptor follows interface contract)."""
        from fastapi import APIRouter
        from domain.scheduler.ports.in_memory_job_repository import InMemoryJobRepository
        from domain.scheduler.core.commands import ListJobsCommand, GetRunHistoryCommand
        from domain.scheduler.adaptors.web_ui_adaptor import build_ui_router
        repo = InMemoryJobRepository()
        router = build_ui_router(
            list_cmd=ListJobsCommand(repo=repo),
            history_cmd=GetRunHistoryCommand(repo=repo),
        )
        self.assertIsInstance(router, APIRouter)

    def test_i_web_ui_adaptor_is_abstract(self):
        """IWebUIAdaptor cannot be instantiated directly."""
        from domain.scheduler.adaptors.i_web_ui_adaptor import IWebUIAdaptor
        with self.assertRaises(TypeError):
            IWebUIAdaptor()  # type: ignore[abstract]


if __name__ == "__main__":
    unittest.main()
