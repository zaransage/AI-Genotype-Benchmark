"""
tests/scheduler/test_ui_adaptors.py

Tests for the Web UI inbound adaptor (ui_routes).
Verifies that GET /ui returns a well-formed HTML page containing the expected
structural elements. The page logic is client-side; only the HTTP boundary is
tested here.
"""

import unittest
from unittest.mock import MagicMock


def _build_ui_test_app():
    """Build a minimal FastAPI app wired with a mock SchedulerService."""
    from fastapi import FastAPI
    from domain.scheduler.core.scheduler_service import SchedulerService
    from domain.scheduler.core.adaptors.ui_routes import build_ui_router

    mock_service = MagicMock(spec=SchedulerService)
    app = FastAPI()
    app.include_router(build_ui_router(service=mock_service))
    return app, mock_service


class TestUiDashboardRoute(unittest.TestCase):

    def setUp(self):
        from fastapi.testclient import TestClient
        self.app, self.mock_service = _build_ui_test_app()
        self.client = TestClient(self.app)

    def test_get_ui_returns_200(self):
        response = self.client.get("/ui")
        self.assertEqual(response.status_code, 200)

    def test_get_ui_content_type_is_html(self):
        response = self.client.get("/ui")
        self.assertIn("text/html", response.headers["content-type"])

    def test_get_ui_contains_jobs_table(self):
        response = self.client.get("/ui")
        self.assertIn("jobs-body", response.text)

    def test_get_ui_contains_runs_section(self):
        response = self.client.get("/ui")
        self.assertIn("runs-section", response.text)

    def test_get_ui_contains_refresh_button(self):
        response = self.client.get("/ui")
        self.assertIn("Refresh", response.text)

    def test_get_ui_fetches_jobs_endpoint_via_script(self):
        """The page script must reference the /jobs REST endpoint."""
        response = self.client.get("/ui")
        self.assertIn("/jobs", response.text)

    def test_get_ui_fetches_runs_endpoint_via_script(self):
        """The page script must reference the /jobs/{id}/runs REST endpoint."""
        response = self.client.get("/ui")
        self.assertIn("/runs", response.text)

    def test_get_ui_does_not_call_scheduler_service(self):
        """The route serves static HTML; it must not invoke the service directly."""
        self.client.get("/ui")
        self.mock_service.list_jobs.assert_not_called()
        self.mock_service.get_run_history.assert_not_called()

    def test_get_ui_contains_valid_html_doctype(self):
        response = self.client.get("/ui")
        self.assertTrue(response.text.strip().startswith("<!DOCTYPE html>"))

    def test_get_ui_has_page_title(self):
        response = self.client.get("/ui")
        self.assertIn("<title>", response.text)
        self.assertIn("Job Scheduler", response.text)


if __name__ == "__main__":
    unittest.main()
