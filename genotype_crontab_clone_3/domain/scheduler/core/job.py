"""
domain/scheduler/core/job.py

Canonical Job dataclass. This is the primary container passed between adaptors,
the service layer, and ports. Validation occurs in __post_init__ — bad input raises.
"""

from dataclasses import dataclass
from typing import ClassVar


@dataclass
class Job:
    DATE_FORMAT: ClassVar[str] = "%Y-%m-%dT%H:%M:%S%z"  # class-level policy constant

    id:              str
    name:            str
    command:         str
    cron_expression: str
    created_at:      str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Job.id must not be empty")
        if not self.name:
            raise ValueError("Job.name must not be empty")
        if not self.command:
            raise ValueError("Job.command must not be empty")
        if not self.cron_expression:
            raise ValueError("Job.cron_expression must not be empty")

    def to_dict(self) -> dict:
        return {
            "id":              self.id,
            "name":            self.name,
            "command":         self.command,
            "cron_expression": self.cron_expression,
            "created_at":      self.created_at,
        }
