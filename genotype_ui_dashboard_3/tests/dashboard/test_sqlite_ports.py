"""
test_sqlite_ports.py — SqliteDashboardRepository integration tests.

Uses an in-memory SQLite database (":memory:") to avoid filesystem side-effects.
Asserts save / get / list_all / widget mutation / metric persistence semantics.
"""
import unittest

from domain.dashboard.core.models import Dashboard, MetricValue, Widget


def _make_dashboard(id_="d1", name="Test Dash") -> Dashboard:
    return Dashboard(id=id_, name=name, created_at="2026-03-29T10:00:00Z")


def _make_widget(id_="w1", name="CPU", unit="percent", dashboard_id="d1") -> Widget:
    return Widget(id=id_, name=name, unit=unit, dashboard_id=dashboard_id)


class TestSqliteDashboardRepository(unittest.TestCase):

    def setUp(self):
        from domain.dashboard.core.ports.sqlite_dashboard_repository import (
            SqliteDashboardRepository,
        )
        self.repo = SqliteDashboardRepository(db_path=":memory:")

    def test_save_and_get_returns_dashboard(self):
        d = _make_dashboard()
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertIsNotNone(result)
        self.assertEqual(result.id,   "d1")
        self.assertEqual(result.name, "Test Dash")

    def test_get_unknown_id_returns_none(self):
        self.assertIsNone(self.repo.get("nonexistent"))

    def test_list_all_empty(self):
        self.assertEqual(self.repo.list_all(), [])

    def test_list_all_returns_all_saved(self):
        self.repo.save(_make_dashboard("d1", "Alpha"))
        self.repo.save(_make_dashboard("d2", "Beta"))
        results = self.repo.list_all()
        self.assertEqual(len(results), 2)
        names = {d.name for d in results}
        self.assertIn("Alpha", names)
        self.assertIn("Beta",  names)

    def test_save_overwrites_existing(self):
        d = _make_dashboard()
        self.repo.save(d)
        d.name = "Updated"
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual(result.name, "Updated")

    def test_widget_stored_within_dashboard(self):
        d = _make_dashboard()
        w = _make_widget(dashboard_id="d1")
        d.widgets.append(w)
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual(len(result.widgets), 1)
        self.assertEqual(result.widgets[0].id, "w1")

    def test_metric_value_stored_within_widget(self):
        d = _make_dashboard()
        w = _make_widget(dashboard_id="d1")
        mv = MetricValue(timestamp="2026-03-29T10:00:00Z", value=42.0)
        w.values.append(mv)
        d.widgets.append(w)
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual(len(result.widgets[0].values), 1)
        self.assertEqual(result.widgets[0].values[0].value, 42.0)

    def test_metric_values_preserved_in_insertion_order(self):
        d = _make_dashboard()
        w = _make_widget(dashboard_id="d1")
        w.values.extend([
            MetricValue(timestamp="2026-03-29T10:00:00Z", value=1.0),
            MetricValue(timestamp="2026-03-29T10:01:00Z", value=2.0),
            MetricValue(timestamp="2026-03-29T10:02:00Z", value=3.0),
        ])
        d.widgets.append(w)
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual([mv.value for mv in result.widgets[0].values], [1.0, 2.0, 3.0])

    def test_stale_widget_removed_on_overwrite(self):
        d = _make_dashboard()
        w = _make_widget(id_="w1", dashboard_id="d1")
        d.widgets.append(w)
        self.repo.save(d)
        d.widgets.clear()
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual(result.widgets, [])

    def test_created_at_round_trips(self):
        d = _make_dashboard()
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual(result.created_at, "2026-03-29T10:00:00Z")

    def test_multiple_widgets_stored(self):
        d  = _make_dashboard()
        w1 = _make_widget(id_="w1", name="CPU",    unit="percent",  dashboard_id="d1")
        w2 = _make_widget(id_="w2", name="Memory", unit="megabytes", dashboard_id="d1")
        d.widgets.extend([w1, w2])
        self.repo.save(d)
        result = self.repo.get("d1")
        self.assertEqual(len(result.widgets), 2)
        ids = {w.id for w in result.widgets}
        self.assertIn("w1", ids)
        self.assertIn("w2", ids)


if __name__ == "__main__":
    unittest.main()
