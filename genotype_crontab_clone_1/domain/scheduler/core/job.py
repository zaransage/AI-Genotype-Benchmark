"""
domain/scheduler/core/job.py

Canonical dataclass models for the scheduler domain.
Validation occurs in __post_init__ — bad input raises ValueError, never silently passes.
Policy constants are class-level attributes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from croniter import CroniterBadCronError, croniter


@dataclass
class Job:
    """Canonical representation of a scheduled job."""

    VALID_STATUSES: tuple[str, ...] = field(
        default=("success", "failure"), init=False, repr=False, compare=False
    )

    id:              str
    name:            str
    command:         str
    cron_expression: str
    created_at:      datetime
    enabled:         bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Job.name must not be blank")
        if not self.command.strip():
            raise ValueError("Job.command must not be blank")
        if not croniter.is_valid(self.cron_expression):
            raise ValueError(
                f"Job.cron_expression is not a valid cron string: {self.cron_expression!r}"
            )


@dataclass
class RunRecord:
    """Canonical representation of a single job execution record."""

    VALID_STATUSES: tuple[str, ...] = field(
        default=("success", "failure"), init=False, repr=False, compare=False
    )

    id:           str
    job_id:       str
    triggered_at: datetime
    status:       str
    output:       str

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("RunRecord.job_id must not be blank")
        if self.status not in ("success", "failure"):
            raise ValueError(
                f"RunRecord.status must be 'success' or 'failure', got {self.status!r}"
            )
