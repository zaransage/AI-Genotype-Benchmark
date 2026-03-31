"""
Tests for domain/core/ports/ — in-memory repository implementations.

One test file per layer (ports) within the dashboard use case.
Per AI_CONTRACT.md §6: tests assert canonical model field values and
repository contract behaviour.
"""
import unittest
from datetime import datetime, timezone

from domain.core.models import Dashboard, MetricWidget, MetricValue


def _dashboard(id_: str = "d1", name: str = "Test Board") -> Dashboard:
    return Dashboard(id=id_, name=name, created_at=datetime.now(timezone.utc))


def _widget(id_: str = "w1", dashboard_id: str = "d1") -> MetricWidget:
    return MetricWidget(id=id_, dashboard_id=dashboard_id, name="CPU", unit="pct")


def _value(id_: str = "v1", widget_id: str = "w1", value: float = 10.0) -> MetricValue:
    return MetricValue(id=id_, widget_id=widget_id, value=value, recorded_at=datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# InMemoryDashboardRepository
# ---------------------------------------------------------------------------

class TestInMemoryDashboardRepository(unittest.TestCase):

    def setUp(self):
        from domain.core.ports.in_memory_dashboard_repository import InMemoryDashboardRepository
        self.repo = InMemoryDashboardRepository()

    def test_save_and_get_returns_dashboard(self):
        d = _dashboard()
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual(result, d)

    def test_get_returns_none_for_missing_id(self):
        result = self.repo.get("nonexistent")
        self.assertIsNone(result)

    def test_list_all_returns_empty_initially(self):
        self.assertEqual(self.repo.list_all(), [])

    def test_list_all_returns_all_saved_dashboards(self):
        d1 = _dashboard("d1", "Alpha")
        d2 = _dashboard("d2", "Beta")
        self.repo.save(d1)
        self.repo.save(d2)
        result = self.repo.list_all()
        self.assertIn(d1, result)
        self.assertIn(d2, result)
        self.assertEqual(len(result), 2)

    def test_save_overwrites_existing_dashboard(self):
        d = _dashboard()
        self.repo.save(d)
        updated = Dashboard(id="d1", name="Updated", created_at=d.created_at)
        self.repo.save(updated)
        self.assertEqual(self.repo.get("d1").name, "Updated")


# ---------------------------------------------------------------------------
# InMemoryWidgetRepository
# ---------------------------------------------------------------------------

class TestInMemoryWidgetRepository(unittest.TestCase):

    def setUp(self):
        from domain.core.ports.in_memory_widget_repository import InMemoryWidgetRepository
        self.repo = InMemoryWidgetRepository()

    def test_save_and_get_returns_widget(self):
        w = _widget()
        self.repo.save(w)
        result = self.repo.get("w1")
        self.assertEqual(result, w)

    def test_get_returns_none_for_missing_id(self):
        self.assertIsNone(self.repo.get("nonexistent"))

    def test_list_by_dashboard_returns_only_matching_widgets(self):
        w1 = _widget("w1", "d1")
        w2 = _widget("w2", "d1")
        w3 = _widget("w3", "d2")
        self.repo.save(w1)
        self.repo.save(w2)
        self.repo.save(w3)
        result = self.repo.list_by_dashboard("d1")
        self.assertIn(w1, result)
        self.assertIn(w2, result)
        self.assertNotIn(w3, result)

    def test_list_by_dashboard_returns_empty_for_unknown_dashboard(self):
        self.assertEqual(self.repo.list_by_dashboard("unknown"), [])


# ---------------------------------------------------------------------------
# InMemoryMetricValueRepository
# ---------------------------------------------------------------------------

class TestInMemoryMetricValueRepository(unittest.TestCase):

    def setUp(self):
        from domain.core.ports.in_memory_metric_value_repository import InMemoryMetricValueRepository
        self.repo = InMemoryMetricValueRepository()

    def test_append_and_list_by_widget(self):
        v = _value()
        self.repo.append(v)
        result = self.repo.list_by_widget("w1")
        self.assertIn(v, result)

    def test_list_by_widget_returns_empty_for_unknown_widget(self):
        self.assertEqual(self.repo.list_by_widget("unknown"), [])

    def test_list_by_widget_returns_only_matching_values(self):
        v1 = _value("v1", "w1", 10.0)
        v2 = _value("v2", "w1", 20.0)
        v3 = _value("v3", "w2", 30.0)
        self.repo.append(v1)
        self.repo.append(v2)
        self.repo.append(v3)
        result = self.repo.list_by_widget("w1")
        self.assertIn(v1, result)
        self.assertIn(v2, result)
        self.assertNotIn(v3, result)

    def test_multiple_appends_preserve_order(self):
        v1 = _value("v1", "w1", 1.0)
        v2 = _value("v2", "w1", 2.0)
        self.repo.append(v1)
        self.repo.append(v2)
        result = self.repo.list_by_widget("w1")
        self.assertEqual(result[0], v1)
        self.assertEqual(result[1], v2)


if __name__ == "__main__":
    unittest.main()
