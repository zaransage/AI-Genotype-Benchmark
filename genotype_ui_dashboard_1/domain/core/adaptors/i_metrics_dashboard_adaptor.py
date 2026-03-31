"""
Inbound adaptor interface: contract for how external callers drive the
metrics dashboard core.

All implementations (e.g. FastAPI router) must satisfy this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class IMetricsDashboardAdaptor(ABC):

    @abstractmethod
    def create_dashboard(self, name: str) -> dict: ...

    @abstractmethod
    def list_dashboards(self) -> list[dict]: ...

    @abstractmethod
    def add_widget(self, dashboard_id: str, name: str, unit: str) -> dict: ...

    @abstractmethod
    def post_metric_value(self, widget_id: str, value: float) -> dict: ...

    @abstractmethod
    def read_widget_values(self, widget_id: str) -> list[dict]: ...
