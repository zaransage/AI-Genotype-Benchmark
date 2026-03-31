"""
domain/scheduler/core/ports/subprocess_job_executor.py

Concrete implementation of IJobExecutor that runs commands via subprocess.
"""
from __future__ import annotations

import subprocess
import uuid
from datetime import datetime, timezone

from domain.scheduler.core.job import RunRecord
from domain.scheduler.core.ports.i_job_executor import IJobExecutor


class SubprocessJobExecutor(IJobExecutor):
    """Runs shell commands via subprocess.run and captures stdout/stderr."""

    def execute(self, job_id: str, command: str) -> RunRecord:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
        )
        status = "success" if result.returncode == 0 else "failure"
        output = result.stdout or result.stderr or ""
        return RunRecord(
            id           = str(uuid.uuid4()),
            job_id       = job_id,
            triggered_at = datetime.now(tz=timezone.utc),
            status       = status,
            output       = output,
        )
