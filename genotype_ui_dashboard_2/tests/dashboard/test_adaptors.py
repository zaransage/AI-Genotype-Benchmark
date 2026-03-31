"""
Tests for domain/dashboard/core/adaptors — inbound REST routes.

Uses FastAPI TestClient to drive the HTTP boundary.
Verifies:
  1. raw fixture fields map to the correct HTTP request bodies
  2. response shape matches the expected canonical output fixtures
"""

import json
import unittest
from pathlib import Path

FIXTURES_RAW = Path(__file__).parents[2] / "fixtures" / "raw" / "dashboard" / "v1"
FIXTURES_EXP = Path(__file__).parents[2] / "fixtures" / "expected" / "dashboard" / "v1"


def load_raw(filename: str) -> dict:
    with open(FIXTURES_RAW / filename) as fh:
        return json.load(fh)


def load_expected(filename: str) -> dict:
    with open(FIXTURES_EXP / filename) as fh:
        return json.load(fh)


from fastapi.testclient import TestClient

from domain.dashboard.core.ports.in_memory_dashboard_repo import InMemoryDashboardRepo
from domain.dashboard.core.adaptors.rest_routes import build_router
from fastapi import FastAPI


def make_app() -> FastAPI:
    repo = InMemoryDashboardRepo()
    app = FastAPI()
    app.include_router(build_router(repo=repo))
    return app


class TestCreateDashboardRoute(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(make_app())

    def test_fixture_raw_has_name_field(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        self.assertIn("name", raw)

    def test_fixture_expected_has_id_name_widget_ids(self):
        exp = load_expected("dashboard.0.0.1.json")
        for key in ("id", "name", "widget_ids"):
            self.assertIn(key, exp)

    def test_post_dashboards_returns_201(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        resp = self.client.post("/dashboards", json=raw)
        self.assertEqual(resp.status_code, 201)

    def test_response_contains_id_name_widget_ids(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        resp = self.client.post("/dashboards", json=raw)
        body = resp.json()
        for key in ("id", "name", "widget_ids"):
            self.assertIn(key, body)

    def test_response_name_matches_request(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        resp = self.client.post("/dashboards", json=raw)
        self.assertEqual(resp.json()["name"], raw["name"])

    def test_post_dashboards_empty_name_returns_422(self):
        resp = self.client.post("/dashboards", json={"name": ""})
        self.assertEqual(resp.status_code, 422)


class TestListDashboardsRoute(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.client = TestClient(self.app)

    def test_get_dashboards_empty_returns_200(self):
        resp = self.client.get("/dashboards")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_get_dashboards_returns_created_dashboards(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        self.client.post("/dashboards", json=raw)
        resp = self.client.get("/dashboards")
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["name"], raw["name"])


class TestAddWidgetRoute(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.client = TestClient(self.app)
        raw_dash = load_raw("create_dashboard.0.0.1.json")
        resp = self.client.post("/dashboards", json=raw_dash)
        self.dashboard_id = resp.json()["id"]

    def test_fixture_raw_add_widget_has_name_metric_name(self):
        raw = load_raw("add_widget.0.0.1.json")
        self.assertIn("name", raw)
        self.assertIn("metric_name", raw)

    def test_fixture_expected_widget_shape(self):
        exp = load_expected("widget.0.0.1.json")
        for key in ("id", "dashboard_id", "name", "metric_name", "values"):
            self.assertIn(key, exp)

    def test_post_widget_returns_201(self):
        raw = load_raw("add_widget.0.0.1.json")
        resp = self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets", json=raw
        )
        self.assertEqual(resp.status_code, 201)

    def test_response_contains_required_fields(self):
        raw = load_raw("add_widget.0.0.1.json")
        resp = self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets", json=raw
        )
        body = resp.json()
        for key in ("id", "dashboard_id", "name", "metric_name", "values"):
            self.assertIn(key, body)

    def test_widget_dashboard_id_matches(self):
        raw = load_raw("add_widget.0.0.1.json")
        resp = self.client.post(
            f"/dashboards/{self.dashboard_id}/widgets", json=raw
        )
        self.assertEqual(resp.json()["dashboard_id"], self.dashboard_id)

    def test_add_widget_to_unknown_dashboard_returns_404(self):
        raw = load_raw("add_widget.0.0.1.json")
        resp = self.client.post("/dashboards/nonexistent/widgets", json=raw)
        self.assertEqual(resp.status_code, 404)


class TestPostMetricRoute(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.client = TestClient(self.app)
        raw_dash = load_raw("create_dashboard.0.0.1.json")
        dash_resp = self.client.post("/dashboards", json=raw_dash)
        dashboard_id = dash_resp.json()["id"]
        raw_widget = load_raw("add_widget.0.0.1.json")
        widget_resp = self.client.post(
            f"/dashboards/{dashboard_id}/widgets", json=raw_widget
        )
        self.widget_id = widget_resp.json()["id"]

    def test_fixture_raw_post_metric_has_value(self):
        raw = load_raw("post_metric.0.0.1.json")
        self.assertIn("value", raw)

    def test_fixture_expected_metric_value_has_value_recorded_at(self):
        exp = load_expected("metric_value.0.0.1.json")
        self.assertIn("value", exp)
        self.assertIn("recorded_at", exp)

    def test_post_metric_returns_201(self):
        raw = load_raw("post_metric.0.0.1.json")
        resp = self.client.post(f"/widgets/{self.widget_id}/values", json=raw)
        self.assertEqual(resp.status_code, 201)

    def test_response_value_matches_fixture(self):
        raw = load_raw("post_metric.0.0.1.json")
        resp = self.client.post(f"/widgets/{self.widget_id}/values", json=raw)
        self.assertEqual(resp.json()["value"], raw["value"])

    def test_response_has_recorded_at(self):
        raw = load_raw("post_metric.0.0.1.json")
        resp = self.client.post(f"/widgets/{self.widget_id}/values", json=raw)
        self.assertIn("recorded_at", resp.json())

    def test_post_metric_to_unknown_widget_returns_404(self):
        raw = load_raw("post_metric.0.0.1.json")
        resp = self.client.post("/widgets/nonexistent/values", json=raw)
        self.assertEqual(resp.status_code, 404)


class TestReadWidgetValuesRoute(unittest.TestCase):
    def setUp(self):
        self.app = make_app()
        self.client = TestClient(self.app)
        raw_dash = load_raw("create_dashboard.0.0.1.json")
        dash_resp = self.client.post("/dashboards", json=raw_dash)
        dashboard_id = dash_resp.json()["id"]
        raw_widget = load_raw("add_widget.0.0.1.json")
        widget_resp = self.client.post(
            f"/dashboards/{dashboard_id}/widgets", json=raw_widget
        )
        self.widget_id = widget_resp.json()["id"]

    def test_get_values_empty_on_new_widget(self):
        resp = self.client.get(f"/widgets/{self.widget_id}/values")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), [])

    def test_get_values_returns_posted_metrics(self):
        raw = load_raw("post_metric.0.0.1.json")
        self.client.post(f"/widgets/{self.widget_id}/values", json=raw)
        resp = self.client.get(f"/widgets/{self.widget_id}/values")
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["value"], raw["value"])

    def test_get_values_accumulates_multiple_posts(self):
        raw = load_raw("post_metric.0.0.1.json")
        self.client.post(f"/widgets/{self.widget_id}/values", json=raw)
        self.client.post(f"/widgets/{self.widget_id}/values", json={"value": 10.0})
        resp = self.client.get(f"/widgets/{self.widget_id}/values")
        self.assertEqual(len(resp.json()), 2)

    def test_get_values_unknown_widget_returns_404(self):
        resp = self.client.get("/widgets/nonexistent/values")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
