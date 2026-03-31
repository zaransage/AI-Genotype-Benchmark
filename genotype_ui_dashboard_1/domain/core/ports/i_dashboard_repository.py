"""Outbound port: contract for dashboard persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.core.models import Dashboard


class IDashboardRepository(ABC):

    @abstractmethod
    def save(self, dashboard: Dashboard) -> None: ...

    @abstractmethod
    def get(self, dashboard_id: str) -> Dashboard | None: ...

    @abstractmethod
    def list_all(self) -> list[Dashboard]: ...
