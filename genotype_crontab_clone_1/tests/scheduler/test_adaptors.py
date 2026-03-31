"""
tests/scheduler/test_adaptors.py

Tests for the inbound HTTP adaptor (HttpAdaptor / FastAPI routes).
Uses httpx.TestClient to drive routes; injects a mock SchedulerService.
"""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

FIXTURES_RAW      = Path(__file__).parent.parent.parent / "fixtures" / "raw"      / "scheduler" / "v1"
FIXTURES_EXPECTED = Path(__file__).parent.parent.parent / "fixtures" / "expected" / "scheduler" / "v1"


def _make_job(job_id="job-001", name="cleanup-logs",
              command="echo hi", cron="0 2 * * *"):
    from domain.scheduler.core.job import Job
    return Job(
        id              = job_id,
        name            = name,
        command         = command,
        cron_expression = cron,
        created_at      = datetime(2026, 3, 28, 20, 0, 0, tzinfo=timezone.utc),
        enabled         = True,
    )


def _make_run_record(job_id="job-001"):
    from domain.scheduler.core.job import RunRecord
    return RunRecord(
        id           = "run-001",
        job_id       = job_id,
        triggered_at = datetime(2026, 3, 28, 20, 5, 0, tzinfo=timezone.utc),
        status       = "success",
        output       = "Deleted 3 files.",
    )


def _build_test_client(mock_service):
    """Build a FastAPI TestClient with mock_service injected via HttpAdaptor."""
    from fastapi import FastAPI
    from httpx import AsyncClient, ASGITransport
    from domain.scheduler.core.adaptors.http_adaptor import HttpAdaptor
    app    = FastAPI()
    adaptor = HttpAdaptor(service=mock_service)
    app.include_router(adaptor.router)
    return app


class TestHttpAdaptorCreateJob(unittest.TestCase):
    """POST /jobs — create a new scheduled job."""

    def setUp(self):
        self.mock_service = MagicMock()
        self.app          = _build_test_client(self.mock_service)

    def _post_create(self, payload):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        async def _run():
            async with AsyncClient(
                transport=ASGITransport(app=self.app), base_url="http://test"
            ) as client:
                return await client.post("/jobs", json=payload)
        return asyncio.run(_run())

    def test_create_job_returns_201_with_job_id(self):
        with open(FIXTURES_RAW / "job.create.request.0.0.1.json") as f:
            payload = json.load(f)
        self.mock_service.create_job.return_value = _make_job(
            name    = payload["name"],
            command = payload["command"],
            cron    = payload["cron_expression"],
        )
        response = self._post_create(payload)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIn("id",              body)
        self.assertIn("name",            body)
        self.assertIn("command",         body)
        self.assertIn("cron_expression", body)
        self.assertIn("created_at",      body)
        self.assertIn("enabled",         body)

    def test_create_job_calls_service_with_correct_args(self):
        with open(FIXTURES_RAW / "job.create.request.0.0.1.json") as f:
            payload = json.load(f)
        self.mock_service.create_job.return_value = _make_job(
            name    = payload["name"],
            command = payload["command"],
            cron    = payload["cron_expression"],
        )
        self._post_create(payload)
        self.mock_service.create_job.assert_called_once_with(
            name            = payload["name"],
            command         = payload["command"],
            cron_expression = payload["cron_expression"],
        )

    def test_create_job_response_matches_expected_fixture_fields(self):
        """
        Translation test:
        1. Raw fixture has expected source fields.
        2. Response body matches expected canonical fixture values.
        """
        with open(FIXTURES_RAW / "job.create.request.0.0.1.json") as f:
            raw_req = json.load(f)
        with open(FIXTURES_EXPECTED / "job.create.0.0.1.json") as f:
            expected = json.load(f)

        # (1) raw fixture integrity
        self.assertIn("name",            raw_req)
        self.assertIn("command",         raw_req)
        self.assertIn("cron_expression", raw_req)

        # (2) canonical model result
        self.mock_service.create_job.return_value = _make_job(
            name    = expected["name"],
            command = expected["command"],
            cron    = expected["cron_expression"],
        )
        response = self._post_create(raw_req)
        body     = response.json()
        self.assertEqual(body["name"],            expected["name"])
        self.assertEqual(body["command"],         expected["command"])
        self.assertEqual(body["cron_expression"], expected["cron_expression"])
        self.assertEqual(body["enabled"],         expected["enabled"])

    def test_missing_name_returns_422(self):
        response = self._post_create({"command": "echo hi", "cron_expression": "* * * * *"})
        self.assertEqual(response.status_code, 422)

    def test_missing_command_returns_422(self):
        response = self._post_create({"name": "job", "cron_expression": "* * * * *"})
        self.assertEqual(response.status_code, 422)


class TestHttpAdaptorListJobs(unittest.TestCase):
    """GET /jobs — list all scheduled jobs."""

    def setUp(self):
        self.mock_service = MagicMock()
        self.app          = _build_test_client(self.mock_service)

    def _get_list(self):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        async def _run():
            async with AsyncClient(
                transport=ASGITransport(app=self.app), base_url="http://test"
            ) as client:
                return await client.get("/jobs")
        return asyncio.run(_run())

    def test_list_returns_200_with_array(self):
        with open(FIXTURES_RAW / "job.list.response.0.0.1.json") as f:
            raw = json.load(f)
        self.mock_service.list_jobs.return_value = [
            _make_job(job_id=item["id"], name=item["name"],
                      command=item["command"], cron=item["cron_expression"])
            for item in raw
        ]
        response = self._get_list()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), len(raw))

    def test_list_empty_returns_empty_array(self):
        self.mock_service.list_jobs.return_value = []
        response = self._get_list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_list_response_matches_expected_fixture(self):
        """
        Translation test:
        1. Raw fixture has the expected source fields.
        2. Response body matches canonical fields in expected fixture.
        """
        with open(FIXTURES_RAW / "job.list.response.0.0.1.json") as f:
            raw = json.load(f)
        with open(FIXTURES_EXPECTED / "job.list.0.0.1.json") as f:
            expected = json.load(f)

        # (1) raw fixture integrity
        for item in raw:
            self.assertIn("id",   item)
            self.assertIn("name", item)

        # (2) canonical model result
        self.mock_service.list_jobs.return_value = [
            _make_job(job_id=item["id"], name=item["name"],
                      command=item["command"], cron=item["cron_expression"])
            for item in raw
        ]
        body = self._get_list().json()
        for i, exp in enumerate(expected):
            self.assertEqual(body[i]["name"],            exp["name"])
            self.assertEqual(body[i]["command"],         exp["command"])
            self.assertEqual(body[i]["cron_expression"], exp["cron_expression"])


class TestHttpAdaptorDeleteJob(unittest.TestCase):
    """DELETE /jobs/{job_id} — delete a job."""

    def setUp(self):
        self.mock_service = MagicMock()
        self.app          = _build_test_client(self.mock_service)

    def _delete(self, job_id):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        async def _run():
            async with AsyncClient(
                transport=ASGITransport(app=self.app), base_url="http://test"
            ) as client:
                return await client.delete(f"/jobs/{job_id}")
        return asyncio.run(_run())

    def test_delete_existing_job_returns_204(self):
        self.mock_service.get_job.return_value = _make_job()
        response = self._delete("job-001")
        self.assertEqual(response.status_code, 204)
        self.mock_service.delete_job.assert_called_once_with("job-001")

    def test_delete_nonexistent_job_returns_404(self):
        self.mock_service.get_job.return_value = None
        response = self._delete("ghost")
        self.assertEqual(response.status_code, 404)


class TestHttpAdaptorRunHistory(unittest.TestCase):
    """GET /jobs/{job_id}/runs — run history for a job."""

    def setUp(self):
        self.mock_service = MagicMock()
        self.app          = _build_test_client(self.mock_service)

    def _get_runs(self, job_id):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        async def _run():
            async with AsyncClient(
                transport=ASGITransport(app=self.app), base_url="http://test"
            ) as client:
                return await client.get(f"/jobs/{job_id}/runs")
        return asyncio.run(_run())

    def test_run_history_returns_200_with_array(self):
        self.mock_service.get_job.return_value = _make_job()
        self.mock_service.get_run_history.return_value = [_make_run_record()]
        response = self._get_runs("job-001")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 1)

    def test_run_history_response_fields(self):
        self.mock_service.get_job.return_value = _make_job()
        self.mock_service.get_run_history.return_value = [_make_run_record()]
        body = self._get_runs("job-001").json()
        item = body[0]
        self.assertIn("id",           item)
        self.assertIn("job_id",       item)
        self.assertIn("triggered_at", item)
        self.assertIn("status",       item)
        self.assertIn("output",       item)

    def test_run_history_unknown_job_returns_404(self):
        self.mock_service.get_job.return_value = None
        response = self._get_runs("ghost")
        self.assertEqual(response.status_code, 404)

    def test_run_history_matches_expected_fixture(self):
        """
        Translation test:
        1. Raw fixture has expected source fields.
        2. Response body matches canonical expected fixture values.
        """
        with open(FIXTURES_RAW / "job.run_history.response.0.0.1.json") as f:
            raw = json.load(f)
        with open(FIXTURES_EXPECTED / "job.run_history.0.0.1.json") as f:
            expected = json.load(f)

        # (1) raw fixture integrity
        for item in raw:
            self.assertIn("job_id",  item)
            self.assertIn("status",  item)
            self.assertIn("output",  item)

        # (2) canonical model result
        from domain.scheduler.core.job import RunRecord
        records = [
            RunRecord(
                id           = item["id"],
                job_id       = item["job_id"],
                triggered_at = datetime.fromisoformat(
                    item["triggered_at"].replace("Z", "+00:00")
                ),
                status       = item["status"],
                output       = item["output"],
            )
            for item in raw
        ]
        self.mock_service.get_job.return_value = _make_job(
            job_id = raw[0]["job_id"]
        )
        self.mock_service.get_run_history.return_value = records
        body = self._get_runs(raw[0]["job_id"]).json()
        for i, exp in enumerate(expected):
            self.assertEqual(body[i]["job_id"],  exp["job_id"])
            self.assertEqual(body[i]["status"],  exp["status"])
            self.assertEqual(body[i]["output"],  exp["output"])


class TestHttpAdaptorTriggerJob(unittest.TestCase):
    """POST /jobs/{job_id}/trigger — manually trigger a job."""

    def setUp(self):
        self.mock_service = MagicMock()
        self.app          = _build_test_client(self.mock_service)

    def _trigger(self, job_id):
        import asyncio
        from httpx import AsyncClient, ASGITransport
        async def _run():
            async with AsyncClient(
                transport=ASGITransport(app=self.app), base_url="http://test"
            ) as client:
                return await client.post(f"/jobs/{job_id}/trigger")
        return asyncio.run(_run())

    def test_trigger_existing_job_returns_200(self):
        self.mock_service.get_job.return_value    = _make_job()
        self.mock_service.trigger_job.return_value = _make_run_record()
        response = self._trigger("job-001")
        self.assertEqual(response.status_code, 200)

    def test_trigger_returns_run_record_fields(self):
        self.mock_service.get_job.return_value    = _make_job()
        self.mock_service.trigger_job.return_value = _make_run_record()
        body = self._trigger("job-001").json()
        self.assertIn("id",           body)
        self.assertIn("job_id",       body)
        self.assertIn("triggered_at", body)
        self.assertIn("status",       body)
        self.assertIn("output",       body)

    def test_trigger_unknown_job_returns_404(self):
        self.mock_service.get_job.return_value = None
        response = self._trigger("ghost")
        self.assertEqual(response.status_code, 404)

    def test_trigger_calls_service_with_correct_job_id(self):
        self.mock_service.get_job.return_value    = _make_job()
        self.mock_service.trigger_job.return_value = _make_run_record()
        self._trigger("job-001")
        self.mock_service.trigger_job.assert_called_once_with("job-001")


if __name__ == "__main__":
    unittest.main()
