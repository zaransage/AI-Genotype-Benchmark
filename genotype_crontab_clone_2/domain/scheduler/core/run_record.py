"""Canonical RunRecord dataclass — records a single execution of a Job."""
from dataclasses import dataclass, field
from datetime import datetime

_VALID_STATUSES = frozenset({"success", "failure", "running"})


@dataclass
class RunRecord:
    DATE_FORMAT: str = field(default="%Y-%m-%dT%H:%M:%SZ", init=False, repr=False, compare=False)

    id:           str
    job_id:       str
    triggered_at: datetime
    status:       str
    output:       str
    duration_s:   float

    def __post_init__(self) -> None:
        if self.status not in _VALID_STATUSES:
            raise ValueError(
                f"RunRecord.status must be one of {sorted(_VALID_STATUSES)}, got {self.status!r}"
            )
