"""
Tests for domain/dashboard/core/ports — SQLite outbound repository implementation.

Verifies that SqliteDashboardRepo satisfies the IDashboardRepo contract.
An in-memory SQLite database (":memory:") is used so tests are fast,
isolated, and leave no files on disk (AI_CONTRACT.md §1).
"""

import json
import unittest
from pathlib import Path

FIXTURES_EXP = Path(__file__).parents[2] / "fixtures" / "expected" / "dashboard" / "v1"


def load_expected(filename: str) -> dict:
    with open(FIXTURES_EXP / filename) as fh:
        return json.load(fh)


from domain.dashboard.core.models import Dashboard, MetricValue, Widget
from domain.dashboard.core.ports.i_dashboard_repo import IDashboardRepo
from domain.dashboard.core.ports.sqlite_dashboard_repo import SqliteDashboardRepo


class TestSqliteDashboardRepoInterface(unittest.TestCase):
    """SqliteDashboardRepo implements the IDashboardRepo contract."""

    def setUp(self):
        self.repo = SqliteDashboardRepo(db_path=":memory:")

    def test_repo_is_instance_of_interface(self):
        self.assertIsInstance(self.repo, IDashboardRepo)

    def test_interface_methods_present(self):
        for method in ("save_dashboard", "get_dashboard", "list_dashboards",
                       "save_widget", "get_widget"):
            self.assertTrue(hasattr(self.repo, method))


class TestSqliteDashboardCRUD(unittest.TestCase):
    """Dashboard persistence via SQLite."""

    def setUp(self):
        self.repo = SqliteDashboardRepo(db_path=":memory:")

    # -- fixture integrity ---------------------------------------------------

    def test_expected_dashboard_fixture_shape(self):
        exp = load_expected("dashboard.0.0.1.json")
        for key in ("id", "name", "widget_ids"):
            self.assertIn(key, exp)

    # -- save / get ----------------------------------------------------------

    def test_save_and_get_dashboard(self):
        d = Dashboard(id="d1", name="Production")
        self.repo.save_dashboard(d)
        got = self.repo.get_dashboard("d1")
        self.assertIsNotNone(got)
        self.assertEqual(got.name, "Production")
        self.assertEqual(got.id, "d1")

    def test_get_dashboard_returns_none_for_unknown_id(self):
        result = self.repo.get_dashboard("nope")
        self.assertIsNone(result)

    def test_save_dashboard_overwrites_on_same_id(self):
        self.repo.save_dashboard(Dashboard(id="d1", name="Original"))
        self.repo.save_dashboard(Dashboard(id="d1", name="Updated"))
        got = self.repo.get_dashboard("d1")
        self.assertEqual(got.name, "Updated")

    def test_list_dashboards_empty_at_start(self):
        self.assertEqual(self.repo.list_dashboards(), [])

    def test_list_dashboards_returns_all_saved(self):
        self.repo.save_dashboard(Dashboard(id="d1", name="Alpha"))
        self.repo.save_dashboard(Dashboard(id="d2", name="Beta"))
        result = self.repo.list_dashboards()
        self.assertEqual(len(result), 2)

    def test_list_dashboards_count_stable_on_overwrite(self):
        self.repo.save_dashboard(Dashboard(id="d1", name="A"))
        self.repo.save_dashboard(Dashboard(id="d1", name="B"))
        self.assertEqual(len(self.repo.list_dashboards()), 1)

    # -- widget_ids order preserved ------------------------------------------

    def test_widget_ids_order_preserved(self):
        d = Dashboard(id="d1", name="Dash", widget_ids=["w3", "w1", "w2"])
        self.repo.save_dashboard(d)
        got = self.repo.get_dashboard("d1")
        self.assertEqual(got.widget_ids, ["w3", "w1", "w2"])

    def test_widget_ids_update_on_resave(self):
        d = Dashboard(id="d1", name="Dash", widget_ids=["w1"])
        self.repo.save_dashboard(d)
        d.widget_ids.append("w2")
        self.repo.save_dashboard(d)
        got = self.repo.get_dashboard("d1")
        self.assertEqual(got.widget_ids, ["w1", "w2"])


class TestSqliteWidgetCRUD(unittest.TestCase):
    """Widget persistence via SQLite."""

    def setUp(self):
        self.repo = SqliteDashboardRepo(db_path=":memory:")

    # -- fixture integrity ---------------------------------------------------

    def test_expected_widget_fixture_shape(self):
        exp = load_expected("widget.0.0.1.json")
        for key in ("id", "dashboard_id", "name", "metric_name", "values"):
            self.assertIn(key, exp)

    # -- save / get ----------------------------------------------------------

    def test_save_and_get_widget(self):
        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu_pct")
        self.repo.save_widget(w)
        got = self.repo.get_widget("w1")
        self.assertIsNotNone(got)
        self.assertEqual(got.name, "CPU")
        self.assertEqual(got.metric_name, "cpu_pct")
        self.assertEqual(got.dashboard_id, "d1")

    def test_get_widget_returns_none_for_unknown_id(self):
        self.assertIsNone(self.repo.get_widget("nope"))

    def test_save_widget_overwrites_on_same_id(self):
        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        self.repo.save_widget(w)
        w2 = Widget(id="w1", dashboard_id="d1", name="Memory", metric_name="mem")
        self.repo.save_widget(w2)
        got = self.repo.get_widget("w1")
        self.assertEqual(got.name, "Memory")

    # -- metric values -------------------------------------------------------

    def test_metric_values_persisted_in_order(self):
        exp = load_expected("metric_value.0.0.1.json")
        self.assertIn("value", exp)
        self.assertIn("recorded_at", exp)

        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        mv1 = MetricValue(value=10.0, recorded_at="2026-03-29T07:00:00Z")
        mv2 = MetricValue(value=20.0, recorded_at="2026-03-29T07:01:00Z")
        w.values.extend([mv1, mv2])
        self.repo.save_widget(w)

        got = self.repo.get_widget("w1")
        self.assertEqual(len(got.values), 2)
        self.assertEqual(got.values[0].value, 10.0)
        self.assertEqual(got.values[1].value, 20.0)

    def test_metric_values_replaced_on_resave(self):
        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        w.values.append(MetricValue(value=99.0, recorded_at="2026-03-29T07:00:00Z"))
        self.repo.save_widget(w)

        # replace values
        w.values.clear()
        w.values.append(MetricValue(value=1.0, recorded_at="2026-03-29T08:00:00Z"))
        self.repo.save_widget(w)

        got = self.repo.get_widget("w1")
        self.assertEqual(len(got.values), 1)
        self.assertEqual(got.values[0].value, 1.0)

    def test_widget_with_no_values_returns_empty_list(self):
        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        self.repo.save_widget(w)
        got = self.repo.get_widget("w1")
        self.assertEqual(got.values, [])


class TestSqliteIsolation(unittest.TestCase):
    """Each test gets a fresh in-memory database — no cross-test leakage."""

    def setUp(self):
        self.repo = SqliteDashboardRepo(db_path=":memory:")

    def test_fresh_repo_has_no_dashboards(self):
        self.assertEqual(self.repo.list_dashboards(), [])

    def test_fresh_repo_returns_none_for_any_widget(self):
        self.assertIsNone(self.repo.get_widget("any"))


if __name__ == "__main__":
    unittest.main()
