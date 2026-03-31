"""
tests/scheduler/test_sqlite_ports.py

Tests for the SqliteJobRepository outbound port implementation.
Validates contract compliance with IJobRepository using a temporary on-disk database.
Each test method receives a fresh, isolated database (via setUp).
"""

import os
import tempfile
import unittest

from domain.scheduler.core.job                            import Job
from domain.scheduler.core.job_run                        import JobRun
from domain.scheduler.core.ports.sqlite_job_repository    import SqliteJobRepository
from domain.scheduler.core.ports.i_job_repository         import IJobRepository


def _make_job(job_id: str = "abc", name: str = "test") -> Job:
    return Job(
        id=job_id,
        name=name,
        command="echo test",
        cron_expression="* * * * *",
        created_at="2026-03-28T00:00:00+00:00",
    )


def _make_run(run_id: str, job_id: str) -> JobRun:
    return JobRun(
        id=run_id,
        job_id=job_id,
        triggered_at="2026-03-28T00:05:00+00:00",
        exit_code=0,
        output="",
        trigger_type="manual",
    )


class TestSqliteJobRepository(unittest.TestCase):

    def setUp(self):
        fd, self._db_path = tempfile.mkstemp(suffix=".sqlite3")
        os.close(fd)
        self.repo = SqliteJobRepository(db_path=self._db_path)

    def tearDown(self):
        os.unlink(self._db_path)

    # -- interface compliance ---------------------------------------------------

    def test_repository_is_instance_of_i_job_repository(self):
        self.assertIsInstance(self.repo, IJobRepository)

    # -- save / find_by_id ------------------------------------------------------

    def test_save_and_find_by_id_returns_saved_job(self):
        job = _make_job("id-1")
        self.repo.save(job)
        result = self.repo.find_by_id("id-1")
        self.assertIsNotNone(result)
        self.assertEqual(result.id,              "id-1")
        self.assertEqual(result.name,            "test")
        self.assertEqual(result.command,         "echo test")
        self.assertEqual(result.cron_expression, "* * * * *")
        self.assertEqual(result.created_at,      "2026-03-28T00:00:00+00:00")

    def test_find_by_id_returns_none_for_unknown_id(self):
        result = self.repo.find_by_id("does-not-exist")
        self.assertIsNone(result)

    def test_save_overwrites_existing_job_with_same_id(self):
        self.repo.save(_make_job("id-1", name="original"))
        self.repo.save(_make_job("id-1", name="updated"))
        result = self.repo.find_by_id("id-1")
        self.assertEqual(result.name, "updated")

    # -- find_all ----------------------------------------------------------------

    def test_find_all_returns_empty_list_when_no_jobs(self):
        self.assertEqual(self.repo.find_all(), [])

    def test_find_all_returns_all_saved_jobs(self):
        self.repo.save(_make_job("id-1", "job-a"))
        self.repo.save(_make_job("id-2", "job-b"))
        result = self.repo.find_all()
        self.assertEqual(len(result), 2)
        ids = {j.id for j in result}
        self.assertIn("id-1", ids)
        self.assertIn("id-2", ids)

    # -- delete ------------------------------------------------------------------

    def test_delete_returns_true_for_existing_job(self):
        self.repo.save(_make_job("id-1"))
        self.assertTrue(self.repo.delete("id-1"))

    def test_delete_removes_job_from_store(self):
        self.repo.save(_make_job("id-1"))
        self.repo.delete("id-1")
        self.assertIsNone(self.repo.find_by_id("id-1"))

    def test_delete_returns_false_for_missing_job(self):
        self.assertFalse(self.repo.delete("does-not-exist"))

    def test_delete_does_not_affect_other_jobs(self):
        self.repo.save(_make_job("id-1"))
        self.repo.save(_make_job("id-2"))
        self.repo.delete("id-1")
        self.assertIsNotNone(self.repo.find_by_id("id-2"))

    # -- save_run / find_runs ---------------------------------------------------

    def test_save_run_and_find_runs_returns_saved_run(self):
        self.repo.save(_make_job("job-1"))
        run = _make_run("run-1", "job-1")
        self.repo.save_run(run)
        runs = self.repo.find_runs("job-1")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].id,           "run-1")
        self.assertEqual(runs[0].job_id,       "job-1")
        self.assertEqual(runs[0].exit_code,    0)
        self.assertEqual(runs[0].trigger_type, "manual")

    def test_find_runs_returns_empty_list_for_unknown_job(self):
        self.assertEqual(self.repo.find_runs("unknown-job"), [])

    def test_find_runs_returns_all_runs_for_job(self):
        self.repo.save(_make_job("job-1"))
        self.repo.save_run(_make_run("run-1", "job-1"))
        self.repo.save_run(_make_run("run-2", "job-1"))
        runs = self.repo.find_runs("job-1")
        self.assertEqual(len(runs), 2)

    def test_find_runs_isolates_runs_by_job_id(self):
        self.repo.save(_make_job("job-1"))
        self.repo.save(_make_job("job-2"))
        self.repo.save_run(_make_run("run-1", "job-1"))
        self.repo.save_run(_make_run("run-2", "job-2"))
        self.assertEqual(len(self.repo.find_runs("job-1")), 1)
        self.assertEqual(len(self.repo.find_runs("job-2")), 1)

    def test_save_run_overwrites_run_with_same_id(self):
        self.repo.save(_make_job("job-1"))
        run_v1 = JobRun(
            id="run-1",
            job_id="job-1",
            triggered_at="2026-03-28T00:05:00+00:00",
            exit_code=0,
            output="first",
            trigger_type="manual",
        )
        run_v2 = JobRun(
            id="run-1",
            job_id="job-1",
            triggered_at="2026-03-28T00:06:00+00:00",
            exit_code=1,
            output="second",
            trigger_type="manual",
        )
        self.repo.save_run(run_v1)
        self.repo.save_run(run_v2)
        runs = self.repo.find_runs("job-1")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].output, "second")

    # -- persistence across instances -------------------------------------------

    def test_data_persists_across_new_repository_instance(self):
        """SQLite must survive a process restart (new instance, same db_path)."""
        self.repo.save(_make_job("persist-id", name="persistent"))
        self.repo.save_run(_make_run("run-p", "persist-id"))

        fresh = SqliteJobRepository(db_path=self._db_path)
        job = fresh.find_by_id("persist-id")
        self.assertIsNotNone(job)
        self.assertEqual(job.name, "persistent")

        runs = fresh.find_runs("persist-id")
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].id, "run-p")


if __name__ == "__main__":
    unittest.main()
