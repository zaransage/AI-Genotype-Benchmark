"""
domain/scheduler/core/ports/in_memory_job_repository.py

In-memory implementation of IJobRepository.
Suitable for development and testing; replace with a persistent store for production.
"""

from typing import Optional

from domain.scheduler.core.job                      import Job
from domain.scheduler.core.job_run                  import JobRun
from domain.scheduler.core.ports.i_job_repository   import IJobRepository


class InMemoryJobRepository(IJobRepository):

    def __init__(self) -> None:
        self._jobs: dict[str, Job]        = {}
        self._runs: dict[str, list[JobRun]] = {}

    def save(self, job: Job) -> None:
        self._jobs[job.id] = job

    def find_by_id(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def find_all(self) -> list[Job]:
        return list(self._jobs.values())

    def delete(self, job_id: str) -> bool:
        if job_id not in self._jobs:
            return False
        del self._jobs[job_id]
        return True

    def save_run(self, run: JobRun) -> None:
        self._runs.setdefault(run.job_id, []).append(run)

    def find_runs(self, job_id: str) -> list[JobRun]:
        return list(self._runs.get(job_id, []))
