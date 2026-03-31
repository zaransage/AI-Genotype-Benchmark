"""
test_adaptors.py — DashboardController use-case tests with a mock repository.

Each test mocks IDashboardRepository to isolate controller logic from storage.
Fixture payloads are loaded via json.load — never hardcoded inline.
"""
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

FIXTURE_RAW      = Path(__file__).parents[2] / "fixtures" / "raw"      / "dashboard" / "v1"
FIXTURE_EXPECTED = Path(__file__).parents[2] / "fixtures" / "expected" / "dashboard" / "v1"


def _make_mock_repo():
    from domain.dashboard.core.ports.i_dashboard_repository import IDashboardRepository
    return MagicMock(spec=IDashboardRepository)


def _make_controller(repo=None):
    from domain.dashboard.core.adaptors.dashboard_controller import DashboardController
    return DashboardController(repository=repo or _make_mock_repo())


class TestCreateDashboard(unittest.TestCase):

    def test_creates_and_saves_dashboard(self):
        """create_dashboard returns a Dashboard with correct name and saves it."""
        raw      = json.load(open(FIXTURE_RAW      / "create_dashboard.0.0.1.json"))
        expected = json.load(open(FIXTURE_EXPECTED / "create_dashboard.0.0.1.json"))

        repo = _make_mock_repo()
        ctrl = _make_controller(repo)
        result = ctrl.create_dashboard(name=raw["name"])

        self.assertEqual(result.name,    expected["name"])
        self.assertEqual(result.widgets, expected["widgets"])
        self.assertTrue(len(result.id) > 0)
        repo.save.assert_called_once_with(result)

    def test_empty_name_raises(self):
        with self.assertRaises(ValueError):
            _make_controller().create_dashboard(name="")


class TestListDashboards(unittest.TestCase):

    def test_delegates_to_repository(self):
        from domain.dashboard.core.models import Dashboard
        repo = _make_mock_repo()
        repo.list_all.return_value = [
            Dashboard(id="d1", name="Alpha", created_at="2026-03-29T10:00:00Z"),
            Dashboard(id="d2", name="Beta",  created_at="2026-03-29T10:00:00Z"),
        ]
        ctrl = _make_controller(repo)
        results = ctrl.list_dashboards()
        self.assertEqual(len(results), 2)
        repo.list_all.assert_called_once()


class TestAddWidget(unittest.TestCase):

    def test_adds_widget_to_existing_dashboard(self):
        """add_widget appends a Widget and re-saves the dashboard."""
        from domain.dashboard.core.models import Dashboard
        raw      = json.load(open(FIXTURE_RAW      / "add_widget.0.0.1.json"))
        expected = json.load(open(FIXTURE_EXPECTED / "add_widget.0.0.1.json"))

        repo = _make_mock_repo()
        repo.get.return_value = Dashboard(id="d1", name="Prod", created_at="2026-03-29T10:00:00Z")
        ctrl = _make_controller(repo)

        widget = ctrl.add_widget(dashboard_id="d1", name=raw["name"], unit=raw["unit"])

        self.assertEqual(widget.name,   expected["name"])
        self.assertEqual(widget.unit,   expected["unit"])
        self.assertEqual(widget.values, expected["values"])
        repo.save.assert_called_once()

    def test_dashboard_not_found_raises(self):
        repo = _make_mock_repo()
        repo.get.return_value = None
        with self.assertRaises(KeyError):
            _make_controller(repo).add_widget("missing", "CPU", "percent")


class TestPostMetric(unittest.TestCase):

    def test_posts_metric_to_existing_widget(self):
        """post_metric appends a MetricValue and re-saves the dashboard."""
        from domain.dashboard.core.models import Dashboard, Widget
        raw      = json.load(open(FIXTURE_RAW      / "post_metric.0.0.1.json"))
        expected = json.load(open(FIXTURE_EXPECTED / "post_metric.0.0.1.json"))

        d = Dashboard(id="d1", name="Prod", created_at="2026-03-29T10:00:00Z")
        w = Widget(id="w1", name="CPU", unit="percent", dashboard_id="d1")
        d.widgets.append(w)

        repo = _make_mock_repo()
        repo.get.return_value = d
        ctrl = _make_controller(repo)

        mv = ctrl.post_metric(
            dashboard_id="d1",
            widget_id="w1",
            value=raw["value"],
            timestamp=raw["timestamp"],
        )

        self.assertEqual(mv.value,     expected["value"])
        self.assertEqual(mv.timestamp, expected["timestamp"])
        repo.save.assert_called_once()

    def test_dashboard_not_found_raises(self):
        repo = _make_mock_repo()
        repo.get.return_value = None
        with self.assertRaises(KeyError):
            _make_controller(repo).post_metric("missing", "w1", 1.0, "2026-03-29T10:00:00Z")

    def test_widget_not_found_raises(self):
        from domain.dashboard.core.models import Dashboard
        repo = _make_mock_repo()
        repo.get.return_value = Dashboard(id="d1", name="Prod", created_at="2026-03-29T10:00:00Z")
        with self.assertRaises(KeyError):
            _make_controller(repo).post_metric("d1", "no-such-widget", 1.0, "2026-03-29T10:00:00Z")


class TestGetWidget(unittest.TestCase):

    def test_returns_widget_with_values(self):
        from domain.dashboard.core.models import Dashboard, Widget, MetricValue
        d = Dashboard(id="d1", name="Prod", created_at="2026-03-29T10:00:00Z")
        w = Widget(id="w1", name="CPU", unit="percent", dashboard_id="d1")
        w.values.append(MetricValue(timestamp="2026-03-29T10:00:00Z", value=55.0))
        d.widgets.append(w)

        repo = _make_mock_repo()
        repo.get.return_value = d
        ctrl = _make_controller(repo)

        result = ctrl.get_widget("d1", "w1")
        self.assertEqual(result.id,            "w1")
        self.assertEqual(len(result.values),   1)
        self.assertEqual(result.values[0].value, 55.0)

    def test_widget_not_found_raises(self):
        from domain.dashboard.core.models import Dashboard
        repo = _make_mock_repo()
        repo.get.return_value = Dashboard(id="d1", name="Prod", created_at="2026-03-29T10:00:00Z")
        with self.assertRaises(KeyError):
            _make_controller(repo).get_widget("d1", "missing")


if __name__ == "__main__":
    unittest.main()
