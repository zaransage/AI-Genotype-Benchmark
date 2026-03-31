from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app, get_store
from storage import InMemoryStore


@pytest.fixture()
def client():
    test_store = InMemoryStore()
    app.dependency_overrides[get_store] = lambda: test_store
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------


def test_create_dashboard(client):
    resp = client.post("/dashboards", json={"name": "Prod", "description": "Production metrics"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Prod"
    assert data["description"] == "Production metrics"
    assert data["widget_count"] == 0
    assert "id" in data
    assert "created_at" in data


def test_create_dashboard_minimal(client):
    resp = client.post("/dashboards", json={"name": "Min"})
    assert resp.status_code == 201
    assert resp.json()["description"] == ""


def test_list_dashboards_empty(client):
    resp = client.get("/dashboards")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_dashboards(client):
    client.post("/dashboards", json={"name": "A"})
    client.post("/dashboards", json={"name": "B"})
    resp = client.get("/dashboards")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_dashboard(client):
    create_resp = client.post("/dashboards", json={"name": "X"})
    dashboard_id = create_resp.json()["id"]
    resp = client.get(f"/dashboards/{dashboard_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == dashboard_id
    assert resp.json()["widgets"] == []


def test_get_dashboard_not_found(client):
    resp = client.get("/dashboards/nonexistent")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------


def _make_dashboard(client, name="Dash"):
    return client.post("/dashboards", json={"name": name}).json()


def test_add_widget(client):
    d = _make_dashboard(client)
    resp = client.post(
        f"/dashboards/{d['id']}/widgets",
        json={"name": "CPU", "unit": "%"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "CPU"
    assert data["unit"] == "%"
    assert data["dashboard_id"] == d["id"]
    assert data["current_value"] is None


def test_add_widget_to_missing_dashboard(client):
    resp = client.post("/dashboards/missing/widgets", json={"name": "W"})
    assert resp.status_code == 404


def test_list_widgets(client):
    d = _make_dashboard(client)
    client.post(f"/dashboards/{d['id']}/widgets", json={"name": "A"})
    client.post(f"/dashboards/{d['id']}/widgets", json={"name": "B"})
    resp = client.get(f"/dashboards/{d['id']}/widgets")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_get_widget(client):
    d = _make_dashboard(client)
    w = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "RAM", "unit": "MB"}).json()
    resp = client.get(f"/dashboards/{d['id']}/widgets/{w['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == w["id"]


def test_get_widget_not_found(client):
    d = _make_dashboard(client)
    resp = client.get(f"/dashboards/{d['id']}/widgets/nope")
    assert resp.status_code == 404


def test_dashboard_detail_includes_widgets(client):
    d = _make_dashboard(client)
    client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W1"})
    resp = client.get(f"/dashboards/{d['id']}")
    assert len(resp.json()["widgets"]) == 1


# ---------------------------------------------------------------------------
# Metric values
# ---------------------------------------------------------------------------


def _setup(client):
    d = _make_dashboard(client)
    w = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "Temp", "unit": "C"}).json()
    return d["id"], w["id"]


def test_post_metric_value(client):
    did, wid = _setup(client)
    resp = client.post(
        f"/dashboards/{did}/widgets/{wid}/values",
        json={"value": 42.5},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["current_value"]["value"] == 42.5


def test_current_value_updates(client):
    did, wid = _setup(client)
    client.post(f"/dashboards/{did}/widgets/{wid}/values", json={"value": 10.0})
    resp = client.post(f"/dashboards/{did}/widgets/{wid}/values", json={"value": 99.9})
    assert resp.json()["current_value"]["value"] == 99.9


def test_get_metric_values(client):
    did, wid = _setup(client)
    for v in [1.0, 2.0, 3.0]:
        client.post(f"/dashboards/{did}/widgets/{wid}/values", json={"value": v})
    resp = client.get(f"/dashboards/{did}/widgets/{wid}/values")
    assert resp.status_code == 200
    values = [entry["value"] for entry in resp.json()]
    assert values == [1.0, 2.0, 3.0]


def test_post_value_with_explicit_timestamp(client):
    did, wid = _setup(client)
    ts = "2025-01-15T12:00:00Z"
    resp = client.post(
        f"/dashboards/{did}/widgets/{wid}/values",
        json={"value": 7.7, "timestamp": ts},
    )
    assert resp.status_code == 201
    assert resp.json()["current_value"]["timestamp"].startswith("2025-01-15")


def test_post_value_missing_widget(client):
    d = _make_dashboard(client)
    resp = client.post(f"/dashboards/{d['id']}/widgets/bad/values", json={"value": 1})
    assert resp.status_code == 404


def test_post_value_missing_dashboard(client):
    resp = client.post("/dashboards/bad/widgets/bad/values", json={"value": 1})
    assert resp.status_code == 404


def test_widget_count_in_list(client):
    d = _make_dashboard(client)
    client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W1"})
    client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W2"})
    dashboards = client.get("/dashboards").json()
    match = next(x for x in dashboards if x["id"] == d["id"])
    assert match["widget_count"] == 2
