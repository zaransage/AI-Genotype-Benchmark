"""
domain/scheduler/core/ports/i_job_repository.py

Outbound port: contract for job and run-record persistence.
The core depends on this interface; implementations live alongside it.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.scheduler.core.job import Job, RunRecord


class IJobRepository(ABC):
    """Outbound port — persistent store for jobs and their run records."""

    @abstractmethod
    def save(self, job: Job) -> None:
        """Persist or update a job."""

    @abstractmethod
    def get(self, job_id: str) -> Job | None:
        """Return the job with the given ID, or None if not found."""

    @abstractmethod
    def list(self) -> list[Job]:
        """Return all persisted jobs."""

    @abstractmethod
    def delete(self, job_id: str) -> None:
        """Remove the job with the given ID. No-op if not found."""

    @abstractmethod
    def save_run(self, run: RunRecord) -> None:
        """Persist a run record."""

    @abstractmethod
    def get_runs(self, job_id: str) -> list[RunRecord]:
        """Return all run records for the given job, in insertion order."""
