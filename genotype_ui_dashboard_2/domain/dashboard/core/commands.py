"""
Core business logic commands for the dashboard domain.

Rules enforced here (AI_CONTRACT.md, ADR-0006):
- Dependencies injected — never instantiated inside the class.
- HTTPException and other framework types MUST NOT appear here.
- Raise LookupError for "not found" — routes map this to HTTP 404.
- Raise ValueError for invalid input — routes map this to HTTP 422.
"""

from datetime import datetime, timezone
from uuid import uuid4

from domain.dashboard.core.models import Dashboard, MetricValue, Widget
from domain.dashboard.core.ports.i_dashboard_repo import IDashboardRepo


class CreateDashboardCommand:
    def __init__(self, repo: IDashboardRepo) -> None:
        self._repo = repo

    def execute(self, name: str) -> Dashboard:
        dashboard = Dashboard(id=str(uuid4()), name=name)  # validation in __post_init__
        self._repo.save_dashboard(dashboard)
        return dashboard


class ListDashboardsCommand:
    def __init__(self, repo: IDashboardRepo) -> None:
        self._repo = repo

    def execute(self) -> list:
        return self._repo.list_dashboards()


class AddWidgetCommand:
    def __init__(self, repo: IDashboardRepo) -> None:
        self._repo = repo

    def execute(self, dashboard_id: str, name: str, metric_name: str) -> Widget:
        dashboard = self._repo.get_dashboard(dashboard_id)
        if dashboard is None:
            raise LookupError(f"Dashboard '{dashboard_id}' not found")
        widget = Widget(
            id           = str(uuid4()),
            dashboard_id = dashboard_id,
            name         = name,
            metric_name  = metric_name,
        )
        self._repo.save_widget(widget)
        dashboard.widget_ids.append(widget.id)
        self._repo.save_dashboard(dashboard)
        return widget


class PostMetricCommand:
    def __init__(self, repo: IDashboardRepo) -> None:
        self._repo = repo

    def execute(self, widget_id: str, value: float) -> MetricValue:
        widget = self._repo.get_widget(widget_id)
        if widget is None:
            raise LookupError(f"Widget '{widget_id}' not found")
        recorded_at = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        metric_value = MetricValue(value=value, recorded_at=recorded_at)
        widget.values.append(metric_value)
        self._repo.save_widget(widget)
        return metric_value


class ReadWidgetValuesCommand:
    def __init__(self, repo: IDashboardRepo) -> None:
        self._repo = repo

    def execute(self, widget_id: str) -> list:
        widget = self._repo.get_widget(widget_id)
        if widget is None:
            raise LookupError(f"Widget '{widget_id}' not found")
        return widget.values


class GetDashboardCommand:
    def __init__(self, repo: IDashboardRepo) -> None:
        self._repo = repo

    def execute(self, dashboard_id: str) -> Dashboard:
        dashboard = self._repo.get_dashboard(dashboard_id)
        if dashboard is None:
            raise LookupError(f"Dashboard '{dashboard_id}' not found")
        return dashboard


class GetWidgetCommand:
    def __init__(self, repo: IDashboardRepo) -> None:
        self._repo = repo

    def execute(self, widget_id: str) -> Widget:
        widget = self._repo.get_widget(widget_id)
        if widget is None:
            raise LookupError(f"Widget '{widget_id}' not found")
        return widget
