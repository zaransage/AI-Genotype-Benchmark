from typing import Dict, Optional
from models import Dashboard


class InMemoryStore:
    def __init__(self):
        self._dashboards: Dict[str, Dashboard] = {}

    def add_dashboard(self, dashboard: Dashboard) -> Dashboard:
        self._dashboards[dashboard.id] = dashboard
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        return self._dashboards.get(dashboard_id)

    def list_dashboards(self) -> list[Dashboard]:
        return list(self._dashboards.values())

    def save_dashboard(self, dashboard: Dashboard) -> Dashboard:
        self._dashboards[dashboard.id] = dashboard
        return dashboard


store = InMemoryStore()
