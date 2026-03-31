"""Outbound port: contract for metric value persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod

from domain.core.models import MetricValue


class IMetricValueRepository(ABC):

    @abstractmethod
    def append(self, metric_value: MetricValue) -> None: ...

    @abstractmethod
    def list_by_widget(self, widget_id: str) -> list[MetricValue]: ...
