"""IJobRepository — outbound port interface for job persistence."""
from abc import ABC, abstractmethod
from typing import List, Optional

from domain.scheduler.core.job import Job
from domain.scheduler.core.run_record import RunRecord


class IJobRepository(ABC):

    @abstractmethod
    def save(self, job: Job) -> None: ...

    @abstractmethod
    def find_by_id(self, job_id: str) -> Optional[Job]: ...

    @abstractmethod
    def find_all(self) -> List[Job]: ...

    @abstractmethod
    def delete(self, job_id: str) -> None: ...

    @abstractmethod
    def save_run_record(self, record: RunRecord) -> None: ...

    @abstractmethod
    def find_run_records(self, job_id: str) -> List[RunRecord]: ...
