"""
Canonical dataclass models for the metrics dashboard domain.

Aligned column formatting is intentional — excluded from auto-formatters
via pyproject.toml.  Validation occurs in __post_init__; bad input raises,
never silently passes.  Policy constants are class-level, not injected.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import ClassVar


@dataclass
class Dashboard:
    DATE_FORMAT: ClassVar[str] = "%Y-%m-%dT%H:%M:%SZ"

    id:          str
    name:        str
    created_at:  datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Dashboard.id must be a non-blank string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Dashboard.name must be a non-blank string")
        if not isinstance(self.created_at, datetime):
            raise ValueError("Dashboard.created_at must be a datetime instance")


@dataclass
class MetricWidget:
    DATE_FORMAT: ClassVar[str] = "%Y-%m-%dT%H:%M:%SZ"

    id:           str
    dashboard_id: str
    name:         str
    unit:         str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("MetricWidget.id must be a non-blank string")
        if not isinstance(self.dashboard_id, str) or not self.dashboard_id.strip():
            raise ValueError("MetricWidget.dashboard_id must be a non-blank string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("MetricWidget.name must be a non-blank string")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("MetricWidget.unit must be a non-blank string")


@dataclass
class MetricValue:
    DATE_FORMAT: ClassVar[str] = "%Y-%m-%dT%H:%M:%SZ"

    id:          str
    widget_id:   str
    value:       float
    recorded_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("MetricValue.id must be a non-blank string")
        if not isinstance(self.widget_id, str) or not self.widget_id.strip():
            raise ValueError("MetricValue.widget_id must be a non-blank string")
        if not isinstance(self.value, (int, float)):
            raise ValueError("MetricValue.value must be numeric")
        if not isinstance(self.recorded_at, datetime):
            raise ValueError("MetricValue.recorded_at must be a datetime instance")
