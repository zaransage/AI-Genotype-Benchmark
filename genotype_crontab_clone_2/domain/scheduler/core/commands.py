"""
Scheduler commands — core business logic.

Rules (ADR 0006, AI_CONTRACT §9):
- No framework imports (HTTPException stays at route level).
- Dependencies injected; never instantiated inside a command.
- logging.basicConfig never called here.
"""
import logging
import subprocess
import time
import uuid
from datetime import datetime, timezone

from domain.scheduler.core.job import Job
from domain.scheduler.core.run_record import RunRecord
from domain.scheduler.ports.i_job_repository import IJobRepository

logger = logging.getLogger(__name__)


class CreateJobCommand:

    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    def execute(self, name: str, command: str, cron_expression: str) -> Job:
        job = Job(
            id=str(uuid.uuid4()),
            name=name,
            command=command,
            cron_expression=cron_expression,
            created_at=datetime.now(timezone.utc),
        )
        self._repo.save(job)
        logger.info("Created job %s (%s)", job.id, job.name)
        return job


class ListJobsCommand:

    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    def execute(self) -> list[Job]:
        return self._repo.find_all()


class DeleteJobCommand:

    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    def execute(self, job_id: str) -> None:
        if self._repo.find_by_id(job_id) is None:
            raise KeyError(f"Job not found: {job_id!r}")
        self._repo.delete(job_id)
        logger.info("Deleted job %s", job_id)


class TriggerJobCommand:

    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    def execute(self, job_id: str) -> RunRecord:
        job = self._repo.find_by_id(job_id)
        if job is None:
            raise KeyError(f"Job not found: {job_id!r}")

        start = time.monotonic()
        triggered_at = datetime.now(timezone.utc)
        try:
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            status = "success" if result.returncode == 0 else "failure"
            output = (result.stdout + result.stderr).strip()
        except Exception as exc:
            status = "failure"
            output = str(exc)

        duration_s = time.monotonic() - start
        record = RunRecord(
            id=str(uuid.uuid4()),
            job_id=job_id,
            triggered_at=triggered_at,
            status=status,
            output=output,
            duration_s=round(duration_s, 3),
        )
        self._repo.save_run_record(record)
        logger.info("Triggered job %s -> %s (%.3fs)", job_id, status, duration_s)
        return record


class GetRunHistoryCommand:

    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    def execute(self, job_id: str) -> list[RunRecord]:
        if self._repo.find_by_id(job_id) is None:
            raise KeyError(f"Job not found: {job_id!r}")
        return self._repo.find_run_records(job_id)
