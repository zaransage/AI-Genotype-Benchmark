"""
tests/scheduler/test_web_ui_adaptor.py

Unit tests for WebUiAdaptor (inbound web-UI adaptor).
Covers: route registration, HTTP response code, content-type, and
HTML structure (presence of expected landmarks).
"""
from __future__ import annotations

import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.scheduler.core.adaptors.web_ui_adaptor import WebUiAdaptor


def _make_app() -> tuple[FastAPI, TestClient]:
    app     = FastAPI()
    adaptor = WebUiAdaptor()
    adaptor.register_routes(app)
    return app, TestClient(app)


class TestWebUiAdaptorRouteRegistration(unittest.TestCase):
    """WebUiAdaptor.register_routes mounts /ui on the given app."""

    def setUp(self) -> None:
        self._app, self._client = _make_app()

    def test_get_ui_returns_200(self) -> None:
        resp = self._client.get("/ui")
        self.assertEqual(resp.status_code, 200)

    def test_get_ui_content_type_is_html(self) -> None:
        resp = self._client.get("/ui")
        self.assertIn("text/html", resp.headers["content-type"])

    def test_get_ui_excluded_from_openapi_schema(self) -> None:
        """The /ui route must not pollute the OpenAPI spec."""
        schema = self._app.openapi()
        paths  = schema.get("paths", {})
        self.assertNotIn("/ui", paths)

    def test_unregistered_route_returns_404(self) -> None:
        resp = self._client.get("/no-such-route")
        self.assertEqual(resp.status_code, 404)


class TestWebUiAdaptorHtmlContent(unittest.TestCase):
    """HTML body contains the structural landmarks required by the front-end."""

    def setUp(self) -> None:
        _, client = _make_app()
        self._html = client.get("/ui").text

    def test_html_contains_doctype(self) -> None:
        self.assertIn("<!DOCTYPE html>", self._html)

    def test_html_contains_jobs_panel(self) -> None:
        self.assertIn("jobs-panel", self._html)

    def test_html_contains_history_panel(self) -> None:
        self.assertIn("history-panel", self._html)

    def test_html_contains_page_title(self) -> None:
        self.assertIn("Crontab Clone", self._html)

    def test_html_contains_fetch_jobs_endpoint(self) -> None:
        """The page must call the /jobs REST endpoint."""
        self.assertIn('fetch("/jobs")', self._html)

    def test_html_contains_fetch_runs_endpoint(self) -> None:
        """The page must call the /jobs/{id}/runs REST endpoint."""
        self.assertIn("/jobs/", self._html)
        self.assertIn("/runs", self._html)

    def test_html_contains_auto_refresh_interval(self) -> None:
        self.assertIn("setInterval", self._html)

    def test_html_contains_xss_escape_function(self) -> None:
        """escHtml must be present to protect against XSS."""
        self.assertIn("escHtml", self._html)


class TestWebUiAdaptorMultipleRegistrations(unittest.TestCase):
    """register_routes can be called on different app instances independently."""

    def test_two_independent_apps_each_serve_ui(self) -> None:
        _, client_a = _make_app()
        _, client_b = _make_app()
        self.assertEqual(client_a.get("/ui").status_code, 200)
        self.assertEqual(client_b.get("/ui").status_code, 200)


if __name__ == "__main__":
    unittest.main()
