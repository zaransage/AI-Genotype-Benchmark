"""InMemoryJobRepository — in-memory implementation of IJobRepository."""
from typing import Dict, List, Optional

from domain.scheduler.core.job import Job
from domain.scheduler.core.run_record import RunRecord
from domain.scheduler.ports.i_job_repository import IJobRepository


class InMemoryJobRepository(IJobRepository):

    def __init__(self) -> None:
        self._jobs: Dict[str, Job]              = {}
        self._runs: Dict[str, List[RunRecord]]  = {}

    def save(self, job: Job) -> None:
        self._jobs[job.id] = job

    def find_by_id(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def find_all(self) -> List[Job]:
        return list(self._jobs.values())

    def delete(self, job_id: str) -> None:
        if job_id not in self._jobs:
            raise KeyError(f"Job not found: {job_id!r}")
        del self._jobs[job_id]

    def save_run_record(self, record: RunRecord) -> None:
        self._runs.setdefault(record.job_id, []).append(record)

    def find_run_records(self, job_id: str) -> List[RunRecord]:
        return list(self._runs.get(job_id, []))
