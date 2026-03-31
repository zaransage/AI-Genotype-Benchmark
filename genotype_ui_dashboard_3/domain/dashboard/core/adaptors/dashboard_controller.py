"""
DashboardController — inbound adaptor implementation.

Orchestrates use-case logic by coordinating canonical models and the repository port.
Framework exceptions (HTTPException) must NOT appear here — they belong in main.py.
Dependencies are injected; never instantiated inside this class.
Aligned column formatting is intentional; excluded from auto-formatters via pyproject.toml.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from domain.dashboard.core.adaptors.i_dashboard_controller import IDashboardController
from domain.dashboard.core.models                          import Dashboard, MetricValue, Widget
from domain.dashboard.core.ports.i_dashboard_repository   import IDashboardRepository


class DashboardController(IDashboardController):

    def __init__(self, repository: IDashboardRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Dashboard use-cases
    # ------------------------------------------------------------------

    def create_dashboard(self, name: str) -> Dashboard:
        dashboard = Dashboard(
            id         = str(uuid.uuid4()),
            name       = name,               # __post_init__ raises on empty
            created_at = _utcnow(),
        )
        self._repo.save(dashboard)
        return dashboard

    def list_dashboards(self) -> list[Dashboard]:
        return self._repo.list_all()

    # ------------------------------------------------------------------
    # Widget use-cases
    # ------------------------------------------------------------------

    def add_widget(self, dashboard_id: str, name: str, unit: str) -> Widget:
        dashboard = self._require_dashboard(dashboard_id)
        widget    = Widget(
            id           = str(uuid.uuid4()),
            name         = name,
            unit         = unit,
            dashboard_id = dashboard_id,
        )
        dashboard.widgets.append(widget)
        self._repo.save(dashboard)
        return widget

    def post_metric(
        self,
        dashboard_id: str,
        widget_id:    str,
        value:        float,
        timestamp:    str,
    ) -> MetricValue:
        dashboard = self._require_dashboard(dashboard_id)
        widget    = self._require_widget(dashboard, widget_id)
        mv        = MetricValue(timestamp=timestamp, value=value)
        widget.values.append(mv)
        self._repo.save(dashboard)
        return mv

    def get_widget(self, dashboard_id: str, widget_id: str) -> Widget:
        dashboard = self._require_dashboard(dashboard_id)
        return self._require_widget(dashboard, widget_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _require_dashboard(self, dashboard_id: str) -> Dashboard:
        dashboard = self._repo.get(dashboard_id)
        if dashboard is None:
            raise KeyError(f"Dashboard not found: {dashboard_id}")
        return dashboard

    @staticmethod
    def _require_widget(dashboard: Dashboard, widget_id: str) -> Widget:
        for w in dashboard.widgets:
            if w.id == widget_id:
                return w
        raise KeyError(f"Widget not found: {widget_id}")


def _utcnow() -> str:
    return datetime.now(timezone.utc).strftime(Dashboard.TIMESTAMP_FORMAT)
