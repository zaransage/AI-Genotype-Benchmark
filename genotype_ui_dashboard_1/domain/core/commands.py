"""
Use-case command handlers for the metrics dashboard domain.

Each command receives its dependencies via constructor injection.
No framework exceptions here — HTTPException belongs at the route level only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from domain.core.models import Dashboard, MetricValue, MetricWidget
from domain.core.ports.i_dashboard_repository import IDashboardRepository
from domain.core.ports.i_metric_value_repository import IMetricValueRepository
from domain.core.ports.i_widget_repository import IWidgetRepository


class CreateDashboardCommand:
    def __init__(self, dashboards: IDashboardRepository) -> None:
        self._dashboards = dashboards

    def execute(self, name: str) -> Dashboard:
        dashboard = Dashboard(
            id=str(uuid4()),
            name=name,
            created_at=datetime.now(timezone.utc),
        )
        self._dashboards.save(dashboard)
        return dashboard


class ListDashboardsCommand:
    def __init__(self, dashboards: IDashboardRepository) -> None:
        self._dashboards = dashboards

    def execute(self) -> list[Dashboard]:
        return self._dashboards.list_all()


class AddWidgetCommand:
    def __init__(
        self,
        dashboards: IDashboardRepository,
        widgets: IWidgetRepository,
    ) -> None:
        self._dashboards = dashboards
        self._widgets    = widgets

    def execute(self, dashboard_id: str, name: str, unit: str) -> MetricWidget:
        if self._dashboards.get(dashboard_id) is None:
            raise ValueError(f"Dashboard '{dashboard_id}' not found")
        widget = MetricWidget(
            id=str(uuid4()),
            dashboard_id=dashboard_id,
            name=name,
            unit=unit,
        )
        self._widgets.save(widget)
        return widget


class PostMetricValueCommand:
    def __init__(
        self,
        widgets: IWidgetRepository,
        metric_values: IMetricValueRepository,
    ) -> None:
        self._widgets       = widgets
        self._metric_values = metric_values

    def execute(self, widget_id: str, value: float) -> MetricValue:
        if self._widgets.get(widget_id) is None:
            raise ValueError(f"Widget '{widget_id}' not found")
        metric_value = MetricValue(
            id=str(uuid4()),
            widget_id=widget_id,
            value=value,
            recorded_at=datetime.now(timezone.utc),
        )
        self._metric_values.append(metric_value)
        return metric_value


class ListWidgetsCommand:
    def __init__(self, widgets: IWidgetRepository) -> None:
        self._widgets = widgets

    def execute(self, dashboard_id: str) -> list[MetricWidget]:
        return self._widgets.list_by_dashboard(dashboard_id)


class ReadWidgetValuesCommand:
    def __init__(
        self,
        widgets: IWidgetRepository,
        metric_values: IMetricValueRepository,
    ) -> None:
        self._widgets       = widgets
        self._metric_values = metric_values

    def execute(self, widget_id: str) -> list[MetricValue]:
        if self._widgets.get(widget_id) is None:
            raise ValueError(f"Widget '{widget_id}' not found")
        return self._metric_values.list_by_widget(widget_id)
