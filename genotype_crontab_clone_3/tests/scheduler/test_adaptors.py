"""
tests/scheduler/test_adaptors.py

Tests for the FastAPI inbound adaptor (scheduler_routes).
Uses TestClient to exercise the HTTP boundary without a live server.
Validates request/response shape against versioned fixtures.
"""

import json
import pathlib
import unittest
from unittest.mock import MagicMock, patch

FIXTURES_RAW      = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "raw"      / "scheduler" / "v1"
FIXTURES_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "scheduler" / "v1"


def _build_test_app():
    """Build a FastAPI app wired with a mock SchedulerService for isolation."""
    from fastapi import FastAPI
    from domain.scheduler.core.scheduler_service import SchedulerService
    from domain.scheduler.core.adaptors.scheduler_routes import build_router

    mock_service = MagicMock(spec=SchedulerService)
    app = FastAPI()
    app.include_router(build_router(service=mock_service))
    return app, mock_service


class TestSchedulerRoutesCreateJob(unittest.TestCase):

    def setUp(self):
        from fastapi.testclient import TestClient
        self.app, self.mock_service = _build_test_app()
        self.client = TestClient(self.app)

    def test_post_jobs_returns_201_with_job_shape(self):
        from domain.scheduler.core.job import Job
        with open(FIXTURES_RAW / "job.create.success.0.0.1.json") as f:
            raw = json.load(f)
        with open(FIXTURES_EXPECTED / "job.create.success.0.0.1.json") as f:
            expected = json.load(f)

        fake_job = Job(
            id=expected["id"],
            name=expected["name"],
            command=expected["command"],
            cron_expression=expected["cron_expression"],
            created_at=expected["created_at"],
        )
        self.mock_service.create_job.return_value = fake_job

        response = self.client.post("/jobs", json=raw)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["id"],              expected["id"])
        self.assertEqual(body["name"],            expected["name"])
        self.assertEqual(body["command"],         expected["command"])
        self.assertEqual(body["cron_expression"], expected["cron_expression"])
        self.assertEqual(body["created_at"],      expected["created_at"])

    def test_post_jobs_calls_service_with_correct_args(self):
        from domain.scheduler.core.job import Job
        with open(FIXTURES_RAW / "job.create.success.0.0.1.json") as f:
            raw = json.load(f)

        fake_job = Job(id="x", name=raw["name"], command=raw["command"],
                       cron_expression=raw["cron_expression"], created_at="2026-03-28T00:00:00+00:00")
        self.mock_service.create_job.return_value = fake_job

        self.client.post("/jobs", json=raw)
        self.mock_service.create_job.assert_called_once_with(
            name=raw["name"],
            command=raw["command"],
            cron_expression=raw["cron_expression"],
        )

    def test_post_jobs_returns_422_on_missing_field(self):
        response = self.client.post("/jobs", json={"name": "only-name"})
        self.assertEqual(response.status_code, 422)


class TestSchedulerRoutesListJobs(unittest.TestCase):

    def setUp(self):
        from fastapi.testclient import TestClient
        self.app, self.mock_service = _build_test_app()
        self.client = TestClient(self.app)

    def test_get_jobs_returns_200_with_job_list(self):
        from domain.scheduler.core.job import Job
        with open(FIXTURES_EXPECTED / "job.list.success.0.0.1.json") as f:
            expected = json.load(f)

        fake_jobs = [
            Job(
                id=j["id"],
                name=j["name"],
                command=j["command"],
                cron_expression=j["cron_expression"],
                created_at=j["created_at"],
            )
            for j in expected
        ]
        self.mock_service.list_jobs.return_value = fake_jobs

        response = self.client.get("/jobs")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 2)
        self.assertEqual(body[0]["id"], expected[0]["id"])
        self.assertEqual(body[1]["id"], expected[1]["id"])

    def test_get_jobs_returns_empty_list_when_no_jobs(self):
        self.mock_service.list_jobs.return_value = []
        response = self.client.get("/jobs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])


class TestSchedulerRoutesDeleteJob(unittest.TestCase):

    def setUp(self):
        from fastapi.testclient import TestClient
        self.app, self.mock_service = _build_test_app()
        self.client = TestClient(self.app)

    def test_delete_job_returns_204_when_deleted(self):
        self.mock_service.delete_job.return_value = True
        response = self.client.delete("/jobs/abc")
        self.assertEqual(response.status_code, 204)

    def test_delete_job_returns_404_when_not_found(self):
        self.mock_service.delete_job.return_value = False
        response = self.client.delete("/jobs/missing")
        self.assertEqual(response.status_code, 404)

    def test_delete_job_calls_service_with_job_id(self):
        self.mock_service.delete_job.return_value = True
        self.client.delete("/jobs/abc-123")
        self.mock_service.delete_job.assert_called_once_with("abc-123")


class TestSchedulerRoutesRunHistory(unittest.TestCase):

    def setUp(self):
        from fastapi.testclient import TestClient
        self.app, self.mock_service = _build_test_app()
        self.client = TestClient(self.app)

    def test_get_runs_returns_200_with_run_list(self):
        from domain.scheduler.core.job_run import JobRun
        with open(FIXTURES_EXPECTED / "job.trigger.success.0.0.1.json") as f:
            expected = json.load(f)

        fake_run = JobRun(
            id=expected["id"],
            job_id=expected["job_id"],
            triggered_at=expected["triggered_at"],
            exit_code=expected["exit_code"],
            output=expected["output"],
            trigger_type=expected["trigger_type"],
        )
        self.mock_service.get_run_history.return_value = [fake_run]

        response = self.client.get(f"/jobs/{expected['job_id']}/runs")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["id"],      expected["id"])
        self.assertEqual(body[0]["job_id"],  expected["job_id"])

    def test_get_runs_returns_empty_list_for_job_with_no_runs(self):
        self.mock_service.get_run_history.return_value = []
        response = self.client.get("/jobs/some-id/runs")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_runs_calls_service_with_job_id(self):
        self.mock_service.get_run_history.return_value = []
        self.client.get("/jobs/target-id/runs")
        self.mock_service.get_run_history.assert_called_once_with("target-id")


class TestSchedulerRoutesTriggerJob(unittest.TestCase):

    def setUp(self):
        from fastapi.testclient import TestClient
        self.app, self.mock_service = _build_test_app()
        self.client = TestClient(self.app)

    def test_trigger_job_returns_200_with_run_shape(self):
        from domain.scheduler.core.job_run import JobRun
        with open(FIXTURES_EXPECTED / "job.trigger.success.0.0.1.json") as f:
            expected = json.load(f)

        fake_run = JobRun(
            id=expected["id"],
            job_id=expected["job_id"],
            triggered_at=expected["triggered_at"],
            exit_code=expected["exit_code"],
            output=expected["output"],
            trigger_type=expected["trigger_type"],
        )
        self.mock_service.trigger_job.return_value = fake_run

        response = self.client.post(f"/jobs/{expected['job_id']}/trigger")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["id"],           expected["id"])
        self.assertEqual(body["job_id"],       expected["job_id"])
        self.assertEqual(body["exit_code"],    expected["exit_code"])
        self.assertEqual(body["trigger_type"], expected["trigger_type"])

    def test_trigger_job_returns_404_when_job_not_found(self):
        self.mock_service.trigger_job.side_effect = ValueError("job not found")
        response = self.client.post("/jobs/missing-id/trigger")
        self.assertEqual(response.status_code, 404)

    def test_trigger_job_calls_service_with_job_id(self):
        from domain.scheduler.core.job_run import JobRun
        fake_run = JobRun(
            id="r1", job_id="j1", triggered_at="2026-03-28T00:05:00+00:00",
            exit_code=0, output="", trigger_type="manual",
        )
        self.mock_service.trigger_job.return_value = fake_run
        self.client.post("/jobs/j1/trigger")
        self.mock_service.trigger_job.assert_called_once_with("j1")


if __name__ == "__main__":
    unittest.main()
