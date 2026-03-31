"""
Canonical dataclass models for the dashboard domain.

Policy constants are baked in as class-level attributes.
Validation occurs in __post_init__ — bad input raises, never silently passes.
Aligned column formatting is intentional; excluded from auto-formatters via pyproject.toml.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing     import ClassVar


@dataclass
class MetricValue:
    TIMESTAMP_FORMAT: ClassVar[str] = "%Y-%m-%dT%H:%M:%SZ"

    timestamp: str
    value:     float

    def __post_init__(self) -> None:
        if not self.timestamp:
            raise ValueError("MetricValue.timestamp must not be empty")


@dataclass
class Widget:
    id:           str
    name:         str
    unit:         str
    dashboard_id: str
    values:       list[MetricValue] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Widget.name must not be empty")
        if not self.unit:
            raise ValueError("Widget.unit must not be empty")


@dataclass
class Dashboard:
    TIMESTAMP_FORMAT: ClassVar[str] = "%Y-%m-%dT%H:%M:%SZ"

    id:         str
    name:       str
    created_at: str
    widgets:    list[Widget] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Dashboard.name must not be empty")
        if not self.created_at:
            raise ValueError("Dashboard.created_at must not be empty")
