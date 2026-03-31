"""
tests/scheduler/test_ports.py

Tests for outbound port implementations:
  - InMemoryJobRepository: save, get, list, delete, save_run, get_runs
  - SubprocessJobExecutor: execute returns RunRecord with correct fields
"""
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

FIXTURES_RAW = Path(__file__).parent.parent.parent / "fixtures" / "raw" / "scheduler" / "v1"


def _utcnow() -> datetime:
    return datetime(2026, 3, 28, 20, 0, 0, tzinfo=timezone.utc)


class TestInMemoryJobRepository(unittest.TestCase):
    """InMemoryJobRepository — full CRUD + run record storage."""

    def setUp(self):
        from domain.scheduler.core.ports.in_memory_job_repository import InMemoryJobRepository
        from domain.scheduler.core.job import Job, RunRecord
        self.repo = InMemoryJobRepository()
        self.Job       = Job
        self.RunRecord = RunRecord

    def _make_job(self, name="test-job", cron="0 * * * *"):
        return self.Job(
            id              = "job-001",
            name            = name,
            command         = "echo test",
            cron_expression = cron,
            created_at      = _utcnow(),
            enabled         = True,
        )

    def test_save_and_get(self):
        job = self._make_job()
        self.repo.save(job)
        retrieved = self.repo.get("job-001")
        self.assertEqual(retrieved.id,   "job-001")
        self.assertEqual(retrieved.name, "test-job")

    def test_get_missing_returns_none(self):
        result = self.repo.get("does-not-exist")
        self.assertIsNone(result)

    def test_list_returns_all_saved_jobs(self):
        self.repo.save(self._make_job(name="job-a"))
        second = self.Job(
            id              = "job-002",
            name            = "job-b",
            command         = "echo b",
            cron_expression = "*/5 * * * *",
            created_at      = _utcnow(),
            enabled         = True,
        )
        self.repo.save(second)
        all_jobs = self.repo.list()
        self.assertEqual(len(all_jobs), 2)
        names = {j.name for j in all_jobs}
        self.assertIn("job-a", names)
        self.assertIn("job-b", names)

    def test_list_empty_returns_empty_list(self):
        self.assertEqual(self.repo.list(), [])

    def test_delete_removes_job(self):
        job = self._make_job()
        self.repo.save(job)
        self.repo.delete("job-001")
        self.assertIsNone(self.repo.get("job-001"))

    def test_delete_nonexistent_is_noop(self):
        self.repo.delete("ghost")  # must not raise

    def test_save_run_and_get_runs(self):
        job = self._make_job()
        self.repo.save(job)
        run = self.RunRecord(
            id           = "run-001",
            job_id       = "job-001",
            triggered_at = _utcnow(),
            status       = "success",
            output       = "ok",
        )
        self.repo.save_run(run)
        runs = self.repo.get_runs("job-001")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].id,     "run-001")
        self.assertEqual(runs[0].status, "success")

    def test_get_runs_for_unknown_job_returns_empty(self):
        self.assertEqual(self.repo.get_runs("unknown"), [])

    def test_multiple_runs_ordered_by_insertion(self):
        job = self._make_job()
        self.repo.save(job)
        for i in range(3):
            self.repo.save_run(self.RunRecord(
                id           = f"run-{i:03d}",
                job_id       = "job-001",
                triggered_at = _utcnow(),
                status       = "success",
                output       = f"run {i}",
            ))
        runs = self.repo.get_runs("job-001")
        self.assertEqual(len(runs), 3)
        self.assertEqual(runs[0].id, "run-000")
        self.assertEqual(runs[2].id, "run-002")

    def test_raw_fixture_list_response_maps_correctly(self):
        """
        Fixture integrity: raw list fixture records must have fields that
        can populate InMemoryJobRepository and be retrieved intact.
        """
        with open(FIXTURES_RAW / "job.list.response.0.0.1.json") as f:
            raw = json.load(f)
        for item in raw:
            job = self.Job(
                id              = item["id"],
                name            = item["name"],
                command         = item["command"],
                cron_expression = item["cron_expression"],
                created_at      = datetime.fromisoformat(
                    item["created_at"].replace("Z", "+00:00")
                ),
                enabled         = item["enabled"],
            )
            self.repo.save(job)
        all_jobs = self.repo.list()
        self.assertEqual(len(all_jobs), len(raw))


class TestSubprocessJobExecutor(unittest.TestCase):
    """SubprocessJobExecutor — execute() produces a correct RunRecord."""

    def setUp(self):
        from domain.scheduler.core.ports.subprocess_job_executor import SubprocessJobExecutor
        from domain.scheduler.core.job import RunRecord
        self.executor  = SubprocessJobExecutor()
        self.RunRecord = RunRecord

    def test_successful_command_returns_success_status(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = "hello"
        mock_result.stderr     = ""
        with patch("subprocess.run", return_value=mock_result):
            record = self.executor.execute(job_id="job-1", command="echo hello")
        self.assertIsInstance(record, self.RunRecord)
        self.assertEqual(record.status,  "success")
        self.assertEqual(record.output,  "hello")
        self.assertEqual(record.job_id,  "job-1")

    def test_failed_command_returns_failure_status(self):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout     = ""
        mock_result.stderr     = "error occurred"
        with patch("subprocess.run", return_value=mock_result):
            record = self.executor.execute(job_id="job-1", command="false")
        self.assertEqual(record.status, "failure")
        self.assertIn("error occurred", record.output)

    def test_run_record_has_job_id_set(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = "done"
        mock_result.stderr     = ""
        with patch("subprocess.run", return_value=mock_result):
            record = self.executor.execute(job_id="job-xyz", command="echo done")
        self.assertEqual(record.job_id, "job-xyz")

    def test_run_record_has_triggered_at_set(self):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout     = ""
        mock_result.stderr     = ""
        with patch("subprocess.run", return_value=mock_result):
            record = self.executor.execute(job_id="job-1", command="true")
        self.assertIsNotNone(record.triggered_at)
        self.assertIsInstance(record.triggered_at, datetime)


if __name__ == "__main__":
    unittest.main()
