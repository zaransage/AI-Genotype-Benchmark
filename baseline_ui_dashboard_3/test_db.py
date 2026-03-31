from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from db import SQLiteStore
from main import app, get_store
from models import Dashboard, MetricValue, Widget


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def store():
    """In-memory SQLite store, isolated per test."""
    return SQLiteStore(":memory:")


@pytest.fixture()
def client(store):
    """TestClient using an isolated SQLite store."""
    app.dependency_overrides[get_store] = lambda: store
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _make_dashboard(store: SQLiteStore, name: str = "Dash") -> Dashboard:
    d = Dashboard(
        id=str(uuid.uuid4()),
        name=name,
        description="desc",
        created_at=datetime.now(timezone.utc),
    )
    store.save_dashboard(d)
    return d


def _make_widget(store: SQLiteStore, dashboard: Dashboard, name: str = "W") -> Widget:
    w = Widget(id=str(uuid.uuid4()), dashboard_id=dashboard.id, name=name, unit="u")
    dashboard.widgets[w.id] = w
    store.save_dashboard(dashboard)
    return w


# ---------------------------------------------------------------------------
# SQLiteStore unit tests
# ---------------------------------------------------------------------------


def test_sqlite_save_and_get_dashboard(store):
    d = _make_dashboard(store, "MyDash")
    result = store.get_dashboard(d.id)
    assert result is not None
    assert result.id == d.id
    assert result.name == "MyDash"
    assert result.description == "desc"


def test_sqlite_get_all_dashboards(store):
    _make_dashboard(store, "A")
    _make_dashboard(store, "B")
    dashboards = store.get_all_dashboards()
    assert len(dashboards) == 2
    names = {d.name for d in dashboards}
    assert names == {"A", "B"}


def test_sqlite_get_dashboard_not_found(store):
    assert store.get_dashboard("nonexistent") is None


def test_sqlite_delete_dashboard(store):
    d = _make_dashboard(store)
    assert store.delete_dashboard(d.id) is True
    assert store.get_dashboard(d.id) is None


def test_sqlite_delete_nonexistent_returns_false(store):
    assert store.delete_dashboard("ghost") is False


def test_sqlite_update_dashboard(store):
    d = _make_dashboard(store, "Original")
    d.name = "Updated"
    store.save_dashboard(d)
    result = store.get_dashboard(d.id)
    assert result.name == "Updated"


def test_sqlite_widgets_persisted(store):
    d = _make_dashboard(store)
    _make_widget(store, d, "CPU")
    _make_widget(store, d, "RAM")
    result = store.get_dashboard(d.id)
    assert len(result.widgets) == 2
    widget_names = {w.name for w in result.widgets.values()}
    assert widget_names == {"CPU", "RAM"}


def test_sqlite_metric_values_persisted(store):
    d = _make_dashboard(store)
    w = _make_widget(store, d)
    ts = datetime.now(timezone.utc)
    w.values.append(MetricValue(value=10.5, timestamp=ts))
    w.values.append(MetricValue(value=20.0, timestamp=ts))
    store.save_dashboard(d)

    result = store.get_dashboard(d.id)
    widget = result.widgets[w.id]
    assert len(widget.values) == 2
    assert widget.values[0].value == 10.5
    assert widget.values[1].value == 20.0


def test_sqlite_metric_value_order_preserved(store):
    d = _make_dashboard(store)
    w = _make_widget(store, d)
    ts = datetime.now(timezone.utc)
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        w.values.append(MetricValue(value=v, timestamp=ts))
    store.save_dashboard(d)

    result = store.get_dashboard(d.id)
    values = [mv.value for mv in result.widgets[w.id].values]
    assert values == [1.0, 2.0, 3.0, 4.0, 5.0]


def test_sqlite_current_value_is_last(store):
    d = _make_dashboard(store)
    w = _make_widget(store, d)
    ts = datetime.now(timezone.utc)
    w.values.append(MetricValue(value=1.0, timestamp=ts))
    w.values.append(MetricValue(value=99.9, timestamp=ts))
    store.save_dashboard(d)

    result = store.get_dashboard(d.id)
    assert result.widgets[w.id].current_value.value == 99.9


def test_sqlite_delete_cascades_widgets_and_values(store):
    d = _make_dashboard(store)
    w = _make_widget(store, d)
    ts = datetime.now(timezone.utc)
    w.values.append(MetricValue(value=7.0, timestamp=ts))
    store.save_dashboard(d)

    store.delete_dashboard(d.id)
    assert store.get_dashboard(d.id) is None
    # Verify no orphan data (indirectly: re-saving with same ID works)
    d2 = Dashboard(
        id=d.id, name="Reborn", description="", created_at=datetime.now(timezone.utc)
    )
    store.save_dashboard(d2)
    assert store.get_dashboard(d.id).name == "Reborn"


# ---------------------------------------------------------------------------
# Web UI endpoint tests (via TestClient)
# ---------------------------------------------------------------------------


def test_ui_returns_200(client):
    resp = client.get("/ui")
    assert resp.status_code == 200


def test_ui_returns_html(client):
    resp = client.get("/ui")
    assert "text/html" in resp.headers["content-type"]


def test_ui_contains_dashboard_title(client):
    resp = client.get("/ui")
    assert "Metrics Dashboard" in resp.text


def test_ui_not_in_openapi_schema(client):
    schema = client.get("/openapi.json").json()
    assert "/ui" not in schema["paths"]


# ---------------------------------------------------------------------------
# API + SQLite integration (via TestClient with SQLite store override)
# ---------------------------------------------------------------------------


def test_api_create_and_list_via_sqlite(client):
    r = client.post("/dashboards", json={"name": "SQLite Dash", "description": "test"})
    assert r.status_code == 201
    dashboards = client.get("/dashboards").json()
    assert any(d["name"] == "SQLite Dash" for d in dashboards)


def test_api_widget_and_value_via_sqlite(client):
    d = client.post("/dashboards", json={"name": "D"}).json()
    w = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "Temp", "unit": "C"}).json()
    r = client.post(
        f"/dashboards/{d['id']}/widgets/{w['id']}/values",
        json={"value": 36.6},
    )
    assert r.status_code == 201
    assert r.json()["current_value"]["value"] == 36.6


def test_api_values_history_via_sqlite(client):
    d = client.post("/dashboards", json={"name": "D"}).json()
    w = client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W"}).json()
    for v in [1.1, 2.2, 3.3]:
        client.post(f"/dashboards/{d['id']}/widgets/{w['id']}/values", json={"value": v})
    values = client.get(f"/dashboards/{d['id']}/widgets/{w['id']}/values").json()
    assert [entry["value"] for entry in values] == [1.1, 2.2, 3.3]


def test_api_widget_count_via_sqlite(client):
    d = client.post("/dashboards", json={"name": "D"}).json()
    client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W1"})
    client.post(f"/dashboards/{d['id']}/widgets", json={"name": "W2"})
    dashboards = client.get("/dashboards").json()
    match = next(x for x in dashboards if x["id"] == d["id"])
    assert match["widget_count"] == 2
