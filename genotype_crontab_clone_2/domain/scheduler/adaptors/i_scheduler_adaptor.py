"""ISchedulerAdaptor — inbound interface defining REST surface for the scheduler."""
from abc import ABC, abstractmethod
from typing import Any


class ISchedulerAdaptor(ABC):

    @abstractmethod
    def create_job(self, payload: Any) -> Any: ...

    @abstractmethod
    def list_jobs(self) -> Any: ...

    @abstractmethod
    def delete_job(self, job_id: str) -> Any: ...

    @abstractmethod
    def trigger_job(self, job_id: str) -> Any: ...

    @abstractmethod
    def get_run_history(self, job_id: str) -> Any: ...
