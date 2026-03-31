"""Tests for SQLite persistence in Storage."""
from __future__ import annotations

import pytest

from models import Job, RunRecord
from storage import Storage


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_job(**kwargs) -> Job:
    defaults = dict(name="test-job", command="echo hi", cron_expression="* * * * *")
    defaults.update(kwargs)
    return Job(**defaults)


def _make_run(job_id: str, **kwargs) -> RunRecord:
    from datetime import datetime
    defaults = dict(
        job_id=job_id,
        started_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
        exit_code=0,
        stdout="ok",
        stderr="",
        triggered_manually=False,
    )
    defaults.update(kwargs)
    return RunRecord(**defaults)


# ── persistence across instances ──────────────────────────────────────────────

def test_job_survives_restart(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job()
    s1.add_job(job)

    s2 = Storage(db_path=db)
    loaded = s2.get_job(job.id)
    assert loaded is not None
    assert loaded.name == job.name
    assert loaded.command == job.command
    assert loaded.cron_expression == job.cron_expression


def test_job_fields_round_trip(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job(name="my-job", command="ls -la", cron_expression="0 * * * *")
    s1.add_job(job)

    s2 = Storage(db_path=db)
    loaded = s2.get_job(job.id)
    assert loaded.id == job.id
    assert loaded.enabled is True


def test_run_record_survives_restart(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job()
    s1.add_job(job)
    run = _make_run(job.id, stdout="hello", exit_code=0)
    s1.add_run(run)

    s2 = Storage(db_path=db)
    history = s2.get_history(job.id)
    assert history is not None
    assert len(history) == 1
    assert history[0].stdout == "hello"
    assert history[0].exit_code == 0


def test_multiple_runs_persist(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job()
    s1.add_job(job)
    for i in range(3):
        s1.add_run(_make_run(job.id, stdout=f"run-{i}"))

    s2 = Storage(db_path=db)
    assert len(s2.get_history(job.id)) == 3


def test_delete_job_removed_from_db(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job()
    s1.add_job(job)
    s1.delete_job(job.id)

    s2 = Storage(db_path=db)
    assert s2.get_job(job.id) is None
    assert s2.get_history(job.id) is None


def test_delete_removes_associated_runs(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job()
    s1.add_job(job)
    s1.add_run(_make_run(job.id))
    s1.delete_job(job.id)

    s2 = Storage(db_path=db)
    assert s2.get_history(job.id) is None


def test_multiple_jobs_persist(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    jobs = [_make_job(name=f"job-{i}") for i in range(5)]
    for j in jobs:
        s1.add_job(j)

    s2 = Storage(db_path=db)
    assert len(s2.list_jobs()) == 5
    names = {j.name for j in s2.list_jobs()}
    for j in jobs:
        assert j.name in names


# ── in-memory isolation ───────────────────────────────────────────────────────

def test_memory_storage_starts_empty():
    s = Storage(db_path=":memory:")
    assert s.list_jobs() == []


def test_clear_wipes_memory_and_db(tmp_path):
    db = str(tmp_path / "jobs.db")
    s = Storage(db_path=db)
    job = _make_job()
    s.add_job(job)
    s.add_run(_make_run(job.id))

    s.clear()
    assert s.list_jobs() == []

    # Verify DB is also cleared
    s2 = Storage(db_path=db)
    assert s2.list_jobs() == []


def test_run_with_none_exit_code_persists(tmp_path):
    """RunRecord with None exit_code should round-trip cleanly."""
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job()
    s1.add_job(job)
    run = _make_run(job.id, exit_code=None, finished_at=None)
    s1.add_run(run)

    s2 = Storage(db_path=db)
    history = s2.get_history(job.id)
    assert len(history) == 1
    assert history[0].exit_code is None


def test_manually_triggered_flag_persists(tmp_path):
    db = str(tmp_path / "jobs.db")
    s1 = Storage(db_path=db)
    job = _make_job()
    s1.add_job(job)
    s1.add_run(_make_run(job.id, triggered_manually=True))

    s2 = Storage(db_path=db)
    history = s2.get_history(job.id)
    assert history[0].triggered_manually is True
