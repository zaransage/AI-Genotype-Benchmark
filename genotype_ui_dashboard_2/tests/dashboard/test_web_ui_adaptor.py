"""
Tests for domain/dashboard/core/adaptors — Web UI inbound adaptor and new REST
detail endpoints (GET /dashboards/{id}, GET /widgets/{id}).

Uses FastAPI TestClient; the app is wired with an InMemoryDashboardRepo so
these tests require no file system I/O (AI_CONTRACT.md §1).
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


from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.dashboard.core.adaptors.rest_routes import build_router
from domain.dashboard.core.adaptors.web_ui_routes import build_web_ui_router
from domain.dashboard.core.ports.in_memory_dashboard_repo import InMemoryDashboardRepo


def make_app() -> FastAPI:
    repo = InMemoryDashboardRepo()
    app  = FastAPI()
    app.include_router(build_router(repo=repo))
    app.include_router(build_web_ui_router())
    return app


# ---------------------------------------------------------------------------
# Web UI HTML routes
# ---------------------------------------------------------------------------

class TestWebUIDashboardListPage(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(make_app())

    def test_get_ui_returns_200(self):
        resp = self.client.get("/ui/")
        self.assertEqual(resp.status_code, 200)

    def test_get_ui_content_type_is_html(self):
        resp = self.client.get("/ui/")
        self.assertIn("text/html", resp.headers["content-type"])

    def test_list_page_contains_dashboards_heading(self):
        resp = self.client.get("/ui/")
        self.assertIn("Dashboards", resp.text)

    def test_list_page_contains_api_fetch_call(self):
        resp = self.client.get("/ui/")
        self.assertIn("/dashboards", resp.text)

    def test_list_page_contains_create_form(self):
        resp = self.client.get("/ui/")
        self.assertIn("<form", resp.text)


class TestWebUIDashboardDetailPage(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(make_app())

    def test_get_ui_dashboard_returns_200(self):
        resp = self.client.get("/ui/dashboards/some-id")
        self.assertEqual(resp.status_code, 200)

    def test_detail_page_content_type_is_html(self):
        resp = self.client.get("/ui/dashboards/some-id")
        self.assertIn("text/html", resp.headers["content-type"])

    def test_detail_page_contains_back_link(self):
        resp = self.client.get("/ui/dashboards/some-id")
        self.assertIn("/ui/", resp.text)

    def test_detail_page_contains_add_widget_form(self):
        resp = self.client.get("/ui/dashboards/some-id")
        self.assertIn("Add Widget", resp.text)

    def test_detail_page_fetches_dashboard_api(self):
        resp = self.client.get("/ui/dashboards/some-id")
        self.assertIn("/dashboards/", resp.text)


# ---------------------------------------------------------------------------
# GET /dashboards/{dashboard_id} — new REST endpoint
# ---------------------------------------------------------------------------

class TestGetDashboardRoute(unittest.TestCase):
    def setUp(self):
        self.app    = make_app()
        self.client = TestClient(self.app)
        raw  = load_raw("create_dashboard.0.0.1.json")
        resp = self.client.post("/dashboards", json=raw)
        self.dashboard_id   = resp.json()["id"]
        self.dashboard_name = resp.json()["name"]

    def test_fixture_raw_has_name(self):
        raw = load_raw("create_dashboard.0.0.1.json")
        self.assertIn("name", raw)

    def test_fixture_expected_has_required_fields(self):
        exp = load_expected("dashboard.0.0.1.json")
        for key in ("id", "name", "widget_ids"):
            self.assertIn(key, exp)

    def test_get_dashboard_returns_200(self):
        resp = self.client.get(f"/dashboards/{self.dashboard_id}")
        self.assertEqual(resp.status_code, 200)

    def test_get_dashboard_returns_correct_name(self):
        resp = self.client.get(f"/dashboards/{self.dashboard_id}")
        self.assertEqual(resp.json()["name"], self.dashboard_name)

    def test_get_dashboard_returns_id_and_widget_ids(self):
        resp = self.client.get(f"/dashboards/{self.dashboard_id}")
        body = resp.json()
        self.assertIn("id", body)
        self.assertIn("widget_ids", body)

    def test_get_dashboard_unknown_id_returns_404(self):
        resp = self.client.get("/dashboards/nonexistent-id")
        self.assertEqual(resp.status_code, 404)

    def test_get_dashboard_widget_ids_updated_after_add(self):
        raw_w = load_raw("add_widget.0.0.1.json")
        self.client.post(f"/dashboards/{self.dashboard_id}/widgets", json=raw_w)
        resp = self.client.get(f"/dashboards/{self.dashboard_id}")
        self.assertEqual(len(resp.json()["widget_ids"]), 1)


# ---------------------------------------------------------------------------
# GET /widgets/{widget_id} — new REST endpoint
# ---------------------------------------------------------------------------

class TestGetWidgetRoute(unittest.TestCase):
    def setUp(self):
        self.app    = make_app()
        self.client = TestClient(self.app)
        raw_d = load_raw("create_dashboard.0.0.1.json")
        d_id  = self.client.post("/dashboards", json=raw_d).json()["id"]
        raw_w = load_raw("add_widget.0.0.1.json")
        w_body = self.client.post(f"/dashboards/{d_id}/widgets", json=raw_w).json()
        self.widget_id   = w_body["id"]
        self.widget_name = w_body["name"]

    def test_fixture_raw_add_widget_has_required_fields(self):
        raw = load_raw("add_widget.0.0.1.json")
        self.assertIn("name", raw)
        self.assertIn("metric_name", raw)

    def test_fixture_expected_widget_shape(self):
        exp = load_expected("widget.0.0.1.json")
        for key in ("id", "dashboard_id", "name", "metric_name", "values"):
            self.assertIn(key, exp)

    def test_get_widget_returns_200(self):
        resp = self.client.get(f"/widgets/{self.widget_id}")
        self.assertEqual(resp.status_code, 200)

    def test_get_widget_returns_name_and_metric_name(self):
        resp = self.client.get(f"/widgets/{self.widget_id}")
        body = resp.json()
        self.assertIn("name", body)
        self.assertIn("metric_name", body)
        self.assertEqual(body["name"], self.widget_name)

    def test_get_widget_returns_values_list(self):
        resp = self.client.get(f"/widgets/{self.widget_id}")
        self.assertIsInstance(resp.json()["values"], list)

    def test_get_widget_values_embedded_after_post(self):
        raw_m = load_raw("post_metric.0.0.1.json")
        self.client.post(f"/widgets/{self.widget_id}/values", json=raw_m)
        resp = self.client.get(f"/widgets/{self.widget_id}")
        values = resp.json()["values"]
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0]["value"], raw_m["value"])

    def test_get_widget_unknown_id_returns_404(self):
        resp = self.client.get("/widgets/nonexistent")
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
