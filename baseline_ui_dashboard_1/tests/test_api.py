import pytest
from fastapi.testclient import TestClient

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import storage as storage_module
from storage import InMemoryStore
from main import app


@pytest.fixture(autouse=True)
def reset_store(monkeypatch):
    """Replace the global store with a fresh instance for each test."""
    fresh = InMemoryStore()
    monkeypatch.setattr(storage_module, "store", fresh)
    import main as main_module
    monkeypatch.setattr(main_module, "store", fresh)
    yield


@pytest.fixture
def client():
    return TestClient(app)


# ── Dashboard endpoints ────────────────────────────────────────────────────────

class TestCreateDashboard:
    def test_returns_201(self, client):
        resp = client.post("/dashboards", json={"name": "My Board"})
        assert resp.status_code == 201

    def test_response_shape(self, client):
        resp = client.post("/dashboards", json={"name": "My Board", "description": "desc"})
        data = resp.json()
        assert data["name"] == "My Board"
        assert data["description"] == "desc"
        assert "id" in data
        assert "created_at" in data
        assert data["widgets"] == []

    def test_description_optional(self, client):
        resp = client.post("/dashboards", json={"name": "No Desc"})
        assert resp.status_code == 201
        assert resp.json()["description"] is None

    def test_name_required(self, client):
        resp = client.post("/dashboards", json={})
        assert resp.status_code == 422


class TestListDashboards:
    def test_empty_initially(self, client):
        resp = client.get("/dashboards")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_created_dashboards(self, client):
        client.post("/dashboards", json={"name": "A"})
        client.post("/dashboards", json={"name": "B"})
        resp = client.get("/dashboards")
        names = [d["name"] for d in resp.json()]
        assert "A" in names
        assert "B" in names

    def test_count(self, client):
        for i in range(3):
            client.post("/dashboards", json={"name": f"Board {i}"})
        assert len(client.get("/dashboards").json()) == 3


class TestGetDashboard:
    def test_returns_dashboard(self, client):
        created = client.post("/dashboards", json={"name": "X"}).json()
        resp = client.get(f"/dashboards/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]

    def test_404_for_missing(self, client):
        resp = client.get("/dashboards/nonexistent")
        assert resp.status_code == 404


# ── Widget endpoints ───────────────────────────────────────────────────────────

class TestAddWidget:
    def _make_dashboard(self, client):
        return client.post("/dashboards", json={"name": "D"}).json()

    def test_returns_201(self, client):
        d = self._make_dashboard(client)
        resp = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "CPU"})
        assert resp.status_code == 201

    def test_response_shape(self, client):
        d = self._make_dashboard(client)
        resp = client.post(
            f"/dashboards/{d['id']}/widgets", json={"name": "CPU", "unit": "%"}
        )
        data = resp.json()
        assert data["name"] == "CPU"
        assert data["unit"] == "%"
        assert data["metrics"] == []
        assert "id" in data

    def test_unit_optional(self, client):
        d = self._make_dashboard(client)
        resp = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W"})
        assert resp.status_code == 201
        assert resp.json()["unit"] is None

    def test_widget_appears_in_dashboard(self, client):
        d = self._make_dashboard(client)
        w = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "MEM"}).json()
        d_updated = client.get(f"/dashboards/{d['id']}").json()
        widget_ids = [ww["id"] for ww in d_updated["widgets"]]
        assert w["id"] in widget_ids

    def test_404_for_missing_dashboard(self, client):
        resp = client.post("/dashboards/bad/widgets", json={"name": "W"})
        assert resp.status_code == 404

    def test_name_required(self, client):
        d = self._make_dashboard(client)
        resp = client.post(f"/dashboards/{d['id']}/widgets", json={})
        assert resp.status_code == 422


# ── Metric endpoints ───────────────────────────────────────────────────────────

class TestPostMetric:
    def _setup(self, client):
        d = client.post("/dashboards", json={"name": "D"}).json()
        w = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W"}).json()
        return d["id"], w["id"]

    def test_returns_201(self, client):
        d_id, w_id = self._setup(client)
        resp = client.post(
            f"/dashboards/{d_id}/widgets/{w_id}/metrics", json={"value": 42.0}
        )
        assert resp.status_code == 201

    def test_response_shape(self, client):
        d_id, w_id = self._setup(client)
        resp = client.post(
            f"/dashboards/{d_id}/widgets/{w_id}/metrics", json={"value": 99.5}
        )
        data = resp.json()
        assert data["value"] == 99.5
        assert "id" in data
        assert "timestamp" in data

    def test_custom_timestamp(self, client):
        d_id, w_id = self._setup(client)
        ts = "2024-01-15T10:30:00Z"
        resp = client.post(
            f"/dashboards/{d_id}/widgets/{w_id}/metrics",
            json={"value": 1.0, "timestamp": ts},
        )
        assert "2024-01-15" in resp.json()["timestamp"]

    def test_404_missing_dashboard(self, client):
        resp = client.post("/dashboards/bad/widgets/bad/metrics", json={"value": 1})
        assert resp.status_code == 404

    def test_404_missing_widget(self, client):
        d = client.post("/dashboards", json={"name": "D"}).json()
        resp = client.post(
            f"/dashboards/{d['id']}/widgets/bad/metrics", json={"value": 1}
        )
        assert resp.status_code == 404

    def test_value_required(self, client):
        d_id, w_id = self._setup(client)
        resp = client.post(f"/dashboards/{d_id}/widgets/{w_id}/metrics", json={})
        assert resp.status_code == 422


class TestListMetrics:
    def _setup(self, client):
        d = client.post("/dashboards", json={"name": "D"}).json()
        w = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W"}).json()
        return d["id"], w["id"]

    def test_empty_initially(self, client):
        d_id, w_id = self._setup(client)
        resp = client.get(f"/dashboards/{d_id}/widgets/{w_id}/metrics")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_posted_metrics(self, client):
        d_id, w_id = self._setup(client)
        client.post(f"/dashboards/{d_id}/widgets/{w_id}/metrics", json={"value": 1.0})
        client.post(f"/dashboards/{d_id}/widgets/{w_id}/metrics", json={"value": 2.0})
        metrics = client.get(f"/dashboards/{d_id}/widgets/{w_id}/metrics").json()
        assert len(metrics) == 2
        values = {m["value"] for m in metrics}
        assert values == {1.0, 2.0}

    def test_404_missing_dashboard(self, client):
        resp = client.get("/dashboards/bad/widgets/bad/metrics")
        assert resp.status_code == 404

    def test_404_missing_widget(self, client):
        d = client.post("/dashboards", json={"name": "D"}).json()
        resp = client.get(f"/dashboards/{d['id']}/widgets/bad/metrics")
        assert resp.status_code == 404

    def test_get_widget_endpoint(self, client):
        d_id, w_id = self._setup(client)
        resp = client.get(f"/dashboards/{d_id}/widgets/{w_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == w_id
