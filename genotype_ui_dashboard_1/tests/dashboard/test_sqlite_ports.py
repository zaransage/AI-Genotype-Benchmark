"""
Tests for the SQLite outbound-port implementations.

One test class per repository, using an in-memory SQLite connection so tests
are fast, isolated, and leave no files on disk.

Layer: ports
"""
from __future__ import annotations

import sqlite3
import unittest
from datetime import datetime, timezone

from domain.core.models import Dashboard, MetricValue, MetricWidget
from domain.core.ports.sqlite_dashboard_repository import SqliteDashboardRepository
from domain.core.ports.sqlite_metric_value_repository import SqliteMetricValueRepository
from domain.core.ports.sqlite_widget_repository import SqliteWidgetRepository

_TS = datetime(2024, 6, 1, 9, 0, 0, tzinfo=timezone.utc)
_TS2 = datetime(2024, 6, 2, 9, 0, 0, tzinfo=timezone.utc)


class TestSqliteDashboardRepository(unittest.TestCase):

    def setUp(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        self._repo = SqliteDashboardRepository(self._conn)

    def tearDown(self) -> None:
        self._conn.close()

    def test_save_and_get_round_trips_dashboard(self) -> None:
        dash = Dashboard(id="d1", name="Prod", created_at=_TS)
        self._repo.save(dash)
        result = self._repo.get("d1")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "d1")
        self.assertEqual(result.name, "Prod")
        self.assertEqual(result.created_at, _TS)

    def test_get_missing_returns_none(self) -> None:
        self.assertIsNone(self._repo.get("no-such-id"))

    def test_list_all_empty_returns_empty_list(self) -> None:
        self.assertEqual(self._repo.list_all(), [])

    def test_list_all_returns_all_saved_dashboards(self) -> None:
        self._repo.save(Dashboard(id="d1", name="First",  created_at=_TS))
        self._repo.save(Dashboard(id="d2", name="Second", created_at=_TS2))
        results = self._repo.list_all()
        self.assertEqual(len(results), 2)
        ids = {d.id for d in results}
        self.assertIn("d1", ids)
        self.assertIn("d2", ids)

    def test_save_overwrites_existing_row(self) -> None:
        self._repo.save(Dashboard(id="d1", name="Original", created_at=_TS))
        self._repo.save(Dashboard(id="d1", name="Updated",  created_at=_TS))
        self.assertEqual(self._repo.get("d1").name, "Updated")

    def test_table_created_once_no_error_on_second_init(self) -> None:
        # A second repo pointing at the same connection must not blow up.
        second = SqliteDashboardRepository(self._conn)
        self.assertIsNotNone(second)


class TestSqliteWidgetRepository(unittest.TestCase):

    def setUp(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        self._repo = SqliteWidgetRepository(self._conn)

    def tearDown(self) -> None:
        self._conn.close()

    def test_save_and_get_round_trips_widget(self) -> None:
        w = MetricWidget(id="w1", dashboard_id="d1", name="CPU", unit="percent")
        self._repo.save(w)
        result = self._repo.get("w1")
        self.assertIsNotNone(result)
        self.assertEqual(result.id, "w1")
        self.assertEqual(result.dashboard_id, "d1")
        self.assertEqual(result.name, "CPU")
        self.assertEqual(result.unit, "percent")

    def test_get_missing_returns_none(self) -> None:
        self.assertIsNone(self._repo.get("no-such-id"))

    def test_list_by_dashboard_returns_only_matching_widgets(self) -> None:
        self._repo.save(MetricWidget(id="w1", dashboard_id="d1", name="CPU",  unit="percent"))
        self._repo.save(MetricWidget(id="w2", dashboard_id="d1", name="RAM",  unit="MB"))
        self._repo.save(MetricWidget(id="w3", dashboard_id="d2", name="Disk", unit="GB"))
        results = self._repo.list_by_dashboard("d1")
        self.assertEqual(len(results), 2)
        self.assertEqual({w.id for w in results}, {"w1", "w2"})

    def test_list_by_dashboard_empty_returns_empty_list(self) -> None:
        self.assertEqual(self._repo.list_by_dashboard("d_none"), [])

    def test_save_overwrites_existing_row(self) -> None:
        self._repo.save(MetricWidget(id="w1", dashboard_id="d1", name="CPU",  unit="percent"))
        self._repo.save(MetricWidget(id="w1", dashboard_id="d1", name="CPU2", unit="cores"))
        result = self._repo.get("w1")
        self.assertEqual(result.name, "CPU2")
        self.assertEqual(result.unit, "cores")


class TestSqliteMetricValueRepository(unittest.TestCase):

    def setUp(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        self._repo = SqliteMetricValueRepository(self._conn)

    def tearDown(self) -> None:
        self._conn.close()

    def test_append_and_list_round_trips_value(self) -> None:
        mv = MetricValue(id="v1", widget_id="w1", value=42.5, recorded_at=_TS)
        self._repo.append(mv)
        results = self._repo.list_by_widget("w1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].id, "v1")
        self.assertAlmostEqual(results[0].value, 42.5)
        self.assertEqual(results[0].recorded_at, _TS)

    def test_list_by_widget_returns_only_matching_values(self) -> None:
        self._repo.append(MetricValue(id="v1", widget_id="w1", value=1.0, recorded_at=_TS))
        self._repo.append(MetricValue(id="v2", widget_id="w2", value=2.0, recorded_at=_TS))
        self._repo.append(MetricValue(id="v3", widget_id="w1", value=3.0, recorded_at=_TS2))
        results = self._repo.list_by_widget("w1")
        self.assertEqual(len(results), 2)
        self.assertEqual({v.id for v in results}, {"v1", "v3"})

    def test_list_by_widget_empty_returns_empty_list(self) -> None:
        self.assertEqual(self._repo.list_by_widget("w_none"), [])

    def test_values_ordered_by_recorded_at(self) -> None:
        self._repo.append(MetricValue(id="v2", widget_id="w1", value=2.0, recorded_at=_TS2))
        self._repo.append(MetricValue(id="v1", widget_id="w1", value=1.0, recorded_at=_TS))
        results = self._repo.list_by_widget("w1")
        self.assertEqual(results[0].id, "v1")
        self.assertEqual(results[1].id, "v2")

    def test_multiple_appends_preserved(self) -> None:
        for i in range(5):
            self._repo.append(
                MetricValue(
                    id=f"v{i}",
                    widget_id="w1",
                    value=float(i),
                    recorded_at=_TS,
                )
            )
        self.assertEqual(len(self._repo.list_by_widget("w1")), 5)


if __name__ == "__main__":
    unittest.main()
