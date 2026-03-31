"""
In-memory implementation of IDashboardRepo.

Suitable for testing and local development.
No external dependencies — storage is a plain dict keyed by id.
"""

from domain.dashboard.core.models import Dashboard, Widget
from domain.dashboard.core.ports.i_dashboard_repo import IDashboardRepo


class InMemoryDashboardRepo(IDashboardRepo):
    """Thread-unsafe in-memory store — use for tests and single-process dev only."""

    def __init__(self) -> None:
        self._dashboards: dict[str, Dashboard] = {}
        self._widgets:    dict[str, Widget]    = {}

    def save_dashboard(self, dashboard: Dashboard) -> None:
        self._dashboards[dashboard.id] = dashboard

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        return self._dashboards.get(dashboard_id)

    def list_dashboards(self) -> list:
        return list(self._dashboards.values())

    def save_widget(self, widget: Widget) -> None:
        self._widgets[widget.id] = widget

    def get_widget(self, widget_id: str) -> Widget | None:
        return self._widgets.get(widget_id)
