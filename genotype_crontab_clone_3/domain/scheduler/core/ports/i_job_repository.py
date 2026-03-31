"""
domain/scheduler/core/ports/i_job_repository.py

Outbound port interface — contract for how the core reaches external storage.
The composition root wires a concrete implementation at startup.
"""

import abc
from typing import Optional

from domain.scheduler.core.job     import Job
from domain.scheduler.core.job_run import JobRun


class IJobRepository(abc.ABC):

    @abc.abstractmethod
    def save(self, job: Job) -> None: ...

    @abc.abstractmethod
    def find_by_id(self, job_id: str) -> Optional[Job]: ...

    @abc.abstractmethod
    def find_all(self) -> list[Job]: ...

    @abc.abstractmethod
    def delete(self, job_id: str) -> bool: ...

    @abc.abstractmethod
    def save_run(self, run: JobRun) -> None: ...

    @abc.abstractmethod
    def find_runs(self, job_id: str) -> list[JobRun]: ...
