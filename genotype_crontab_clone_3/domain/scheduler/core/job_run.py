"""
domain/scheduler/core/job_run.py

Canonical JobRun dataclass. Records the outcome of a single job execution.
Validation occurs in __post_init__ — bad input raises.
"""

from dataclasses import dataclass

VALID_TRIGGER_TYPES = frozenset({"manual", "scheduled"})


@dataclass
class JobRun:
    id:           str
    job_id:       str
    triggered_at: str
    exit_code:    int
    output:       str
    trigger_type: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("JobRun.id must not be empty")
        if not self.job_id:
            raise ValueError("JobRun.job_id must not be empty")
        if self.trigger_type not in VALID_TRIGGER_TYPES:
            raise ValueError(
                f"JobRun.trigger_type must be one of {VALID_TRIGGER_TYPES}, "
                f"got '{self.trigger_type}'"
            )

    def to_dict(self) -> dict:
        return {
            "id":           self.id,
            "job_id":       self.job_id,
            "triggered_at": self.triggered_at,
            "exit_code":    self.exit_code,
            "output":       self.output,
            "trigger_type": self.trigger_type,
        }
