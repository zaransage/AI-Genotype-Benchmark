"""Canonical Job dataclass — the primary container for a scheduled job."""
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


# Five-field cron: minute hour dom month dow — each field is [0-9*/,-]+
_CRON_RE = re.compile(
    r"^(\*|[0-9*/,-]+)\s+"
    r"(\*|[0-9*/,-]+)\s+"
    r"(\*|[0-9*/,-]+)\s+"
    r"(\*|[0-9*/,-]+)\s+"
    r"(\*|[0-9*/,-]+)$"
)


@dataclass
class Job:
    DATE_FORMAT: str = field(default="%Y-%m-%dT%H:%M:%SZ", init=False, repr=False, compare=False)

    id:              str
    name:            str
    command:         str
    cron_expression: str
    created_at:      datetime
    enabled:         bool = True

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Job.name must not be empty")
        if not self.command.strip():
            raise ValueError("Job.command must not be empty")
        if not _CRON_RE.match(self.cron_expression.strip()):
            raise ValueError(
                f"Invalid cron expression: {self.cron_expression!r}. "
                "Expected five fields: minute hour dom month dow"
            )
