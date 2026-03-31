"""
Tests for domain/scheduler/ports — IJobRepository and InMemoryJobRepository.

Test contract (ADR 0001, ADR 0004, AI_CONTRACT §1, §5, §6):
- Tests are permanent; never removed.
- Written before implementation.
"""
import unittest
from datetime import datetime, timezone


class TestInMemoryJobRepository(unittest.TestCase):

    def setUp(self):
        from domain.scheduler.ports.in_memory_job_repository import InMemoryJobRepository
        from domain.scheduler.core.job import Job
        from domain.scheduler.core.run_record import RunRecord
        self.repo = InMemoryJobRepository()
        self.Job = Job
        self.RunRecord = RunRecord

    def _make_job(self, job_id="j1", name="test-job"):
        return self.Job(
            id=job_id,
            name=name,
            command="echo hi",
            cron_expression="* * * * *",
            created_at=datetime(2026, 3, 28, tzinfo=timezone.utc),
        )

    def _make_rr(self, rr_id="rr1", job_id="j1"):
        return self.RunRecord(
            id=rr_id,
            job_id=job_id,
            triggered_at=datetime(2026, 3, 28, tzinfo=timezone.utc),
            status="success",
            output="ok",
            duration_s=0.1,
        )

    def test_save_and_find_by_id(self):
        job = self._make_job()
        self.repo.save(job)
        found = self.repo.find_by_id("j1")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "test-job")

    def test_find_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repo.find_by_id("nonexistent"))

    def test_find_all_returns_all_saved_jobs(self):
        self.repo.save(self._make_job("j1", "job-one"))
        self.repo.save(self._make_job("j2", "job-two"))
        all_jobs = self.repo.find_all()
        self.assertEqual(len(all_jobs), 2)
        names = {j.name for j in all_jobs}
        self.assertIn("job-one", names)
        self.assertIn("job-two", names)

    def test_delete_removes_job(self):
        job = self._make_job()
        self.repo.save(job)
        self.repo.delete("j1")
        self.assertIsNone(self.repo.find_by_id("j1"))

    def test_delete_nonexistent_raises(self):
        with self.assertRaises(KeyError):
            self.repo.delete("ghost")

    def test_save_run_record_and_find_run_records(self):
        job = self._make_job()
        self.repo.save(job)
        rr1 = self._make_rr("rr1", "j1")
        rr2 = self._make_rr("rr2", "j1")
        self.repo.save_run_record(rr1)
        self.repo.save_run_record(rr2)
        records = self.repo.find_run_records("j1")
        self.assertEqual(len(records), 2)
        ids = {r.id for r in records}
        self.assertIn("rr1", ids)
        self.assertIn("rr2", ids)

    def test_find_run_records_empty_when_none(self):
        job = self._make_job()
        self.repo.save(job)
        self.assertEqual(self.repo.find_run_records("j1"), [])

    def test_find_run_records_only_returns_records_for_given_job(self):
        self.repo.save(self._make_job("j1"))
        self.repo.save(self._make_job("j2"))
        self.repo.save_run_record(self._make_rr("rr1", "j1"))
        self.repo.save_run_record(self._make_rr("rr2", "j2"))
        j1_records = self.repo.find_run_records("j1")
        self.assertEqual(len(j1_records), 1)
        self.assertEqual(j1_records[0].job_id, "j1")

    def test_implements_interface(self):
        from domain.scheduler.ports.i_job_repository import IJobRepository
        from domain.scheduler.ports.in_memory_job_repository import InMemoryJobRepository
        self.assertIsInstance(self.repo, IJobRepository)


class TestSQLiteJobRepository(unittest.TestCase):
    """Mirrors TestInMemoryJobRepository contracts against the SQLite implementation."""

    def setUp(self):
        import tempfile
        import os
        from domain.scheduler.ports.sqlite_job_repository import SQLiteJobRepository
        from domain.scheduler.core.job import Job
        from domain.scheduler.core.run_record import RunRecord
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._tmp.close()
        self.repo = SQLiteJobRepository(db_path=self._tmp.name)
        self.Job = Job
        self.RunRecord = RunRecord

    def tearDown(self):
        import os
        os.unlink(self._tmp.name)

    def _make_job(self, job_id="j1", name="test-job"):
        return self.Job(
            id=job_id,
            name=name,
            command="echo hi",
            cron_expression="* * * * *",
            created_at=datetime(2026, 3, 28, tzinfo=timezone.utc),
        )

    def _make_rr(self, rr_id="rr1", job_id="j1"):
        return self.RunRecord(
            id=rr_id,
            job_id=job_id,
            triggered_at=datetime(2026, 3, 28, tzinfo=timezone.utc),
            status="success",
            output="ok",
            duration_s=0.1,
        )

    def test_save_and_find_by_id(self):
        job = self._make_job()
        self.repo.save(job)
        found = self.repo.find_by_id("j1")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "test-job")

    def test_find_by_id_returns_none_when_missing(self):
        self.assertIsNone(self.repo.find_by_id("nonexistent"))

    def test_find_all_returns_all_saved_jobs(self):
        self.repo.save(self._make_job("j1", "job-one"))
        self.repo.save(self._make_job("j2", "job-two"))
        all_jobs = self.repo.find_all()
        self.assertEqual(len(all_jobs), 2)
        names = {j.name for j in all_jobs}
        self.assertIn("job-one", names)
        self.assertIn("job-two", names)

    def test_delete_removes_job(self):
        job = self._make_job()
        self.repo.save(job)
        self.repo.delete("j1")
        self.assertIsNone(self.repo.find_by_id("j1"))

    def test_delete_nonexistent_raises(self):
        with self.assertRaises(KeyError):
            self.repo.delete("ghost")

    def test_save_run_record_and_find_run_records(self):
        job = self._make_job()
        self.repo.save(job)
        rr1 = self._make_rr("rr1", "j1")
        rr2 = self._make_rr("rr2", "j1")
        self.repo.save_run_record(rr1)
        self.repo.save_run_record(rr2)
        records = self.repo.find_run_records("j1")
        self.assertEqual(len(records), 2)
        ids = {r.id for r in records}
        self.assertIn("rr1", ids)
        self.assertIn("rr2", ids)

    def test_find_run_records_empty_when_none(self):
        job = self._make_job()
        self.repo.save(job)
        self.assertEqual(self.repo.find_run_records("j1"), [])

    def test_find_run_records_only_returns_records_for_given_job(self):
        self.repo.save(self._make_job("j1"))
        self.repo.save(self._make_job("j2"))
        self.repo.save_run_record(self._make_rr("rr1", "j1"))
        self.repo.save_run_record(self._make_rr("rr2", "j2"))
        j1_records = self.repo.find_run_records("j1")
        self.assertEqual(len(j1_records), 1)
        self.assertEqual(j1_records[0].job_id, "j1")

    def test_implements_interface(self):
        from domain.scheduler.ports.i_job_repository import IJobRepository
        from domain.scheduler.ports.sqlite_job_repository import SQLiteJobRepository
        self.assertIsInstance(self.repo, IJobRepository)

    def test_persists_across_reconnect(self):
        """Data saved in one SQLiteJobRepository instance is readable by a new one."""
        from domain.scheduler.ports.sqlite_job_repository import SQLiteJobRepository
        self.repo.save(self._make_job("j1", "persistent-job"))
        repo2 = SQLiteJobRepository(db_path=self._tmp.name)
        found = repo2.find_by_id("j1")
        self.assertIsNotNone(found)
        self.assertEqual(found.name, "persistent-job")

    def test_save_is_idempotent_on_same_id(self):
        """Saving a job twice with the same id updates rather than duplicates."""
        job = self._make_job("j1", "original-name")
        self.repo.save(job)
        updated = self._make_job("j1", "updated-name")
        self.repo.save(updated)
        all_jobs = self.repo.find_all()
        self.assertEqual(len(all_jobs), 1)
        self.assertEqual(all_jobs[0].name, "updated-name")


if __name__ == "__main__":
    unittest.main()
