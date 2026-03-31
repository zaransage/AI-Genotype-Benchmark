"""
IDashboardRepository — outbound port interface.

Defines the contract the core expects from any persistent store.
Implementations live alongside this file (see in_memory_dashboard_repository.py).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.dashboard.core.models import Dashboard


class IDashboardRepository(ABC):

    @abstractmethod
    def save(self, dashboard: Dashboard) -> None:
        """Persist or overwrite a dashboard by its id."""

    @abstractmethod
    def get(self, dashboard_id: str) -> Dashboard | None:
        """Return the dashboard with the given id, or None if not found."""

    @abstractmethod
    def list_all(self) -> list[Dashboard]:
        """Return all persisted dashboards."""
