"""
Tests for domain/dashboard/core — canonical models and commands.

One test file per layer per use case (AI_CONTRACT.md §5).
Tests assert:
  1. raw fixture integrity (expected source fields present)
  2. canonical dataclass field values after construction / command execution
"""

import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURES_RAW = Path(__file__).parents[2] / "fixtures" / "raw" / "dashboard" / "v1"
FIXTURES_EXP = Path(__file__).parents[2] / "fixtures" / "expected" / "dashboard" / "v1"


def load_raw(filename: str) -> dict:
    with open(FIXTURES_RAW / filename) as fh:
        return json.load(fh)


def load_expected(filename: str) -> dict:
    with open(FIXTURES_EXP / filename) as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Import domain under test (written after tests per ADR-0001)
# ---------------------------------------------------------------------------

from domain.dashboard.core.models import Dashboard, MetricValue, Widget
from domain.dashboard.core.commands import (
    AddWidgetCommand,
    CreateDashboardCommand,
    ListDashboardsCommand,
    PostMetricCommand,
    ReadWidgetValuesCommand,
)


class TestDashboardModel(unittest.TestCase):
    """Canonical dataclass — Dashboard."""

    def test_fixture_raw_create_has_required_fields(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        self.assertIn("name", raw)

    def test_fixture_expected_dashboard_shape(self):
        exp = load_expected("dashboard.0.0.1.json")
        self.assertIn("id", exp)
        self.assertIn("name", exp)
        self.assertIn("widget_ids", exp)

    def test_dashboard_stores_name(self):
        d = Dashboard(id="d1", name="Prod")
        self.assertEqual(d.name, "Prod")
        self.assertEqual(d.id, "d1")
        self.assertEqual(d.widget_ids, [])

    def test_dashboard_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            Dashboard(id="d1", name="")

    def test_dashboard_rejects_blank_name(self):
        with self.assertRaises(ValueError):
            Dashboard(id="d1", name="   ")


class TestWidgetModel(unittest.TestCase):
    """Canonical dataclass — Widget."""

    def test_fixture_raw_add_widget_has_required_fields(self):
        raw = load_raw("add_widget.0.0.1.json")
        self.assertIn("name", raw)
        self.assertIn("metric_name", raw)

    def test_fixture_expected_widget_shape(self):
        exp = load_expected("widget.0.0.1.json")
        self.assertIn("id", exp)
        self.assertIn("dashboard_id", exp)
        self.assertIn("name", exp)
        self.assertIn("metric_name", exp)
        self.assertIn("values", exp)

    def test_widget_stores_fields(self):
        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu_pct")
        self.assertEqual(w.name, "CPU")
        self.assertEqual(w.metric_name, "cpu_pct")
        self.assertEqual(w.values, [])

    def test_widget_rejects_empty_name(self):
        with self.assertRaises(ValueError):
            Widget(id="w1", dashboard_id="d1", name="", metric_name="cpu")

    def test_widget_rejects_empty_metric_name(self):
        with self.assertRaises(ValueError):
            Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="")


class TestMetricValueModel(unittest.TestCase):
    """Canonical dataclass — MetricValue."""

    def test_fixture_raw_post_metric_has_required_fields(self):
        raw = load_raw("post_metric.0.0.1.json")
        self.assertIn("value", raw)

    def test_fixture_expected_metric_value_shape(self):
        exp = load_expected("metric_value.0.0.1.json")
        self.assertIn("value", exp)
        self.assertIn("recorded_at", exp)

    def test_metric_value_stores_fields(self):
        mv = MetricValue(value=42.0, recorded_at="2026-03-29T07:00:00Z")
        self.assertEqual(mv.value, 42.0)
        self.assertEqual(mv.recorded_at, "2026-03-29T07:00:00Z")

    def test_metric_value_recorded_at_matches_date_format_constant(self):
        mv = MetricValue(value=1.0, recorded_at="2026-03-29T07:00:00Z")
        import re
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
        self.assertRegex(mv.recorded_at, pattern)


class TestCreateDashboardCommand(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()

    def test_creates_dashboard_with_given_name(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        cmd = CreateDashboardCommand(repo=self.repo)
        result = cmd.execute(name=raw["name"])
        self.assertEqual(result.name, raw["name"])
        self.assertIsInstance(result.id, str)
        self.assertTrue(len(result.id) > 0)

    def test_saves_dashboard_to_repo(self):
        cmd = CreateDashboardCommand(repo=self.repo)
        result = cmd.execute(name="Test")
        self.repo.save_dashboard.assert_called_once_with(result)

    def test_raises_on_empty_name(self):
        cmd = CreateDashboardCommand(repo=self.repo)
        with self.assertRaises(ValueError):
            cmd.execute(name="")


class TestListDashboardsCommand(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()

    def test_returns_repo_list(self):
        d1 = Dashboard(id="d1", name="Alpha")
        d2 = Dashboard(id="d2", name="Beta")
        self.repo.list_dashboards.return_value = [d1, d2]
        cmd = ListDashboardsCommand(repo=self.repo)
        result = cmd.execute()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "Alpha")


class TestAddWidgetCommand(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.dashboard = Dashboard(id="dash-001", name="Prod")
        self.repo.get_dashboard.return_value = self.dashboard

    def test_adds_widget_and_returns_it(self):
        raw = load_raw("add_widget.0.0.1.json")
        cmd = AddWidgetCommand(repo=self.repo)
        result = cmd.execute(
            dashboard_id="dash-001",
            name=raw["name"],
            metric_name=raw["metric_name"],
        )
        self.assertEqual(result.name, raw["name"])
        self.assertEqual(result.metric_name, raw["metric_name"])
        self.assertEqual(result.dashboard_id, "dash-001")

    def test_raises_404_equivalent_when_dashboard_missing(self):
        self.repo.get_dashboard.return_value = None
        cmd = AddWidgetCommand(repo=self.repo)
        with self.assertRaises(LookupError):
            cmd.execute(dashboard_id="missing", name="W", metric_name="m")

    def test_widget_id_appended_to_dashboard(self):
        raw = load_raw("add_widget.0.0.1.json")
        cmd = AddWidgetCommand(repo=self.repo)
        result = cmd.execute(
            dashboard_id="dash-001",
            name=raw["name"],
            metric_name=raw["metric_name"],
        )
        self.assertIn(result.id, self.dashboard.widget_ids)


class TestPostMetricCommand(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.widget = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        self.repo.get_widget.return_value = self.widget

    def test_appends_metric_value(self):
        raw = load_raw("post_metric.0.0.1.json")
        cmd = PostMetricCommand(repo=self.repo)
        result = cmd.execute(widget_id="w1", value=raw["value"])
        self.assertEqual(result.value, raw["value"])
        self.assertIn(result, self.widget.values)

    def test_raises_lookup_error_when_widget_missing(self):
        self.repo.get_widget.return_value = None
        cmd = PostMetricCommand(repo=self.repo)
        with self.assertRaises(LookupError):
            cmd.execute(widget_id="missing", value=1.0)

    def test_recorded_at_is_iso_format(self):
        cmd = PostMetricCommand(repo=self.repo)
        result = cmd.execute(widget_id="w1", value=99.9)
        import re
        self.assertRegex(result.recorded_at, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class TestReadWidgetValuesCommand(unittest.TestCase):
    def setUp(self):
        self.repo = MagicMock()
        self.widget = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        mv = MetricValue(value=73.4, recorded_at="2026-03-29T07:00:00Z")
        self.widget.values.append(mv)
        self.repo.get_widget.return_value = self.widget

    def test_returns_values_list(self):
        cmd = ReadWidgetValuesCommand(repo=self.repo)
        result = cmd.execute(widget_id="w1")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].value, 73.4)

    def test_raises_lookup_error_when_widget_missing(self):
        self.repo.get_widget.return_value = None
        cmd = ReadWidgetValuesCommand(repo=self.repo)
        with self.assertRaises(LookupError):
            cmd.execute(widget_id="missing")


if __name__ == "__main__":
    unittest.main()
