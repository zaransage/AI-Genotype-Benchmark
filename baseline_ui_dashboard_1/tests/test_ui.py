"""Tests for the HTML web UI routes."""
import os
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage as storage_module
from storage import InMemoryStore
from main import app


@pytest.fixture(autouse=True)
def reset_store(monkeypatch):
    """Use a fresh in-memory store for each test (same as existing test_api.py)."""
    fresh = InMemoryStore()
    monkeypatch.setattr(storage_module, "store", fresh)
    import main as main_module
    monkeypatch.setattr(main_module, "store", fresh)
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ── GET / ──────────────────────────────────────────────────────────────────────

class TestIndexPage:
    def test_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_content_type_html(self, client):
        resp = client.get("/")
        assert "text/html" in resp.headers["content-type"]

    def test_contains_title(self, client):
        resp = client.get("/")
        assert "Dashboards" in resp.text

    def test_contains_api_fetch_script(self, client):
        resp = client.get("/")
        assert "/dashboards" in resp.text

    def test_contains_links_to_ui_dashboards(self, client):
        resp = client.get("/")
        assert "/ui/dashboards/" in resp.text


# ── GET /ui/dashboards/{id} ────────────────────────────────────────────────────

class TestDashboardPage:
    def _create_dashboard(self, client, name="Test", description="Desc"):
        return client.post("/dashboards", json={"name": name, "description": description}).json()

    def test_returns_200_for_existing(self, client):
        d = self._create_dashboard(client)
        resp = client.get(f"/ui/dashboards/{d['id']}")
        assert resp.status_code == 200

    def test_content_type_html(self, client):
        d = self._create_dashboard(client)
        resp = client.get(f"/ui/dashboards/{d['id']}")
        assert "text/html" in resp.headers["content-type"]

    def test_returns_404_for_missing(self, client):
        resp = client.get("/ui/dashboards/nonexistent-id")
        assert resp.status_code == 404

    def test_page_contains_back_link(self, client):
        d = self._create_dashboard(client)
        resp = client.get(f"/ui/dashboards/{d['id']}")
        assert "href=\"/\"" in resp.text or 'href=/' in resp.text

    def test_page_contains_api_fetch_script(self, client):
        d = self._create_dashboard(client)
        resp = client.get(f"/ui/dashboards/{d['id']}")
        assert "/dashboards/" in resp.text

    def test_different_dashboards_same_template(self, client):
        d1 = self._create_dashboard(client, "Board One")
        d2 = self._create_dashboard(client, "Board Two")
        r1 = client.get(f"/ui/dashboards/{d1['id']}")
        r2 = client.get(f"/ui/dashboards/{d2['id']}")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Both return the same HTML shell; JS fetches the actual data
        assert r1.text == r2.text
