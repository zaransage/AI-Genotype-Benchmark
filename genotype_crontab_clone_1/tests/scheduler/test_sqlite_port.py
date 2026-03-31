"""
tests/scheduler/test_sqlite_port.py

Unit tests for SqliteJobRepository (outbound port).
Covers: CRUD operations, run-record persistence, ordering,
and survival across a reconnect (simulated restart).
"""
from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timezone

from domain.scheduler.core.job import Job, RunRecord
from domain.scheduler.core.ports.sqlite_job_repository import SqliteJobRepository


def _make_job(suffix: str = "a") -> Job:
    return Job(
        id              = f"job-{suffix}",
        name            = f"Test Job {suffix}",
        command         = "echo hello",
        cron_expression = "* * * * *",
        created_at      = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        enabled         = True,
    )


def _make_run(job_id: str, suffix: str = "1", status: str = "success") -> RunRecord:
    # Use suffix as microsecond offset so ordering tests work for numeric suffixes
    # and non-numeric suffixes still produce a valid datetime.
    try:
        micro = int(suffix) % 1_000_000
    except ValueError:
        micro = abs(hash(suffix)) % 1_000_000
    return RunRecord(
        id           = f"run-{suffix}",
        job_id       = job_id,
        triggered_at = datetime(2026, 1, 1, 12, 0, 0, microsecond=micro, tzinfo=timezone.utc),
        status       = status,
        output       = f"output-{suffix}",
    )


class TestSqliteJobRepositoryCrud(unittest.TestCase):
    """Basic create, read, update, delete operations."""

    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self._repo = SqliteJobRepository(self._tmp.name)

    def tearDown(self) -> None:
        os.unlink(self._tmp.name)

    def test_save_and_get_roundtrip(self) -> None:
        job = _make_job("x")
        self._repo.save(job)
        result = self._repo.get(job.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.id,              job.id)
        self.assertEqual(result.name,            job.name)
        self.assertEqual(result.command,         job.command)
        self.assertEqual(result.cron_expression, job.cron_expression)
        self.assertEqual(result.enabled,         job.enabled)
        # Timestamp must survive roundtrip (timezone-aware)
        self.assertEqual(result.created_at, job.created_at)

    def test_get_returns_none_for_missing_id(self) -> None:
        self.assertIsNone(self._repo.get("does-not-exist"))

    def test_save_upsert_updates_existing_job(self) -> None:
        job = _make_job("u")
        self._repo.save(job)
        updated = Job(
            id              = job.id,
            name            = "Updated Name",
            command         = "echo updated",
            cron_expression = "0 * * * *",
            created_at      = job.created_at,
            enabled         = False,
        )
        self._repo.save(updated)
        result = self._repo.get(job.id)
        self.assertEqual(result.name,    "Updated Name")
        self.assertEqual(result.enabled, False)

    def test_list_returns_all_saved_jobs(self) -> None:
        job_a = _make_job("a")
        job_b = _make_job("b")
        self._repo.save(job_a)
        self._repo.save(job_b)
        jobs = self._repo.list()
        ids = {j.id for j in jobs}
        self.assertIn(job_a.id, ids)
        self.assertIn(job_b.id, ids)
        self.assertEqual(len(jobs), 2)

    def test_list_returns_empty_when_no_jobs(self) -> None:
        self.assertEqual(self._repo.list(), [])

    def test_delete_removes_job(self) -> None:
        job = _make_job("d")
        self._repo.save(job)
        self._repo.delete(job.id)
        self.assertIsNone(self._repo.get(job.id))

    def test_delete_is_noop_for_missing_id(self) -> None:
        # Must not raise
        self._repo.delete("ghost-id")

    def test_delete_also_removes_associated_runs(self) -> None:
        job = _make_job("cascade")
        run = _make_run(job.id, "1")
        self._repo.save(job)
        self._repo.save_run(run)
        self._repo.delete(job.id)
        # run_records CASCADE deletes with foreign key
        runs = self._repo.get_runs(job.id)
        self.assertEqual(runs, [])


class TestSqliteJobRepositoryRunRecords(unittest.TestCase):
    """Run-record storage and retrieval."""

    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self._repo = SqliteJobRepository(self._tmp.name)
        self._job = _make_job("r")
        self._repo.save(self._job)

    def tearDown(self) -> None:
        os.unlink(self._tmp.name)

    def test_save_run_and_get_runs_roundtrip(self) -> None:
        run = _make_run(self._job.id, "1")
        self._repo.save_run(run)
        runs = self._repo.get_runs(self._job.id)
        self.assertEqual(len(runs), 1)
        r = runs[0]
        self.assertEqual(r.id,     run.id)
        self.assertEqual(r.job_id, run.job_id)
        self.assertEqual(r.status, run.status)
        self.assertEqual(r.output, run.output)
        self.assertEqual(r.triggered_at, run.triggered_at)

    def test_get_runs_returns_empty_for_unknown_job(self) -> None:
        self.assertEqual(self._repo.get_runs("no-such-job"), [])

    def test_multiple_runs_ordered_by_triggered_at(self) -> None:
        # Insert in reverse order; expect ascending order back
        for i in ("3", "1", "2"):
            self._repo.save_run(_make_run(self._job.id, i))
        runs = self._repo.get_runs(self._job.id)
        self.assertEqual([r.id for r in runs], ["run-1", "run-2", "run-3"])

    def test_run_status_failure_persisted(self) -> None:
        run = _make_run(self._job.id, "f", status="failure")
        self._repo.save_run(run)
        result = self._repo.get_runs(self._job.id)[0]
        self.assertEqual(result.status, "failure")

    def test_duplicate_run_id_is_ignored(self) -> None:
        run = _make_run(self._job.id, "dup")
        self._repo.save_run(run)
        self._repo.save_run(run)  # second insert must not raise
        self.assertEqual(len(self._repo.get_runs(self._job.id)), 1)


class TestSqliteJobRepositoryPersistence(unittest.TestCase):
    """Data survives closing and re-opening the connection (restart simulation)."""

    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()

    def tearDown(self) -> None:
        os.unlink(self._tmp.name)

    def test_jobs_survive_reconnect(self) -> None:
        repo1 = SqliteJobRepository(self._tmp.name)
        job = _make_job("persist")
        repo1.save(job)
        repo1._conn.close()

        repo2 = SqliteJobRepository(self._tmp.name)
        result = repo2.get(job.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, job.name)

    def test_runs_survive_reconnect(self) -> None:
        repo1 = SqliteJobRepository(self._tmp.name)
        job = _make_job("persrun")
        run = _make_run(job.id, "99")
        repo1.save(job)
        repo1.save_run(run)
        repo1._conn.close()

        repo2 = SqliteJobRepository(self._tmp.name)
        runs = repo2.get_runs(job.id)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].output, run.output)


if __name__ == "__main__":
    unittest.main()
