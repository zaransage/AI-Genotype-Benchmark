"""
IDashboardController — inbound adaptor interface.

Defines the contract that external callers (e.g. FastAPI routes) rely on.
HTTPException and other framework concerns belong at the route level — never here.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.dashboard.core.models import Dashboard, MetricValue, Widget


class IDashboardController(ABC):

    @abstractmethod
    def create_dashboard(self, name: str) -> Dashboard:
        """Create and persist a new dashboard. Raises ValueError on bad input."""

    @abstractmethod
    def list_dashboards(self) -> list[Dashboard]:
        """Return all dashboards."""

    @abstractmethod
    def add_widget(self, dashboard_id: str, name: str, unit: str) -> Widget:
        """Add a metric widget to a dashboard. Raises KeyError if dashboard not found."""

    @abstractmethod
    def post_metric(
        self,
        dashboard_id: str,
        widget_id:    str,
        value:        float,
        timestamp:    str,
    ) -> MetricValue:
        """Append a metric value to a widget. Raises KeyError if dashboard or widget not found."""

    @abstractmethod
    def get_widget(self, dashboard_id: str, widget_id: str) -> Widget:
        """Return a widget with its accumulated values. Raises KeyError if not found."""
