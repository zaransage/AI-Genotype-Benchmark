"""
Tests for domain/scheduler/core — canonical models and commands.

Test contract (ADR 0001, ADR 0004, AI_CONTRACT §1, §5, §6):
- Tests are permanent; never removed.
- Written before implementation.
- One test file per layer.
"""
import json
import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

FIXTURES_RAW      = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "raw",      "scheduler", "v1")
FIXTURES_EXPECTED = os.path.join(os.path.dirname(__file__), "..", "..", "fixtures", "expected", "scheduler", "v1")


def _load(base: str, filename: str) -> dict:
    with open(os.path.join(base, filename)) as fh:
        return json.load(fh)


class TestJobModel(unittest.TestCase):
    """Canonical Job dataclass validation."""

    def setUp(self):
        from domain.scheduler.core.job import Job
        self.Job = Job

    def test_valid_job_is_created(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        exp = _load(FIXTURES_EXPECTED, "scheduler/v1/job.0.0.1.json".split("/")[-1])

        # Assert raw fixture contains required source fields
        self.assertIn("name",            raw)
        self.assertIn("command",         raw)
        self.assertIn("cron_expression", raw)

        job = self.Job(
            id="job-001",
            name=raw["name"],
            command=raw["command"],
            cron_expression=raw["cron_expression"],
            created_at=datetime(2026, 3, 28, tzinfo=timezone.utc),
        )

        # Assert canonical model field values match expected fixture
        self.assertEqual(job.name,            exp["name"])
        self.assertEqual(job.command,         exp["command"])
        self.assertEqual(job.cron_expression, exp["cron_expression"])
        self.assertEqual(job.enabled,         exp["enabled"])

    def test_empty_name_raises(self):
        with self.assertRaises(ValueError):
            self.Job(
                id="x",
                name="",
                command="echo hi",
                cron_expression="* * * * *",
                created_at=datetime.now(timezone.utc),
            )

    def test_empty_command_raises(self):
        with self.assertRaises(ValueError):
            self.Job(
                id="x",
                name="myjob",
                command="",
                cron_expression="* * * * *",
                created_at=datetime.now(timezone.utc),
            )

    def test_invalid_cron_raises(self):
        with self.assertRaises(ValueError):
            self.Job(
                id="x",
                name="myjob",
                command="echo hi",
                cron_expression="not-a-cron",
                created_at=datetime.now(timezone.utc),
            )

    def test_job_has_date_format_constant(self):
        self.assertTrue(hasattr(self.Job, "DATE_FORMAT"))


class TestRunRecordModel(unittest.TestCase):
    """Canonical RunRecord dataclass validation."""

    def setUp(self):
        from domain.scheduler.core.run_record import RunRecord
        self.RunRecord = RunRecord

    def test_valid_run_record_is_created(self):
        raw = _load(FIXTURES_RAW, "trigger_job.0.0.1.json")
        exp = _load(FIXTURES_EXPECTED, "run_record.0.0.1.json")

        # Assert raw fixture contains required source fields
        self.assertIn("job_id", raw)

        rr = self.RunRecord(
            id="rr-001",
            job_id=raw["job_id"],
            triggered_at=datetime(2026, 3, 28, tzinfo=timezone.utc),
            status="success",
            output="",
            duration_s=0.0,
        )

        # Assert canonical model field values
        self.assertEqual(rr.job_id, exp["job_id"])
        self.assertEqual(rr.status, exp["status"])
        self.assertEqual(rr.output, exp["output"])

    def test_invalid_status_raises(self):
        from domain.scheduler.core.run_record import RunRecord
        with self.assertRaises(ValueError):
            RunRecord(
                id="rr-002",
                job_id="job-001",
                triggered_at=datetime.now(timezone.utc),
                status="unknown_status",
                output="",
                duration_s=0.0,
            )


class TestCreateJobCommand(unittest.TestCase):

    def setUp(self):
        from domain.scheduler.core.commands import CreateJobCommand
        from domain.scheduler.ports.i_job_repository import IJobRepository
        self.CreateJobCommand = CreateJobCommand
        self.mock_repo = MagicMock(spec=IJobRepository)

    def test_creates_and_saves_job(self):
        raw = _load(FIXTURES_RAW, "create_job.0.0.1.json")
        cmd = self.CreateJobCommand(repo=self.mock_repo)
        job = cmd.execute(
            name=raw["name"],
            command=raw["command"],
            cron_expression=raw["cron_expression"],
        )
        self.mock_repo.save.assert_called_once_with(job)
        self.assertEqual(job.name, raw["name"])
        self.assertEqual(job.command, raw["command"])
        self.assertEqual(job.cron_expression, raw["cron_expression"])
        self.assertTrue(job.id)

    def test_invalid_cron_raises_before_save(self):
        cmd = self.CreateJobCommand(repo=self.mock_repo)
        with self.assertRaises(ValueError):
            cmd.execute(name="x", command="echo hi", cron_expression="bad")
        self.mock_repo.save.assert_not_called()


class TestListJobsCommand(unittest.TestCase):

    def setUp(self):
        from domain.scheduler.core.commands import ListJobsCommand
        from domain.scheduler.ports.i_job_repository import IJobRepository
        self.ListJobsCommand = ListJobsCommand
        self.mock_repo = MagicMock(spec=IJobRepository)

    def test_returns_all_jobs_from_repo(self):
        sentinel = [MagicMock(), MagicMock()]
        self.mock_repo.find_all.return_value = sentinel
        cmd = self.ListJobsCommand(repo=self.mock_repo)
        result = cmd.execute()
        self.mock_repo.find_all.assert_called_once()
        self.assertEqual(result, sentinel)


class TestDeleteJobCommand(unittest.TestCase):

    def setUp(self):
        from domain.scheduler.core.commands import DeleteJobCommand
        from domain.scheduler.ports.i_job_repository import IJobRepository
        self.DeleteJobCommand = DeleteJobCommand
        self.mock_repo = MagicMock(spec=IJobRepository)

    def test_deletes_existing_job(self):
        from domain.scheduler.core.job import Job
        job = Job(
            id="job-del-001",
            name="to-delete",
            command="echo bye",
            cron_expression="* * * * *",
            created_at=datetime.now(timezone.utc),
        )
        self.mock_repo.find_by_id.return_value = job
        cmd = self.DeleteJobCommand(repo=self.mock_repo)
        cmd.execute(job_id="job-del-001")
        self.mock_repo.delete.assert_called_once_with("job-del-001")

    def test_raises_when_job_not_found(self):
        self.mock_repo.find_by_id.return_value = None
        cmd = self.DeleteJobCommand(repo=self.mock_repo)
        with self.assertRaises(KeyError):
            cmd.execute(job_id="nonexistent")
        self.mock_repo.delete.assert_not_called()


class TestTriggerJobCommand(unittest.TestCase):

    def setUp(self):
        from domain.scheduler.core.commands import TriggerJobCommand
        from domain.scheduler.ports.i_job_repository import IJobRepository
        self.TriggerJobCommand = TriggerJobCommand
        self.mock_repo = MagicMock(spec=IJobRepository)

    def test_trigger_creates_run_record(self):
        from domain.scheduler.core.job import Job
        job = Job(
            id="job-trigger-001",
            name="trigger-test",
            command="echo triggered",
            cron_expression="* * * * *",
            created_at=datetime.now(timezone.utc),
        )
        self.mock_repo.find_by_id.return_value = job
        cmd = self.TriggerJobCommand(repo=self.mock_repo)
        rr = cmd.execute(job_id="job-trigger-001")
        self.mock_repo.save_run_record.assert_called_once_with(rr)
        self.assertEqual(rr.job_id, "job-trigger-001")
        self.assertIn(rr.status, ("success", "failure"))

    def test_trigger_raises_when_job_not_found(self):
        self.mock_repo.find_by_id.return_value = None
        cmd = self.TriggerJobCommand(repo=self.mock_repo)
        with self.assertRaises(KeyError):
            cmd.execute(job_id="ghost")


class TestGetRunHistoryCommand(unittest.TestCase):

    def setUp(self):
        from domain.scheduler.core.commands import GetRunHistoryCommand
        from domain.scheduler.ports.i_job_repository import IJobRepository
        self.GetRunHistoryCommand = GetRunHistoryCommand
        self.mock_repo = MagicMock(spec=IJobRepository)

    def test_returns_run_records_for_job(self):
        from domain.scheduler.core.job import Job
        job = Job(
            id="job-hist-001",
            name="hist-test",
            command="echo history",
            cron_expression="* * * * *",
            created_at=datetime.now(timezone.utc),
        )
        sentinel = [MagicMock(), MagicMock()]
        self.mock_repo.find_by_id.return_value = job
        self.mock_repo.find_run_records.return_value = sentinel
        cmd = self.GetRunHistoryCommand(repo=self.mock_repo)
        result = cmd.execute(job_id="job-hist-001")
        self.mock_repo.find_run_records.assert_called_once_with("job-hist-001")
        self.assertEqual(result, sentinel)

    def test_raises_when_job_not_found(self):
        self.mock_repo.find_by_id.return_value = None
        cmd = self.GetRunHistoryCommand(repo=self.mock_repo)
        with self.assertRaises(KeyError):
            cmd.execute(job_id="ghost")


if __name__ == "__main__":
    unittest.main()
