"""
Tests for domain/core/models.py and domain/core/commands.py.

One test file per layer (core) within the dashboard use case.
Per AI_CONTRACT.md §6: tests assert raw fixture assumptions, canonical model
field values, and serialized response shape.
"""
import json
import pathlib
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock

RAW_DIR = pathlib.Path(__file__).parents[2] / "fixtures" / "raw" / "dashboard" / "v1"
EXP_DIR = pathlib.Path(__file__).parents[2] / "fixtures" / "expected" / "dashboard" / "v1"


# ---------------------------------------------------------------------------
# Canonical model: Dashboard
# ---------------------------------------------------------------------------

class TestDashboardModel(unittest.TestCase):

    def _load_raw(self, filename: str) -> dict:
        with open(RAW_DIR / filename) as fh:
            return json.load(fh)

    def _load_expected(self, filename: str) -> dict:
        with open(EXP_DIR / filename) as fh:
            return json.load(fh)

    def test_raw_fixture_has_required_fields(self):
        raw = self._load_raw("create_dashboard.0.0.1.json")
        self.assertIn("name", raw)
        self.assertEqual(raw["name"], "Production Metrics")

    def test_expected_fixture_has_required_fields(self):
        expected = self._load_expected("dashboard.0.0.1.json")
        self.assertIn("name", expected)

    def test_valid_dashboard_constructs(self):
        from domain.core.models import Dashboard
        d = Dashboard(id="d1", name="My Board", created_at=datetime.now(timezone.utc))
        self.assertEqual(d.id, "d1")
        self.assertEqual(d.name, "My Board")
        self.assertIsInstance(d.created_at, datetime)

    def test_dashboard_rejects_blank_id(self):
        from domain.core.models import Dashboard
        with self.assertRaises(ValueError):
            Dashboard(id="", name="My Board", created_at=datetime.now(timezone.utc))

    def test_dashboard_rejects_blank_name(self):
        from domain.core.models import Dashboard
        with self.assertRaises(ValueError):
            Dashboard(id="d1", name="   ", created_at=datetime.now(timezone.utc))

    def test_dashboard_rejects_non_datetime_created_at(self):
        from domain.core.models import Dashboard
        with self.assertRaises((ValueError, TypeError)):
            Dashboard(id="d1", name="My Board", created_at="not-a-datetime")


# ---------------------------------------------------------------------------
# Canonical model: MetricWidget
# ---------------------------------------------------------------------------

class TestMetricWidgetModel(unittest.TestCase):

    def _load_raw(self, filename: str) -> dict:
        with open(RAW_DIR / filename) as fh:
            return json.load(fh)

    def _load_expected(self, filename: str) -> dict:
        with open(EXP_DIR / filename) as fh:
            return json.load(fh)

    def test_raw_fixture_has_required_fields(self):
        raw = self._load_raw("add_widget.0.0.1.json")
        self.assertIn("name", raw)
        self.assertIn("unit", raw)
        self.assertEqual(raw["name"], "CPU Usage")
        self.assertEqual(raw["unit"], "percent")

    def test_expected_fixture_has_required_fields(self):
        expected = self._load_expected("widget.0.0.1.json")
        self.assertIn("name", expected)
        self.assertIn("unit", expected)

    def test_valid_widget_constructs(self):
        from domain.core.models import MetricWidget
        w = MetricWidget(id="w1", dashboard_id="d1", name="CPU Usage", unit="percent")
        self.assertEqual(w.id, "w1")
        self.assertEqual(w.dashboard_id, "d1")
        self.assertEqual(w.name, "CPU Usage")
        self.assertEqual(w.unit, "percent")

    def test_widget_rejects_blank_id(self):
        from domain.core.models import MetricWidget
        with self.assertRaises(ValueError):
            MetricWidget(id="", dashboard_id="d1", name="CPU Usage", unit="percent")

    def test_widget_rejects_blank_unit(self):
        from domain.core.models import MetricWidget
        with self.assertRaises(ValueError):
            MetricWidget(id="w1", dashboard_id="d1", name="CPU Usage", unit="")


# ---------------------------------------------------------------------------
# Canonical model: MetricValue
# ---------------------------------------------------------------------------

class TestMetricValueModel(unittest.TestCase):

    def _load_raw(self, filename: str) -> dict:
        with open(RAW_DIR / filename) as fh:
            return json.load(fh)

    def _load_expected(self, filename: str) -> dict:
        with open(EXP_DIR / filename) as fh:
            return json.load(fh)

    def test_raw_fixture_has_required_fields(self):
        raw = self._load_raw("post_metric_value.0.0.1.json")
        self.assertIn("value", raw)
        self.assertEqual(raw["value"], 42.5)

    def test_expected_fixture_has_required_fields(self):
        expected = self._load_expected("metric_value.0.0.1.json")
        self.assertIn("value", expected)

    def test_valid_metric_value_constructs(self):
        from domain.core.models import MetricValue
        v = MetricValue(id="v1", widget_id="w1", value=42.5, recorded_at=datetime.now(timezone.utc))
        self.assertEqual(v.id, "v1")
        self.assertEqual(v.widget_id, "w1")
        self.assertAlmostEqual(v.value, 42.5)

    def test_metric_value_rejects_blank_widget_id(self):
        from domain.core.models import MetricValue
        with self.assertRaises(ValueError):
            MetricValue(id="v1", widget_id="", value=1.0, recorded_at=datetime.now(timezone.utc))

    def test_metric_value_rejects_non_datetime_recorded_at(self):
        from domain.core.models import MetricValue
        with self.assertRaises((ValueError, TypeError)):
            MetricValue(id="v1", widget_id="w1", value=1.0, recorded_at="not-a-datetime")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

class TestCreateDashboardCommand(unittest.TestCase):

    def test_execute_returns_dashboard_with_correct_name(self):
        from domain.core.commands import CreateDashboardCommand
        repo = MagicMock()
        cmd = CreateDashboardCommand(dashboards=repo)
        result = cmd.execute(name="Ops Board")
        self.assertEqual(result.name, "Ops Board")
        self.assertTrue(result.id)
        self.assertIsInstance(result.created_at, datetime)
        repo.save.assert_called_once_with(result)


class TestListDashboardsCommand(unittest.TestCase):

    def test_execute_delegates_to_repository(self):
        from domain.core.commands import ListDashboardsCommand
        from domain.core.models import Dashboard
        d = Dashboard(id="d1", name="X", created_at=datetime.now(timezone.utc))
        repo = MagicMock()
        repo.list_all.return_value = [d]
        cmd = ListDashboardsCommand(dashboards=repo)
        result = cmd.execute()
        self.assertEqual(result, [d])
        repo.list_all.assert_called_once()


class TestAddWidgetCommand(unittest.TestCase):

    def test_execute_returns_widget_when_dashboard_exists(self):
        from domain.core.commands import AddWidgetCommand
        from domain.core.models import Dashboard
        d = Dashboard(id="d1", name="X", created_at=datetime.now(timezone.utc))
        dash_repo = MagicMock()
        dash_repo.get.return_value = d
        widget_repo = MagicMock()
        cmd = AddWidgetCommand(dashboards=dash_repo, widgets=widget_repo)
        result = cmd.execute(dashboard_id="d1", name="Latency", unit="ms")
        self.assertEqual(result.name, "Latency")
        self.assertEqual(result.unit, "ms")
        self.assertEqual(result.dashboard_id, "d1")
        widget_repo.save.assert_called_once_with(result)

    def test_execute_raises_when_dashboard_not_found(self):
        from domain.core.commands import AddWidgetCommand
        dash_repo = MagicMock()
        dash_repo.get.return_value = None
        widget_repo = MagicMock()
        cmd = AddWidgetCommand(dashboards=dash_repo, widgets=widget_repo)
        with self.assertRaises(ValueError):
            cmd.execute(dashboard_id="missing", name="Latency", unit="ms")


class TestPostMetricValueCommand(unittest.TestCase):

    def test_execute_returns_metric_value_when_widget_exists(self):
        from domain.core.commands import PostMetricValueCommand
        from domain.core.models import MetricWidget
        w = MetricWidget(id="w1", dashboard_id="d1", name="CPU", unit="pct")
        widget_repo = MagicMock()
        widget_repo.get.return_value = w
        value_repo = MagicMock()
        cmd = PostMetricValueCommand(widgets=widget_repo, metric_values=value_repo)
        result = cmd.execute(widget_id="w1", value=88.0)
        self.assertAlmostEqual(result.value, 88.0)
        self.assertEqual(result.widget_id, "w1")
        value_repo.append.assert_called_once_with(result)

    def test_execute_raises_when_widget_not_found(self):
        from domain.core.commands import PostMetricValueCommand
        widget_repo = MagicMock()
        widget_repo.get.return_value = None
        value_repo = MagicMock()
        cmd = PostMetricValueCommand(widgets=widget_repo, metric_values=value_repo)
        with self.assertRaises(ValueError):
            cmd.execute(widget_id="missing", value=1.0)


class TestReadWidgetValuesCommand(unittest.TestCase):

    def test_execute_raises_when_widget_not_found(self):
        from domain.core.commands import ReadWidgetValuesCommand
        widget_repo = MagicMock()
        widget_repo.get.return_value = None
        value_repo = MagicMock()
        cmd = ReadWidgetValuesCommand(widgets=widget_repo, metric_values=value_repo)
        with self.assertRaises(ValueError):
            cmd.execute(widget_id="missing")

    def test_execute_returns_values_for_widget(self):
        from domain.core.commands import ReadWidgetValuesCommand
        from domain.core.models import MetricWidget, MetricValue
        w = MetricWidget(id="w1", dashboard_id="d1", name="CPU", unit="pct")
        v = MetricValue(id="v1", widget_id="w1", value=50.0, recorded_at=datetime.now(timezone.utc))
        widget_repo = MagicMock()
        widget_repo.get.return_value = w
        value_repo = MagicMock()
        value_repo.list_by_widget.return_value = [v]
        cmd = ReadWidgetValuesCommand(widgets=widget_repo, metric_values=value_repo)
        result = cmd.execute(widget_id="w1")
        self.assertEqual(result, [v])
        value_repo.list_by_widget.assert_called_once_with("w1")


if __name__ == "__main__":
    unittest.main()
