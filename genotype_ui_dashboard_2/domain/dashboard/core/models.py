"""
Canonical dataclass models for the dashboard domain.

Validation in __post_init__ — bad input raises, never silently passes (AI_CONTRACT.md §3).
Policy constants are class-level, not injected (ADR-0006).
"""

from dataclasses import dataclass, field


@dataclass
class MetricValue:
    """A single recorded metric sample."""

    DATE_FORMAT: str = field(default="ISO8601", init=False, repr=False, compare=False)

    value:       float
    recorded_at: str   # ISO 8601 — "YYYY-MM-DDTHH:MM:SSZ"

    def __post_init__(self) -> None:
        if not isinstance(self.value, (int, float)):
            raise TypeError(f"value must be numeric, got {type(self.value)}")


@dataclass
class Widget:
    """A metric widget belonging to a dashboard."""

    id:           str
    dashboard_id: str
    name:         str
    metric_name:  str
    values:       list = field(default_factory=list)  # list[MetricValue]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Widget.name must not be empty")
        if not self.metric_name or not self.metric_name.strip():
            raise ValueError("Widget.metric_name must not be empty")


@dataclass
class Dashboard:
    """A named collection of metric widgets."""

    id:         str
    name:       str
    widget_ids: list = field(default_factory=list)  # list[str]

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Dashboard.name must not be empty")
