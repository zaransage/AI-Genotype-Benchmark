"""
tests/scheduler/test_core.py

Tests for canonical domain models: Job and RunRecord.
Covers:
  - Valid construction
  - __post_init__ validation (bad input raises ValueError)
  - Fixture integrity: raw fixture fields map to canonical model fields
"""
import json
import unittest
from pathlib import Path
from datetime import datetime, timezone

FIXTURES_RAW      = Path(__file__).parent.parent.parent / "fixtures" / "raw"      / "scheduler" / "v1"
FIXTURES_EXPECTED = Path(__file__).parent.parent.parent / "fixtures" / "expected" / "scheduler" / "v1"


class TestJobModel(unittest.TestCase):
    """Job dataclass — construction and validation."""

    def _make_job(self, **overrides):
        from domain.scheduler.core.job import Job
        defaults = {
            "id":              "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "name":            "cleanup-logs",
            "command":         "echo hello",
            "cron_expression": "0 2 * * *",
            "created_at":      datetime(2026, 3, 28, 20, 0, 0, tzinfo=timezone.utc),
            "enabled":         True,
        }
        defaults.update(overrides)
        return Job(**defaults)

    def test_valid_job_construction(self):
        from domain.scheduler.core.job import Job
        job = self._make_job()
        self.assertIsInstance(job, Job)
        self.assertEqual(job.name, "cleanup-logs")
        self.assertEqual(job.command, "echo hello")
        self.assertEqual(job.cron_expression, "0 2 * * *")
        self.assertTrue(job.enabled)

    def test_blank_name_raises(self):
        with self.assertRaises(ValueError):
            self._make_job(name="")

    def test_blank_command_raises(self):
        with self.assertRaises(ValueError):
            self._make_job(command="")

    def test_invalid_cron_expression_raises(self):
        with self.assertRaises(ValueError):
            self._make_job(cron_expression="not-a-cron")

    def test_valid_cron_five_fields(self):
        job = self._make_job(cron_expression="*/5 * * * *")
        self.assertEqual(job.cron_expression, "*/5 * * * *")

    def test_raw_fixture_create_request_has_required_fields(self):
        """Raw fixture must contain the fields the adaptor will read."""
        with open(FIXTURES_RAW / "job.create.request.0.0.1.json") as f:
            raw = json.load(f)
        self.assertIn("name",            raw)
        self.assertIn("command",         raw)
        self.assertIn("cron_expression", raw)

    def test_raw_fixture_create_response_maps_to_canonical_fields(self):
        """Raw create response fixture must carry all canonical Job fields."""
        with open(FIXTURES_RAW / "job.create.response.0.0.1.json") as f:
            raw = json.load(f)
        self.assertIn("id",              raw)
        self.assertIn("name",            raw)
        self.assertIn("command",         raw)
        self.assertIn("cron_expression", raw)
        self.assertIn("created_at",      raw)
        self.assertIn("enabled",         raw)

    def test_expected_fixture_create_canonical_fields(self):
        """Expected fixture must match canonical model field values."""
        with open(FIXTURES_EXPECTED / "job.create.0.0.1.json") as f:
            expected = json.load(f)
        job = self._make_job(
            name            = expected["name"],
            command         = expected["command"],
            cron_expression = expected["cron_expression"],
        )
        self.assertEqual(job.name,            expected["name"])
        self.assertEqual(job.command,         expected["command"])
        self.assertEqual(job.cron_expression, expected["cron_expression"])
        self.assertEqual(job.enabled,         expected["enabled"])

    def test_raw_fixture_list_response_has_two_jobs(self):
        with open(FIXTURES_RAW / "job.list.response.0.0.1.json") as f:
            raw = json.load(f)
        self.assertEqual(len(raw), 2)
        for item in raw:
            self.assertIn("id",              item)
            self.assertIn("name",            item)
            self.assertIn("cron_expression", item)


class TestRunRecordModel(unittest.TestCase):
    """RunRecord dataclass — construction and validation."""

    def _make_run_record(self, **overrides):
        from domain.scheduler.core.job import RunRecord
        defaults = {
            "id":           "aab85f64-5717-4562-b3fc-2c963f66afa6",
            "job_id":       "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "triggered_at": datetime(2026, 3, 28, 20, 5, 0, tzinfo=timezone.utc),
            "status":       "success",
            "output":       "Deleted 3 files.",
        }
        defaults.update(overrides)
        return RunRecord(**defaults)

    def test_valid_run_record_construction(self):
        from domain.scheduler.core.job import RunRecord
        record = self._make_run_record()
        self.assertIsInstance(record, RunRecord)
        self.assertEqual(record.status, "success")
        self.assertEqual(record.output, "Deleted 3 files.")

    def test_invalid_status_raises(self):
        with self.assertRaises(ValueError):
            self._make_run_record(status="unknown")

    def test_blank_job_id_raises(self):
        with self.assertRaises(ValueError):
            self._make_run_record(job_id="")

    def test_raw_fixture_run_history_has_required_fields(self):
        """Raw run-history fixture must carry all canonical RunRecord fields."""
        with open(FIXTURES_RAW / "job.run_history.response.0.0.1.json") as f:
            raw = json.load(f)
        self.assertGreater(len(raw), 0)
        for item in raw:
            self.assertIn("id",           item)
            self.assertIn("job_id",       item)
            self.assertIn("triggered_at", item)
            self.assertIn("status",       item)
            self.assertIn("output",       item)

    def test_expected_fixture_run_history_canonical_fields(self):
        """Expected fixture canonical fields match RunRecord after construction."""
        with open(FIXTURES_EXPECTED / "job.run_history.0.0.1.json") as f:
            expected = json.load(f)
        record = self._make_run_record(
            job_id = expected[0]["job_id"],
            status = expected[0]["status"],
            output = expected[0]["output"],
        )
        self.assertEqual(record.job_id,  expected[0]["job_id"])
        self.assertEqual(record.status,  expected[0]["status"])
        self.assertEqual(record.output,  expected[0]["output"])


if __name__ == "__main__":
    unittest.main()
