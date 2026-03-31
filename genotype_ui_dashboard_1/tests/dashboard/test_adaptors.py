"""
Tests for domain/core/adaptors/fastapi_router.py — HTTP adaptor translation layer.

One test file per layer (adaptors) within the dashboard use case.

Per AI_CONTRACT.md §6, each translation test asserts TWO things:
  1. The raw fixture contains the expected source fields.
  2. The canonical dataclass instance has the correct field values after
     adaptor conversion (verified via the HTTP response body).
"""
import json
import pathlib
import unittest

from fastapi.testclient import TestClient

RAW_DIR = pathlib.Path(__file__).parents[2] / "fixtures" / "raw" / "dashboard" / "v1"
EXP_DIR = pathlib.Path(__file__).parents[2] / "fixtures" / "expected" / "dashboard" / "v1"


def _load_raw(filename: str) -> dict:
    with open(RAW_DIR / filename) as fh:
        return json.load(fh)


def _load_expected(filename: str) -> dict:
    with open(EXP_DIR / filename) as fh:
        return json.load(fh)


def _build_client() -> TestClient:
    """Compose the FastAPI app with in-memory implementations for testing."""
    from domain.core.commands import (
        CreateDashboardCommand,
        ListDashboardsCommand,
        AddWidgetCommand,
        PostMetricValueCommand,
        ReadWidgetValuesCommand,
    )
    from domain.core.ports.in_memory_dashboard_repository import InMemoryDashboardRepository
    from domain.core.ports.in_memory_widget_repository import InMemoryWidgetRepository
    from domain.core.ports.in_memory_metric_value_repository import InMemoryMetricValueRepository
    from domain.core.adaptors.fastapi_router import MetricsDashboardAdaptor, create_router
    from fastapi import FastAPI

    dash_repo   = InMemoryDashboardRepository()
    widget_repo = InMemoryWidgetRepository()
    value_repo  = InMemoryMetricValueRepository()

    adaptor = MetricsDashboardAdaptor(
        create_cmd=CreateDashboardCommand(dashboards=dash_repo),
        list_cmd=ListDashboardsCommand(dashboards=dash_repo),
        add_widget_cmd=AddWidgetCommand(dashboards=dash_repo, widgets=widget_repo),
        post_value_cmd=PostMetricValueCommand(widgets=widget_repo, metric_values=value_repo),
        read_values_cmd=ReadWidgetValuesCommand(widgets=widget_repo, metric_values=value_repo),
    )

    app = FastAPI()
    app.include_router(create_router(adaptor))
    return TestClient(app)


class TestCreateDashboardAdaptor(unittest.TestCase):

    def setUp(self):
        self.client = _build_client()

    def test_raw_fixture_has_name_field(self):
        raw = _load_raw("create_dashboard.0.0.1.json")
        self.assertIn("name", raw)

    def test_post_creates_dashboard_and_response_matches_canonical_model(self):
        raw      = _load_raw("create_dashboard.0.0.1.json")
        expected = _load_expected("dashboard.0.0.1.json")

        resp = self.client.post("/dashboards", json=raw)
        self.assertEqual(resp.status_code, 201)

        body = resp.json()
        # Response shape carries all canonical Dashboard fields
        self.assertIn("id", body)
        self.assertIn("name", body)
        self.assertIn("created_at", body)
        # Stable field from canonical model matches expected fixture
        self.assertEqual(body["name"], expected["name"])


class TestListDashboardsAdaptor(unittest.TestCase):

    def setUp(self):
        self.client = _build_client()

    def test_get_returns_empty_list_initially(self):
        resp = self.client.get("/dashboards")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_get_returns_created_dashboards(self):
        raw = _load_raw("create_dashboard.0.0.1.json")
        self.client.post("/dashboards", json=raw)

        resp = self.client.get("/dashboards")
        self.assertEqual(resp.status_code, 200)
        dashboards = resp.json()
        self.assertEqual(len(dashboards), 1)
        self.assertEqual(dashboards[0]["name"], raw["name"])


class TestAddWidgetAdaptor(unittest.TestCase):

    def setUp(self):
        self.client = _build_client()
        raw = _load_raw("create_dashboard.0.0.1.json")
        resp = self.client.post("/dashboards", json=raw)
        self.dashboard_id = resp.json()["id"]

    def test_raw_widget_fixture_has_name_and_unit_fields(self):
        raw = _load_raw("add_widget.0.0.1.json")
        self.assertIn("name", raw)
        self.assertIn("unit", raw)

    def test_post_adds_widget_and_response_matches_canonical_model(self):
        raw      = _load_raw("add_widget.0.0.1.json")
        expected = _load_expected("widget.0.0.1.json")

        resp = self.client.post(f"/dashboards/{self.dashboard_id}/widgets", json=raw)
        self.assertEqual(resp.status_code, 201)

        body = resp.json()
        self.assertIn("id", body)
        self.assertIn("dashboard_id", body)
        self.assertIn("name", body)
        self.assertIn("unit", body)
        # Stable canonical fields match expected fixture
        self.assertEqual(body["name"], expected["name"])
        self.assertEqual(body["unit"], expected["unit"])
        self.assertEqual(body["dashboard_id"], self.dashboard_id)

    def test_post_to_missing_dashboard_returns_404(self):
        raw  = _load_raw("add_widget.0.0.1.json")
        resp = self.client.post("/dashboards/nonexistent/widgets", json=raw)
        self.assertEqual(resp.status_code, 404)


class TestPostMetricValueAdaptor(unittest.TestCase):

    def setUp(self):
        self.client = _build_client()
        d_resp = self.client.post("/dashboards", json=_load_raw("create_dashboard.0.0.1.json"))
        self.dashboard_id = d_resp.json()["id"]
        w_resp = self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets",
            json=_load_raw("add_widget.0.0.1.json"),
        )
        self.widget_id = w_resp.json()["id"]

    def test_raw_metric_value_fixture_has_value_field(self):
        raw = _load_raw("post_metric_value.0.0.1.json")
        self.assertIn("value", raw)

    def test_post_metric_value_response_matches_canonical_model(self):
        raw      = _load_raw("post_metric_value.0.0.1.json")
        expected = _load_expected("metric_value.0.0.1.json")

        resp = self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets/{self.widget_id}/values",
            json=raw,
        )
        self.assertEqual(resp.status_code, 201)

        body = resp.json()
        self.assertIn("id", body)
        self.assertIn("widget_id", body)
        self.assertIn("value", body)
        self.assertIn("recorded_at", body)
        # Stable canonical field matches expected fixture
        self.assertAlmostEqual(body["value"], expected["value"])
        self.assertEqual(body["widget_id"], self.widget_id)

    def test_post_metric_value_to_missing_widget_returns_404(self):
        raw  = _load_raw("post_metric_value.0.0.1.json")
        resp = self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets/nonexistent/values",
            json=raw,
        )
        self.assertEqual(resp.status_code, 404)


class TestReadWidgetValuesAdaptor(unittest.TestCase):

    def setUp(self):
        self.client = _build_client()
        d_resp = self.client.post("/dashboards", json=_load_raw("create_dashboard.0.0.1.json"))
        self.dashboard_id = d_resp.json()["id"]
        w_resp = self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets",
            json=_load_raw("add_widget.0.0.1.json"),
        )
        self.widget_id = w_resp.json()["id"]

    def test_read_returns_empty_list_initially(self):
        resp = self.client.get(
            f"/dashboards/{self.dashboard_id}/widgets/{self.widget_id}/values"
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_read_returns_posted_values(self):
        raw = _load_raw("post_metric_value.0.0.1.json")
        self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets/{self.widget_id}/values",
            json=raw,
        )
        resp = self.client.get(
            f"/dashboards/{self.dashboard_id}/widgets/{self.widget_id}/values"
        )
        self.assertEqual(resp.status_code, 200)
        values = resp.json()
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0]["value"], raw["value"])

    def test_read_missing_widget_returns_404(self):
        resp = self.client.get(
            f"/dashboards/{self.dashboard_id}/widgets/nonexistent/values"
        )
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
