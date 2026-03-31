"""
domain/scheduler/core/ports/in_memory_job_repository.py

In-memory implementation of IJobRepository.
Suitable for development, tests, and single-process deployments.
"""
from __future__ import annotations

from domain.scheduler.core.job import Job, RunRecord
from domain.scheduler.core.ports.i_job_repository import IJobRepository


class InMemoryJobRepository(IJobRepository):
    """Thread-unsafe, in-process store for jobs and run records."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job]          = {}
        self._runs: dict[str, list[RunRecord]] = {}

    def save(self, job: Job) -> None:
        self._jobs[job.id] = job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        return list(self._jobs.values())

    def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
        self._runs.pop(job_id, None)

    def save_run(self, run: RunRecord) -> None:
        self._runs.setdefault(run.job_id, []).append(run)

    def get_runs(self, job_id: str) -> list[RunRecord]:
        return list(self._runs.get(job_id, []))
