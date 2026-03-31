"""
test_core.py — canonical model validation tests.

Asserts:
  1. Raw fixture contains expected source fields.
  2. Canonical dataclass instances have correct field values.
  3. __post_init__ validation raises on bad input.
"""
import json
import unittest
from pathlib import Path

FIXTURE_RAW      = Path(__file__).parents[2] / "fixtures" / "raw"      / "dashboard" / "v1"
FIXTURE_EXPECTED = Path(__file__).parents[2] / "fixtures" / "expected" / "dashboard" / "v1"


class TestMetricValueModel(unittest.TestCase):

    def test_valid_metric_value(self):
        from domain.dashboard.core.models import MetricValue
        mv = MetricValue(timestamp="2026-03-29T10:00:00Z", value=72.5)
        self.assertEqual(mv.timestamp, "2026-03-29T10:00:00Z")
        self.assertEqual(mv.value, 72.5)

    def test_empty_timestamp_raises(self):
        from domain.dashboard.core.models import MetricValue
        with self.assertRaises(ValueError):
            MetricValue(timestamp="", value=1.0)

    def test_fixture_raw_fields(self):
        """Raw fixture contains the expected source fields."""
        raw = json.load(open(FIXTURE_RAW / "post_metric.0.0.1.json"))
        self.assertIn("value",     raw)
        self.assertIn("timestamp", raw)

    def test_fixture_canonical_mapping(self):
        """Canonical MetricValue matches expected fixture output."""
        from domain.dashboard.core.models import MetricValue
        raw      = json.load(open(FIXTURE_RAW      / "post_metric.0.0.1.json"))
        expected = json.load(open(FIXTURE_EXPECTED / "post_metric.0.0.1.json"))
        mv = MetricValue(timestamp=raw["timestamp"], value=raw["value"])
        self.assertEqual(mv.value,     expected["value"])
        self.assertEqual(mv.timestamp, expected["timestamp"])


class TestWidgetModel(unittest.TestCase):

    def test_valid_widget(self):
        from domain.dashboard.core.models import Widget
        w = Widget(id="w1", name="CPU Usage", unit="percent", dashboard_id="d1")
        self.assertEqual(w.name, "CPU Usage")
        self.assertEqual(w.unit, "percent")
        self.assertEqual(w.values, [])

    def test_empty_name_raises(self):
        from domain.dashboard.core.models import Widget
        with self.assertRaises(ValueError):
            Widget(id="w1", name="", unit="percent", dashboard_id="d1")

    def test_empty_unit_raises(self):
        from domain.dashboard.core.models import Widget
        with self.assertRaises(ValueError):
            Widget(id="w1", name="CPU", unit="", dashboard_id="d1")

    def test_fixture_raw_fields(self):
        """Raw add_widget fixture contains name and unit fields."""
        raw = json.load(open(FIXTURE_RAW / "add_widget.0.0.1.json"))
        self.assertIn("name", raw)
        self.assertIn("unit", raw)

    def test_fixture_canonical_mapping(self):
        """Canonical Widget matches expected fixture output."""
        from domain.dashboard.core.models import Widget
        raw      = json.load(open(FIXTURE_RAW      / "add_widget.0.0.1.json"))
        expected = json.load(open(FIXTURE_EXPECTED / "add_widget.0.0.1.json"))
        w = Widget(id="w1", name=raw["name"], unit=raw["unit"], dashboard_id="d1")
        self.assertEqual(w.name,   expected["name"])
        self.assertEqual(w.unit,   expected["unit"])
        self.assertEqual(w.values, expected["values"])


class TestDashboardModel(unittest.TestCase):

    def test_valid_dashboard(self):
        from domain.dashboard.core.models import Dashboard
        d = Dashboard(id="d1", name="Production Metrics", created_at="2026-03-29T10:00:00Z")
        self.assertEqual(d.name, "Production Metrics")
        self.assertEqual(d.widgets, [])

    def test_empty_name_raises(self):
        from domain.dashboard.core.models import Dashboard
        with self.assertRaises(ValueError):
            Dashboard(id="d1", name="", created_at="2026-03-29T10:00:00Z")

    def test_empty_created_at_raises(self):
        from domain.dashboard.core.models import Dashboard
        with self.assertRaises(ValueError):
            Dashboard(id="d1", name="Dash", created_at="")

    def test_fixture_raw_fields(self):
        """Raw create_dashboard fixture contains a name field."""
        raw = json.load(open(FIXTURE_RAW / "create_dashboard.0.0.1.json"))
        self.assertIn("name", raw)

    def test_fixture_canonical_mapping(self):
        """Canonical Dashboard matches expected fixture output."""
        from domain.dashboard.core.models import Dashboard
        raw      = json.load(open(FIXTURE_RAW      / "create_dashboard.0.0.1.json"))
        expected = json.load(open(FIXTURE_EXPECTED / "create_dashboard.0.0.1.json"))
        d = Dashboard(id="d1", name=raw["name"], created_at="2026-03-29T10:00:00Z")
        self.assertEqual(d.name,    expected["name"])
        self.assertEqual(d.widgets, expected["widgets"])


if __name__ == "__main__":
    unittest.main()
