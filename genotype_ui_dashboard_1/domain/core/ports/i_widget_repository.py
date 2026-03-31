"""Outbound port: contract for metric widget persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.core.models import MetricWidget


class IWidgetRepository(ABC):

    @abstractmethod
    def save(self, widget: MetricWidget) -> None: ...

    @abstractmethod
    def get(self, widget_id: str) -> MetricWidget | None: ...

    @abstractmethod
    def list_by_dashboard(self, dashboard_id: str) -> list[MetricWidget]: ...
