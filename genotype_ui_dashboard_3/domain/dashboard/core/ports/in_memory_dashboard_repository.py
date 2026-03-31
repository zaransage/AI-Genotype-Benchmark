"""
InMemoryDashboardRepository — in-memory implementation of IDashboardRepository.

Suitable for development, testing, and single-process deployments.
Swap for a database-backed implementation by injecting a different concrete type
at the composition root (main.py) without touching domain or adaptor code.
"""
from __future__ import annotations

from domain.dashboard.core.models                        import Dashboard
from domain.dashboard.core.ports.i_dashboard_repository import IDashboardRepository


class InMemoryDashboardRepository(IDashboardRepository):

    def __init__(self) -> None:
        self._store: dict[str, Dashboard] = {}

    def save(self, dashboard: Dashboard) -> None:
        self._store[dashboard.id] = dashboard

    def get(self, dashboard_id: str) -> Dashboard | None:
        return self._store.get(dashboard_id)

    def list_all(self) -> list[Dashboard]:
        return list(self._store.values())
