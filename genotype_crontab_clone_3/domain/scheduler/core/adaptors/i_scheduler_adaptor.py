"""
domain/scheduler/core/adaptors/i_scheduler_adaptor.py

Inbound adaptor interface — contract for how external callers drive the scheduler core.
Concrete implementations (e.g. FastAPI router) are co-located in this folder.
"""

import abc

from domain.scheduler.core.job     import Job
from domain.scheduler.core.job_run import JobRun


class ISchedulerAdaptor(abc.ABC):

    @abc.abstractmethod
    def create_job(self, name: str, command: str, cron_expression: str) -> Job: ...

    @abc.abstractmethod
    def list_jobs(self) -> list[Job]: ...

    @abc.abstractmethod
    def delete_job(self, job_id: str) -> bool: ...

    @abc.abstractmethod
    def get_run_history(self, job_id: str) -> list[JobRun]: ...

    @abc.abstractmethod
    def trigger_job(self, job_id: str) -> JobRun: ...
