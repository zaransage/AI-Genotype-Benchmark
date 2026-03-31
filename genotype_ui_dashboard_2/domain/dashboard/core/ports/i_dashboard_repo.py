"""
Outbound port interface: IDashboardRepo.

Defines the contract the core needs from external storage.
Implementations belong here alongside the interface (ADR-0008).
Framework and infrastructure concerns must never appear in this file.
"""

from abc import ABC, abstractmethod

from domain.dashboard.core.models import Dashboard, Widget


class IDashboardRepo(ABC):
    """Outbound storage contract for the dashboard domain."""

    @abstractmethod
    def save_dashboard(self, dashboard: Dashboard) -> None:
        """Persist or overwrite a dashboard by id."""

    @abstractmethod
    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        """Return Dashboard for the given id, or None if not found."""

    @abstractmethod
    def list_dashboards(self) -> list:
        """Return all persisted dashboards."""

    @abstractmethod
    def save_widget(self, widget: Widget) -> None:
        """Persist or overwrite a widget by id."""

    @abstractmethod
    def get_widget(self, widget_id: str) -> Widget | None:
        """Return Widget for the given id, or None if not found."""
