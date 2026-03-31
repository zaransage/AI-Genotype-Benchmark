from __future__ import annotations

from models import Dashboard


class InMemoryStore:
    def __init__(self) -> None:
        self._dashboards: dict[str, Dashboard] = {}

    def get_all_dashboards(self) -> list[Dashboard]:
        return list(self._dashboards.values())

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        return self._dashboards.get(dashboard_id)

    def save_dashboard(self, dashboard: Dashboard) -> Dashboard:
        self._dashboards[dashboard.id] = dashboard
        return dashboard

    def delete_dashboard(self, dashboard_id: str) -> bool:
        if dashboard_id in self._dashboards:
            del self._dashboards[dashboard_id]
            return True
        return False


store = InMemoryStore()
