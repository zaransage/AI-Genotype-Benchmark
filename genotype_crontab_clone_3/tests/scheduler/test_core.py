"""
tests/scheduler/test_core.py

Tests for the canonical Job and JobRun dataclass models and SchedulerService business logic.
Each test is self-describing per ADR-0004 (unit tests as multi-agent contract).
"""

import json
import pathlib
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

FIXTURES_RAW      = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "raw"      / "scheduler" / "v1"
FIXTURES_EXPECTED = pathlib.Path(__file__).parent.parent.parent / "fixtures" / "expected" / "scheduler" / "v1"


class TestJobDataclass(unittest.TestCase):
    """Canonical Job model: validation, field contract, and fixture alignment."""

    def _import_job(self):
        from domain.scheduler.core.job import Job
        return Job

    def test_job_creates_with_valid_fields(self):
        Job = self._import_job()
        job = Job(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="backup",
            command="tar -czf /tmp/backup.tar.gz /data",
            cron_expression="0 2 * * *",
            created_at="2026-03-28T00:00:00+00:00",
        )
        self.assertEqual(job.id, "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(job.name, "backup")
        self.assertEqual(job.command, "tar -czf /tmp/backup.tar.gz /data")
        self.assertEqual(job.cron_expression, "0 2 * * *")
        self.assertEqual(job.created_at, "2026-03-28T00:00:00+00:00")

    def test_job_raises_on_empty_name(self):
        Job = self._import_job()
        with self.assertRaises(ValueError):
            Job(
                id="abc",
                name="",
                command="echo hi",
                cron_expression="* * * * *",
                created_at="2026-03-28T00:00:00+00:00",
            )

    def test_job_raises_on_empty_command(self):
        Job = self._import_job()
        with self.assertRaises(ValueError):
            Job(
                id="abc",
                name="myjob",
                command="",
                cron_expression="* * * * *",
                created_at="2026-03-28T00:00:00+00:00",
            )

    def test_job_raises_on_empty_cron_expression(self):
        Job = self._import_job()
        with self.assertRaises(ValueError):
            Job(
                id="abc",
                name="myjob",
                command="echo hi",
                cron_expression="",
                created_at="2026-03-28T00:00:00+00:00",
            )

    def test_job_raises_on_empty_id(self):
        Job = self._import_job()
        with self.assertRaises(ValueError):
            Job(
                id="",
                name="myjob",
                command="echo hi",
                cron_expression="* * * * *",
                created_at="2026-03-28T00:00:00+00:00",
            )

    def test_raw_fixture_contains_expected_create_fields(self):
        """Raw fixture must contain the fields the adaptor will translate."""
        with open(FIXTURES_RAW / "job.create.success.0.0.1.json") as f:
            raw = json.load(f)
        self.assertIn("name", raw)
        self.assertIn("command", raw)
        self.assertIn("cron_expression", raw)

    def test_expected_fixture_matches_canonical_job_shape(self):
        """Expected fixture must align with all Job dataclass fields."""
        with open(FIXTURES_EXPECTED / "job.create.success.0.0.1.json") as f:
            expected = json.load(f)
        self.assertIn("id", expected)
        self.assertIn("name", expected)
        self.assertIn("command", expected)
        self.assertIn("cron_expression", expected)
        self.assertIn("created_at", expected)

    def test_canonical_job_fields_match_expected_fixture_values(self):
        """Job dataclass built from raw fixture fields equals expected canonical output."""
        Job = self._import_job()
        with open(FIXTURES_RAW / "job.create.success.0.0.1.json") as f:
            raw = json.load(f)
        with open(FIXTURES_EXPECTED / "job.create.success.0.0.1.json") as f:
            expected = json.load(f)

        job = Job(
            id=expected["id"],
            name=raw["name"],
            command=raw["command"],
            cron_expression=raw["cron_expression"],
            created_at=expected["created_at"],
        )
        self.assertEqual(job.id,              expected["id"])
        self.assertEqual(job.name,            expected["name"])
        self.assertEqual(job.command,         expected["command"])
        self.assertEqual(job.cron_expression, expected["cron_expression"])
        self.assertEqual(job.created_at,      expected["created_at"])

    def test_job_to_dict_returns_all_fields(self):
        Job = self._import_job()
        job = Job(
            id="abc",
            name="x",
            command="echo x",
            cron_expression="* * * * *",
            created_at="2026-03-28T00:00:00+00:00",
        )
        d = job.to_dict()
        self.assertEqual(d["id"],              "abc")
        self.assertEqual(d["name"],            "x")
        self.assertEqual(d["command"],         "echo x")
        self.assertEqual(d["cron_expression"], "* * * * *")
        self.assertEqual(d["created_at"],      "2026-03-28T00:00:00+00:00")


class TestJobRunDataclass(unittest.TestCase):
    """Canonical JobRun model: validation and fixture alignment."""

    def _import_job_run(self):
        from domain.scheduler.core.job_run import JobRun
        return JobRun

    def test_job_run_creates_with_valid_fields(self):
        JobRun = self._import_job_run()
        run = JobRun(
            id="770e8400-e29b-41d4-a716-446655440002",
            job_id="550e8400-e29b-41d4-a716-446655440000",
            triggered_at="2026-03-28T00:05:00+00:00",
            exit_code=0,
            output="",
            trigger_type="manual",
        )
        self.assertEqual(run.job_id,       "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(run.exit_code,    0)
        self.assertEqual(run.trigger_type, "manual")

    def test_job_run_raises_on_invalid_trigger_type(self):
        JobRun = self._import_job_run()
        with self.assertRaises(ValueError):
            JobRun(
                id="abc",
                job_id="def",
                triggered_at="2026-03-28T00:05:00+00:00",
                exit_code=0,
                output="",
                trigger_type="unknown",
            )

    def test_job_run_raises_on_empty_job_id(self):
        JobRun = self._import_job_run()
        with self.assertRaises(ValueError):
            JobRun(
                id="abc",
                job_id="",
                triggered_at="2026-03-28T00:05:00+00:00",
                exit_code=0,
                output="",
                trigger_type="manual",
            )

    def test_raw_trigger_fixture_contains_expected_fields(self):
        with open(FIXTURES_RAW / "job.trigger.success.0.0.1.json") as f:
            raw = json.load(f)
        self.assertIn("job_id", raw)
        self.assertIn("trigger_type", raw)

    def test_expected_trigger_fixture_matches_canonical_job_run_shape(self):
        with open(FIXTURES_EXPECTED / "job.trigger.success.0.0.1.json") as f:
            expected = json.load(f)
        self.assertIn("id", expected)
        self.assertIn("job_id", expected)
        self.assertIn("triggered_at", expected)
        self.assertIn("exit_code", expected)
        self.assertIn("output", expected)
        self.assertIn("trigger_type", expected)

    def test_canonical_job_run_fields_match_expected_fixture_values(self):
        JobRun = self._import_job_run()
        with open(FIXTURES_RAW / "job.trigger.success.0.0.1.json") as f:
            raw = json.load(f)
        with open(FIXTURES_EXPECTED / "job.trigger.success.0.0.1.json") as f:
            expected = json.load(f)

        run = JobRun(
            id=expected["id"],
            job_id=raw["job_id"],
            triggered_at=expected["triggered_at"],
            exit_code=expected["exit_code"],
            output=expected["output"],
            trigger_type=raw["trigger_type"],
        )
        self.assertEqual(run.id,           expected["id"])
        self.assertEqual(run.job_id,       expected["job_id"])
        self.assertEqual(run.triggered_at, expected["triggered_at"])
        self.assertEqual(run.exit_code,    expected["exit_code"])
        self.assertEqual(run.trigger_type, expected["trigger_type"])

    def test_job_run_to_dict_returns_all_fields(self):
        JobRun = self._import_job_run()
        run = JobRun(
            id="abc",
            job_id="def",
            triggered_at="2026-03-28T00:05:00+00:00",
            exit_code=1,
            output="error",
            trigger_type="scheduled",
        )
        d = run.to_dict()
        self.assertEqual(d["id"],           "abc")
        self.assertEqual(d["job_id"],       "def")
        self.assertEqual(d["exit_code"],    1)
        self.assertEqual(d["output"],       "error")
        self.assertEqual(d["trigger_type"], "scheduled")


class TestSchedulerService(unittest.TestCase):
    """SchedulerService business logic: create, list, delete, history, trigger."""

    def _make_service(self):
        from domain.scheduler.core.ports.i_job_repository import IJobRepository
        from domain.scheduler.core.scheduler_service import SchedulerService
        repo = MagicMock(spec=IJobRepository)
        service = SchedulerService(repo=repo)
        return service, repo

    def test_create_job_returns_job_with_generated_id(self):
        service, repo = self._make_service()
        job = service.create_job(
            name="backup",
            command="tar -czf /tmp/backup.tar.gz /data",
            cron_expression="0 2 * * *",
        )
        self.assertIsNotNone(job.id)
        self.assertEqual(job.name,            "backup")
        self.assertEqual(job.command,         "tar -czf /tmp/backup.tar.gz /data")
        self.assertEqual(job.cron_expression, "0 2 * * *")
        repo.save.assert_called_once_with(job)

    def test_create_job_stores_iso_created_at(self):
        service, repo = self._make_service()
        job = service.create_job(name="x", command="echo x", cron_expression="* * * * *")
        # Must be parseable ISO 8601
        datetime.fromisoformat(job.created_at)

    def test_list_jobs_delegates_to_repository(self):
        service, repo = self._make_service()
        repo.find_all.return_value = []
        result = service.list_jobs()
        self.assertEqual(result, [])
        repo.find_all.assert_called_once()

    def test_delete_job_delegates_to_repository(self):
        service, repo = self._make_service()
        repo.delete.return_value = True
        result = service.delete_job("abc")
        self.assertTrue(result)
        repo.delete.assert_called_once_with("abc")

    def test_delete_job_returns_false_when_not_found(self):
        service, repo = self._make_service()
        repo.delete.return_value = False
        result = service.delete_job("missing-id")
        self.assertFalse(result)

    def test_get_run_history_delegates_to_repository(self):
        service, repo = self._make_service()
        repo.find_runs.return_value = []
        result = service.get_run_history("abc")
        self.assertEqual(result, [])
        repo.find_runs.assert_called_once_with("abc")

    def test_trigger_job_raises_value_error_when_job_not_found(self):
        service, repo = self._make_service()
        repo.find_by_id.return_value = None
        with self.assertRaises(ValueError):
            service.trigger_job("missing-id")

    def test_trigger_job_saves_run_and_returns_job_run(self):
        service, repo = self._make_service()
        from domain.scheduler.core.job import Job
        fake_job = Job(
            id="550e8400-e29b-41d4-a716-446655440000",
            name="echo-job",
            command="echo hello",
            cron_expression="* * * * *",
            created_at="2026-03-28T00:00:00+00:00",
        )
        repo.find_by_id.return_value = fake_job

        with patch("subprocess.run") as mock_subproc:
            mock_subproc.return_value = MagicMock(returncode=0, stdout="hello\n", stderr="")
            run = service.trigger_job("550e8400-e29b-41d4-a716-446655440000")

        self.assertEqual(run.job_id,       "550e8400-e29b-41d4-a716-446655440000")
        self.assertEqual(run.exit_code,    0)
        self.assertEqual(run.trigger_type, "manual")
        repo.save_run.assert_called_once_with(run)

    def test_trigger_job_captures_non_zero_exit_code(self):
        service, repo = self._make_service()
        from domain.scheduler.core.job import Job
        fake_job = Job(
            id="aaa",
            name="fail-job",
            command="exit 1",
            cron_expression="* * * * *",
            created_at="2026-03-28T00:00:00+00:00",
        )
        repo.find_by_id.return_value = fake_job

        with patch("subprocess.run") as mock_subproc:
            mock_subproc.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
            run = service.trigger_job("aaa")

        self.assertEqual(run.exit_code, 1)
        self.assertIn("error msg", run.output)


if __name__ == "__main__":
    unittest.main()
