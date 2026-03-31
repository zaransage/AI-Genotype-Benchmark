"""In-memory implementation of IWidgetRepository."""
from __future__ import annotations

from domain.core.models import MetricWidget
from domain.core.ports.i_widget_repository import IWidgetRepository


class InMemoryWidgetRepository(IWidgetRepository):

    def __init__(self) -> None:
        self._store: dict[str, MetricWidget] = {}

    def save(self, widget: MetricWidget) -> None:
        self._store[widget.id] = widget

    def get(self, widget_id: str) -> MetricWidget | None:
        return self._store.get(widget_id)

    def list_by_dashboard(self, dashboard_id: str) -> list[MetricWidget]:
        return [w for w in self._store.values() if w.dashboard_id == dashboard_id]
