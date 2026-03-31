"""
test_ui_adaptor.py — UiRouter HTML rendering tests.

Uses a mock IDashboardController to isolate rendering logic from storage.
Asserts:
  - HTML output contains expected domain data.
  - XSS-sensitive fields are escaped.
  - KeyError is raised for unknown dashboard IDs.
"""
import unittest
from unittest.mock import MagicMock

from domain.dashboard.core.models import Dashboard, MetricValue, Widget


def _make_mock_ctrl():
    from domain.dashboard.core.adaptors.i_dashboard_controller import IDashboardController
    return MagicMock(spec=IDashboardController)


def _make_ui_router(ctrl=None):
    from domain.dashboard.core.adaptors.ui_router import UiRouter
    return UiRouter(controller=ctrl or _make_mock_ctrl())


class TestRenderDashboardList(unittest.TestCase):

    def test_renders_html_with_dashboard_names(self):
        ctrl = _make_mock_ctrl()
        ctrl.list_dashboards.return_value = [
            Dashboard(id="d1", name="Alpha", created_at="2026-03-29T10:00:00Z"),
            Dashboard(id="d2", name="Beta",  created_at="2026-03-29T10:00:00Z"),
        ]
        html = _make_ui_router(ctrl).render_dashboard_list()
        self.assertIn("Alpha",              html)
        self.assertIn("Beta",               html)
        self.assertIn("/ui/dashboards/d1",  html)
        self.assertIn("/ui/dashboards/d2",  html)

    def test_renders_empty_state_message(self):
        ctrl = _make_mock_ctrl()
        ctrl.list_dashboards.return_value = []
        html = _make_ui_router(ctrl).render_dashboard_list()
        self.assertIn("No dashboards", html)

    def test_output_is_html_document(self):
        ctrl = _make_mock_ctrl()
        ctrl.list_dashboards.return_value = []
        html = _make_ui_router(ctrl).render_dashboard_list()
        self.assertIn("<!doctype html>", html.lower())
        self.assertIn("<title>",         html)
        self.assertIn("</body>",         html)

    def test_delegates_to_controller_list_dashboards(self):
        ctrl = _make_mock_ctrl()
        ctrl.list_dashboards.return_value = []
        _make_ui_router(ctrl).render_dashboard_list()
        ctrl.list_dashboards.assert_called_once()


class TestRenderDashboardDetail(unittest.TestCase):

    def test_renders_dashboard_name_and_created_at(self):
        ctrl = _make_mock_ctrl()
        d = Dashboard(id="d1", name="Prod Metrics", created_at="2026-03-29T10:00:00Z")
        ctrl.list_dashboards.return_value = [d]
        html = _make_ui_router(ctrl).render_dashboard_detail("d1")
        self.assertIn("Prod Metrics",          html)
        self.assertIn("2026-03-29T10:00:00Z",  html)

    def test_renders_widget_name_unit_and_metric_value(self):
        ctrl = _make_mock_ctrl()
        d    = Dashboard(id="d1", name="Ops", created_at="2026-03-29T10:00:00Z")
        w    = Widget(id="w1", name="CPU Usage", unit="percent", dashboard_id="d1")
        w.values.append(MetricValue(timestamp="2026-03-29T10:00:00Z", value=72.5))
        d.widgets.append(w)
        ctrl.list_dashboards.return_value = [d]
        html = _make_ui_router(ctrl).render_dashboard_detail("d1")
        self.assertIn("CPU Usage",  html)
        self.assertIn("percent",    html)
        self.assertIn("72.5",       html)

    def test_renders_back_link_to_list(self):
        ctrl = _make_mock_ctrl()
        d = Dashboard(id="d1", name="Ops", created_at="2026-03-29T10:00:00Z")
        ctrl.list_dashboards.return_value = [d]
        html = _make_ui_router(ctrl).render_dashboard_detail("d1")
        self.assertIn('href="/ui"', html)

    def test_unknown_dashboard_raises_key_error(self):
        ctrl = _make_mock_ctrl()
        ctrl.list_dashboards.return_value = []
        with self.assertRaises(KeyError):
            _make_ui_router(ctrl).render_dashboard_detail("no-such-id")

    def test_escapes_html_in_dashboard_name(self):
        ctrl = _make_mock_ctrl()
        d    = Dashboard(
            id         = "d1",
            name       = "<script>alert(1)</script>",
            created_at = "2026-03-29T10:00:00Z",
        )
        ctrl.list_dashboards.return_value = [d]
        html = _make_ui_router(ctrl).render_dashboard_detail("d1")
        self.assertNotIn("<script>",      html)
        self.assertIn("&lt;script&gt;",   html)

    def test_no_widgets_message_shown(self):
        ctrl = _make_mock_ctrl()
        d = Dashboard(id="d1", name="Empty", created_at="2026-03-29T10:00:00Z")
        ctrl.list_dashboards.return_value = [d]
        html = _make_ui_router(ctrl).render_dashboard_detail("d1")
        self.assertIn("No widgets", html)

    def test_multiple_metric_values_all_rendered(self):
        ctrl = _make_mock_ctrl()
        d    = Dashboard(id="d1", name="Multi", created_at="2026-03-29T10:00:00Z")
        w    = Widget(id="w1", name="Load", unit="avg", dashboard_id="d1")
        w.values.extend([
            MetricValue(timestamp="2026-03-29T10:00:00Z", value=1.1),
            MetricValue(timestamp="2026-03-29T10:01:00Z", value=2.2),
        ])
        d.widgets.append(w)
        ctrl.list_dashboards.return_value = [d]
        html = _make_ui_router(ctrl).render_dashboard_detail("d1")
        self.assertIn("1.1", html)
        self.assertIn("2.2", html)


if __name__ == "__main__":
    unittest.main()
