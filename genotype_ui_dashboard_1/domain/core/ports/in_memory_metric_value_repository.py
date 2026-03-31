"""In-memory implementation of IMetricValueRepository."""
from __future__ import annotations

from domain.core.models import MetricValue
from domain.core.ports.i_metric_value_repository import IMetricValueRepository


class InMemoryMetricValueRepository(IMetricValueRepository):

    def __init__(self) -> None:
        self._store: list[MetricValue] = []

    def append(self, metric_value: MetricValue) -> None:
        self._store.append(metric_value)

    def list_by_widget(self, widget_id: str) -> list[MetricValue]:
        return [v for v in self._store if v.widget_id == widget_id]
