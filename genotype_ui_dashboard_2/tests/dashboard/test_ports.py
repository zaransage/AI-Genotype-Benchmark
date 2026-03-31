"""
Tests for domain/dashboard/core/ports — outbound repository contract.

Verifies that InMemoryDashboardRepo satisfies the IDashboardRepo contract.
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
from domain.dashboard.core.ports.in_memory_dashboard_repo import InMemoryDashboardRepo


class TestIDashboardRepoInterface(unittest.TestCase):
    """IDashboardRepo is an abstract interface — cannot be instantiated."""

    def test_cannot_instantiate_interface_directly(self):
        with self.assertRaises(TypeError):
            IDashboardRepo()  # type: ignore[abstract]

    def test_interface_declares_save_dashboard(self):
        self.assertTrue(hasattr(IDashboardRepo, "save_dashboard"))

    def test_interface_declares_get_dashboard(self):
        self.assertTrue(hasattr(IDashboardRepo, "get_dashboard"))

    def test_interface_declares_list_dashboards(self):
        self.assertTrue(hasattr(IDashboardRepo, "list_dashboards"))

    def test_interface_declares_save_widget(self):
        self.assertTrue(hasattr(IDashboardRepo, "save_widget"))

    def test_interface_declares_get_widget(self):
        self.assertTrue(hasattr(IDashboardRepo, "get_widget"))


class TestInMemoryDashboardRepo(unittest.TestCase):
    """InMemoryDashboardRepo satisfies the IDashboardRepo contract."""

    def setUp(self):
        self.repo = InMemoryDashboardRepo()

    # -- fixture integrity ---------------------------------------------------

    def test_expected_dashboard_fixture_has_id_and_name(self):
        exp = load_expected("dashboard.0.0.1.json")
        self.assertIn("id", exp)
        self.assertIn("name", exp)

    def test_expected_widget_fixture_has_required_fields(self):
        exp = load_expected("widget.0.0.1.json")
        for field in ("id", "dashboard_id", "name", "metric_name"):
            self.assertIn(field, exp)

    # -- dashboard operations ------------------------------------------------

    def test_save_and_get_dashboard(self):
        d = Dashboard(id="d1", name="Prod")
        self.repo.save_dashboard(d)
        retrieved = self.repo.get_dashboard("d1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Prod")

    def test_get_dashboard_returns_none_for_unknown_id(self):
        result = self.repo.get_dashboard("unknown")
        self.assertIsNone(result)

    def test_list_dashboards_empty_at_start(self):
        self.assertEqual(self.repo.list_dashboards(), [])

    def test_list_dashboards_returns_all_saved(self):
        self.repo.save_dashboard(Dashboard(id="d1", name="Alpha"))
        self.repo.save_dashboard(Dashboard(id="d2", name="Beta"))
        result = self.repo.list_dashboards()
        self.assertEqual(len(result), 2)

    def test_save_dashboard_overwrites_on_same_id(self):
        d = Dashboard(id="d1", name="Original")
        self.repo.save_dashboard(d)
        d_updated = Dashboard(id="d1", name="Updated")
        self.repo.save_dashboard(d_updated)
        retrieved = self.repo.get_dashboard("d1")
        self.assertEqual(retrieved.name, "Updated")
        self.assertEqual(len(self.repo.list_dashboards()), 1)

    # -- widget operations ---------------------------------------------------

    def test_save_and_get_widget(self):
        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        self.repo.save_widget(w)
        retrieved = self.repo.get_widget("w1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "CPU")

    def test_get_widget_returns_none_for_unknown_id(self):
        result = self.repo.get_widget("unknown")
        self.assertIsNone(result)

    def test_save_widget_overwrites_on_same_id(self):
        w = Widget(id="w1", dashboard_id="d1", name="CPU", metric_name="cpu")
        self.repo.save_widget(w)
        mv = MetricValue(value=50.0, recorded_at="2026-03-29T07:00:00Z")
        w.values.append(mv)
        self.repo.save_widget(w)
        retrieved = self.repo.get_widget("w1")
        self.assertEqual(len(retrieved.values), 1)

    def test_repo_is_instance_of_interface(self):
        self.assertIsInstance(self.repo, IDashboardRepo)


if __name__ == "__main__":
    unittest.main()
