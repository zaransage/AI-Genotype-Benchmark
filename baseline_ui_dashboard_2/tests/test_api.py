import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

# Import app fresh for each test module run; isolate store via fixture.
import main as app_module
from main import app, store as _store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset in-memory store before every test."""
    _store._dashboards.clear()
    _store._widgets.clear()
    yield
    _store._dashboards.clear()
    _store._widgets.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_dashboard(client, name="Test", description=None):
    payload = {"name": name}
    if description:
        payload["description"] = description
    return client.post("/dashboards", json=payload)


def _create_widget(client, dashboard_id, name="CPU", unit="%"):
    return client.post(
        f"/dashboards/{dashboard_id}/widgets",
        json={"name": name, "unit": unit},
    )


def _post_metric(client, dashboard_id, widget_id, value, labels=None):
    payload = {"value": value}
    if labels:
        payload["labels"] = labels
    return client.post(
        f"/dashboards/{dashboard_id}/widgets/{widget_id}/metrics",
        json=payload,
    )


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------


class TestCreateDashboard:
    def test_creates_dashboard_returns_201(self, client):
        r = _create_dashboard(client, "Prod")
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Prod"
        assert "id" in body
        assert "created_at" in body

    def test_description_is_optional(self, client):
        r = _create_dashboard(client)
        assert r.status_code == 201
        assert r.json()["description"] is None

    def test_description_stored(self, client):
        r = _create_dashboard(client, description="My dashboard")
        assert r.json()["description"] == "My dashboard"

    def test_missing_name_returns_422(self, client):
        r = client.post("/dashboards", json={})
        assert r.status_code == 422


class TestListDashboards:
    def test_empty_list(self, client):
        r = client.get("/dashboards")
        assert r.status_code == 200
        assert r.json() == []

    def test_returns_created_dashboards(self, client):
        _create_dashboard(client, "A")
        _create_dashboard(client, "B")
        r = client.get("/dashboards")
        assert r.status_code == 200
        names = {d["name"] for d in r.json()}
        assert names == {"A", "B"}


class TestGetDashboard:
    def test_get_existing(self, client):
        created = _create_dashboard(client, "X").json()
        r = client.get(f"/dashboards/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_nonexistent_returns_404(self, client):
        r = client.get("/dashboards/does-not-exist")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Widget tests
# ---------------------------------------------------------------------------


class TestCreateWidget:
    def test_creates_widget(self, client):
        dash = _create_dashboard(client).json()
        r = _create_widget(client, dash["id"], "Memory", "MB")
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "Memory"
        assert body["unit"] == "MB"
        assert body["dashboard_id"] == dash["id"]

    def test_unknown_dashboard_returns_404(self, client):
        r = _create_widget(client, "bad-id")
        assert r.status_code == 404

    def test_initial_latest_value_is_null(self, client):
        dash = _create_dashboard(client).json()
        w = _create_widget(client, dash["id"]).json()
        assert w["latest_value"] is None
        assert w["latest_timestamp"] is None
        assert w["history"] == []


class TestListWidgets:
    def test_lists_widgets_for_dashboard(self, client):
        dash = _create_dashboard(client).json()
        _create_widget(client, dash["id"], "CPU")
        _create_widget(client, dash["id"], "RAM")
        r = client.get(f"/dashboards/{dash['id']}/widgets")
        assert r.status_code == 200
        assert len(r.json()) == 2

    def test_widgets_isolated_between_dashboards(self, client):
        d1 = _create_dashboard(client, "D1").json()
        d2 = _create_dashboard(client, "D2").json()
        _create_widget(client, d1["id"], "W1")
        r = client.get(f"/dashboards/{d2['id']}/widgets")
        assert r.json() == []

    def test_unknown_dashboard_returns_404(self, client):
        r = client.get("/dashboards/nope/widgets")
        assert r.status_code == 404


class TestGetWidget:
    def test_get_widget(self, client):
        dash = _create_dashboard(client).json()
        w = _create_widget(client, dash["id"]).json()
        r = client.get(f"/dashboards/{dash['id']}/widgets/{w['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == w["id"]

    def test_wrong_dashboard_returns_404(self, client):
        d1 = _create_dashboard(client, "D1").json()
        d2 = _create_dashboard(client, "D2").json()
        w = _create_widget(client, d1["id"]).json()
        r = client.get(f"/dashboards/{d2['id']}/widgets/{w['id']}")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Metric tests
# ---------------------------------------------------------------------------


class TestPostMetric:
    def test_post_metric_returns_201(self, client):
        dash = _create_dashboard(client).json()
        w = _create_widget(client, dash["id"]).json()
        r = _post_metric(client, dash["id"], w["id"], 42.5)
        assert r.status_code == 201
        body = r.json()
        assert body["value"] == 42.5
        assert "timestamp" in body

    def test_latest_value_updated(self, client):
        dash = _create_dashboard(client).json()
        w = _create_widget(client, dash["id"]).json()
        _post_metric(client, dash["id"], w["id"], 10.0)
        _post_metric(client, dash["id"], w["id"], 99.9)
        w_updated = client.get(f"/dashboards/{dash['id']}/widgets/{w['id']}").json()
        assert w_updated["latest_value"] == 99.9

    def test_history_accumulates(self, client):
        dash = _create_dashboard(client).json()
        w = _create_widget(client, dash["id"]).json()
        for v in [1.0, 2.0, 3.0]:
            _post_metric(client, dash["id"], w["id"], v)
        w_data = client.get(f"/dashboards/{dash['id']}/widgets/{w['id']}").json()
        assert len(w_data["history"]) == 3
        assert [p["value"] for p in w_data["history"]] == [1.0, 2.0, 3.0]

    def test_labels_stored(self, client):
        dash = _create_dashboard(client).json()
        w = _create_widget(client, dash["id"]).json()
        r = _post_metric(client, dash["id"], w["id"], 5.0, labels={"host": "web-1"})
        assert r.json()["labels"] == {"host": "web-1"}

    def test_unknown_widget_returns_404(self, client):
        dash = _create_dashboard(client).json()
        r = _post_metric(client, dash["id"], "bad-widget-id", 1.0)
        assert r.status_code == 404

    def test_unknown_dashboard_returns_404(self, client):
        dash = _create_dashboard(client).json()
        w = _create_widget(client, dash["id"]).json()
        r = _post_metric(client, "bad-dash", w["id"], 1.0)
        assert r.status_code == 404
