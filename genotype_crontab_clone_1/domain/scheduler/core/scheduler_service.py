"""
domain/scheduler/core/scheduler_service.py

Business logic for the scheduler domain.
Depends on IJobRepository (outbound) and IJobExecutor (outbound) via injection.
Raises ValueError for domain rule violations — no framework exceptions here.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.scheduler.core.job import Job, RunRecord
from domain.scheduler.core.ports.i_job_executor import IJobExecutor
from domain.scheduler.core.ports.i_job_repository import IJobRepository


class SchedulerService:
    """Core command handlers for job scheduling operations."""

    def __init__(
        self,
        repository: IJobRepository,
        executor:   IJobExecutor,
    ) -> None:
        self._repository = repository
        self._executor   = executor

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def create_job(
        self,
        name:            str,
        command:         str,
        cron_expression: str,
    ) -> Job:
        """Create and persist a new scheduled job."""
        job = Job(
            id              = str(uuid.uuid4()),
            name            = name,
            command         = command,
            cron_expression = cron_expression,
            created_at      = datetime.now(tz=timezone.utc),
            enabled         = True,
        )
        self._repository.save(job)
        return job

    def delete_job(self, job_id: str) -> None:
        """Remove a job by ID. Raises ValueError if not found."""
        if self._repository.get(job_id) is None:
            raise ValueError(f"Job {job_id!r} not found")
        self._repository.delete(job_id)

    def trigger_job(self, job_id: str) -> RunRecord:
        """Execute a job immediately and record the outcome."""
        job = self._repository.get(job_id)
        if job is None:
            raise ValueError(f"Job {job_id!r} not found")
        run = self._executor.execute(job_id=job.id, command=job.command)
        self._repository.save_run(run)
        return run

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_job(self, job_id: str) -> Job | None:
        """Return the job with the given ID, or None."""
        return self._repository.get(job_id)

    def list_jobs(self) -> list[Job]:
        """Return all registered jobs."""
        return self._repository.list()

    def get_run_history(self, job_id: str) -> list[RunRecord]:
        """Return all run records for a job, in insertion order."""
        return self._repository.get_runs(job_id)
