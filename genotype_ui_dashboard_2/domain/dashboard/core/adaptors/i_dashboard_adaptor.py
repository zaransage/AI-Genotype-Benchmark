"""
Inbound adaptor interface: IDashboardAdaptor.

Defines the contract for how external callers drive the dashboard core.
Implementations (e.g. REST routes, CLI) live alongside this interface (ADR-0008).
"""

from abc import ABC, abstractmethod


class IDashboardAdaptor(ABC):
    """Inbound contract — how external callers access the dashboard domain."""

    @abstractmethod
    def create_dashboard(self, name: str) -> dict:
        """Create a dashboard and return its serialised representation."""

    @abstractmethod
    def list_dashboards(self) -> list:
        """Return all dashboards as a list of serialised representations."""

    @abstractmethod
    def add_widget(self, dashboard_id: str, name: str, metric_name: str) -> dict:
        """Add a widget to a dashboard and return its serialised representation."""

    @abstractmethod
    def post_metric(self, widget_id: str, value: float) -> dict:
        """Append a metric value to a widget and return it serialised."""

    @abstractmethod
    def read_widget_values(self, widget_id: str) -> list:
        """Return all metric values for a widget as serialised representations."""
