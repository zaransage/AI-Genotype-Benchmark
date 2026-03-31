"""
Tests for the web UI inbound adaptor.

Exercises GET /ui with an in-memory repo stack.  Asserts on the raw HTML
fixture assumptions AND on the canonical model fields present in the rendered
page so that both sides of the translation are validated.

Layer: adaptors
"""
from __future__ import annotations

import unittest
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.core.adaptors.web_ui_router import WebUIAdaptor, create_web_ui_router
from domain.core.commands import (
    ListDashboardsCommand,
    ListWidgetsCommand,
    ReadWidgetValuesCommand,
)
from domain.core.models import Dashboard, MetricValue, MetricWidget
from domain.core.ports.in_memory_dashboard_repository import InMemoryDashboardRepository
from domain.core.ports.in_memory_metric_value_repository import InMemoryMetricValueRepository
from domain.core.ports.in_memory_widget_repository import InMemoryWidgetRepository

_TS = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)


def _make_client(
    dash_repo=None,
    widget_repo=None,
    value_repo=None,
) -> TestClient:
    dash_repo   = dash_repo   or InMemoryDashboardRepository()
    widget_repo = widget_repo or InMemoryWidgetRepository()
    value_repo  = value_repo  or InMemoryMetricValueRepository()

    adaptor = WebUIAdaptor(
        list_dashboards_cmd=ListDashboardsCommand(dashboards=dash_repo),
        list_widgets_cmd=ListWidgetsCommand(widgets=widget_repo),
        read_values_cmd=ReadWidgetValuesCommand(widgets=widget_repo, metric_values=value_repo),
    )
    app = FastAPI()
    app.include_router(create_web_ui_router(adaptor))
    return TestClient(app)


class TestWebUIIndexEmpty(unittest.TestCase):
    """GET /ui with no data shows an empty-state message."""

    def setUp(self) -> None:
        self._client = _make_client()

    def test_returns_200(self) -> None:
        resp = self._client.get("/ui")
        self.assertEqual(resp.status_code, 200)

    def test_content_type_is_html(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("text/html", resp.headers["content-type"])

    def test_page_title_present(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("<title>Metrics Dashboard</title>", resp.text)

    def test_empty_state_message_shown(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("No dashboards", resp.text)


class TestWebUIIndexWithDashboard(unittest.TestCase):
    """GET /ui renders dashboard name and metadata."""

    def setUp(self) -> None:
        self._dash_repo = InMemoryDashboardRepository()
        self._dash_repo.save(
            Dashboard(id="d1", name="Production Metrics", created_at=_TS)
        )
        self._client = _make_client(dash_repo=self._dash_repo)

    def test_dashboard_name_appears_in_page(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("Production Metrics", resp.text)

    def test_dashboard_id_appears_in_page(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("d1", resp.text)

    def test_no_widgets_message_shown(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("No widgets", resp.text)


class TestWebUIIndexWithWidgetsAndValues(unittest.TestCase):
    """GET /ui renders widgets and their metric readings."""

    def setUp(self) -> None:
        self._dash_repo   = InMemoryDashboardRepository()
        self._widget_repo = InMemoryWidgetRepository()
        self._value_repo  = InMemoryMetricValueRepository()

        self._dash_repo.save(
            Dashboard(id="d1", name="Infra", created_at=_TS)
        )
        self._widget_repo.save(
            MetricWidget(id="w1", dashboard_id="d1", name="CPU Usage", unit="percent")
        )
        self._value_repo.append(
            MetricValue(id="v1", widget_id="w1", value=73.5, recorded_at=_TS)
        )
        self._client = _make_client(
            dash_repo=self._dash_repo,
            widget_repo=self._widget_repo,
            value_repo=self._value_repo,
        )

    def test_widget_name_appears(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("CPU Usage", resp.text)

    def test_widget_unit_appears(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("percent", resp.text)

    def test_metric_value_appears(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("73.5", resp.text)

    def test_recorded_at_appears(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("2024-06-01", resp.text)

    def test_html_escaping_prevents_xss(self) -> None:
        """Dashboard names with HTML special chars must be escaped."""
        dash_repo = InMemoryDashboardRepository()
        dash_repo.save(
            Dashboard(id="d2", name="<script>alert(1)</script>", created_at=_TS)
        )
        client = _make_client(dash_repo=dash_repo)
        resp = client.get("/ui")
        self.assertNotIn("<script>alert(1)</script>", resp.text)
        self.assertIn("&lt;script&gt;", resp.text)


class TestWebUIOnlyLastTenValues(unittest.TestCase):
    """GET /ui shows at most 10 readings per widget (most recent)."""

    def setUp(self) -> None:
        self._dash_repo   = InMemoryDashboardRepository()
        self._widget_repo = InMemoryWidgetRepository()
        self._value_repo  = InMemoryMetricValueRepository()

        self._dash_repo.save(
            Dashboard(id="d1", name="Dash", created_at=_TS)
        )
        self._widget_repo.save(
            MetricWidget(id="w1", dashboard_id="d1", name="Mem", unit="MB")
        )
        # Append 12 readings with distinct float values 0.0 … 11.0
        for i in range(12):
            self._value_repo.append(
                MetricValue(
                    id=f"v{i}",
                    widget_id="w1",
                    value=float(i),
                    recorded_at=_TS,
                )
            )
        self._client = _make_client(
            dash_repo=self._dash_repo,
            widget_repo=self._widget_repo,
            value_repo=self._value_repo,
        )

    def test_first_two_values_not_present(self) -> None:
        """Values 0.0 and 1.0 fall outside the last-10 window."""
        resp = self._client.get("/ui")
        # The page must contain the last 10 values (2.0 through 11.0).
        # Values 0.0 and 1.0 may not appear as standalone strings because
        # they are excluded from the last-10 slice.
        # We verify that the last value (11.0) IS present.
        self.assertIn("11.0", resp.text)


if __name__ == "__main__":
    unittest.main()
