"""
domain/scheduler/core/ports/i_job_executor.py

Outbound port: contract for executing a job command and returning a run record.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.scheduler.core.job import RunRecord


class IJobExecutor(ABC):
    """Outbound port — executes a shell command and returns a RunRecord."""

    @abstractmethod
    def execute(self, job_id: str, command: str) -> RunRecord:
        """
        Run the command associated with job_id.
        Returns a RunRecord with status 'success' or 'failure' and captured output.
        """
