"""
domain/scheduler/core/scheduler_service.py

Business logic for the job scheduler. All coordination between the domain
models and the outbound repository port lives here.

Rules (ADR-0006):
- No HTTPException here — that belongs at the route level.
- No logging.basicConfig() here — that belongs at the application boundary.
- Repository is injected, never self-instantiated.
"""

import subprocess
import uuid
from datetime import datetime, timezone

from domain.scheduler.core.job                    import Job
from domain.scheduler.core.job_run                import JobRun
from domain.scheduler.core.ports.i_job_repository import IJobRepository


class SchedulerService:

    def __init__(self, repo: IJobRepository) -> None:
        self._repo = repo

    def create_job(self, name: str, command: str, cron_expression: str) -> Job:
        job = Job(
            id=str(uuid.uuid4()),
            name=name,
            command=command,
            cron_expression=cron_expression,
            created_at=datetime.now(tz=timezone.utc).isoformat(),
        )
        self._repo.save(job)
        return job

    def list_jobs(self) -> list[Job]:
        return self._repo.find_all()

    def delete_job(self, job_id: str) -> bool:
        return self._repo.delete(job_id)

    def get_run_history(self, job_id: str) -> list[JobRun]:
        return self._repo.find_runs(job_id)

    def trigger_job(self, job_id: str) -> JobRun:
        job = self._repo.find_by_id(job_id)
        if job is None:
            raise ValueError(f"Job '{job_id}' not found")

        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
        )
        output = (result.stdout + result.stderr).strip()

        run = JobRun(
            id=str(uuid.uuid4()),
            job_id=job_id,
            triggered_at=datetime.now(tz=timezone.utc).isoformat(),
            exit_code=result.returncode,
            output=output,
            trigger_type="manual",
        )
        self._repo.save_run(run)
        return run
