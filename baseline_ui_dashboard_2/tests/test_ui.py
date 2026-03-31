import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from fastapi.testclient import TestClient

from main import app, store as _store


@pytest.fixture(autouse=True)
def reset_store():
    """Reset in-memory store before every test (mirrors test_api.py fixture)."""
    _store._dashboards.clear()
    _store._widgets.clear()
    yield
    _store._dashboards.clear()
    _store._widgets.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Web UI endpoint
# ---------------------------------------------------------------------------


class TestUIEndpoint:
    def test_index_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200

    def test_index_content_type_is_html(self, client):
        r = client.get("/")
        assert "text/html" in r.headers["content-type"]

    def test_index_contains_page_title(self, client):
        r = client.get("/")
        assert "Metrics Dashboard" in r.text

    def test_index_not_included_in_openapi_schema(self, client):
        schema = client.get("/openapi.json").json()
        assert "/" not in schema["paths"]

    def test_index_references_dashboards_api(self, client):
        # The HTML page should fetch /dashboards via JS
        r = client.get("/")
        assert "/dashboards" in r.text


# ---------------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------------


class TestSQLitePersistence:
    """Verify that data written through SQLiteStore survives a fresh store instance."""

    def _make_dashboard(self, name="Test"):
        from models import Dashboard
        return Dashboard(
            id=str(uuid.uuid4()),
            name=name,
            description="desc",
            created_at=datetime.now(timezone.utc),
        )

    def _make_widget(self, dashboard_id, name="CPU"):
        from models import Widget
        return Widget(
            id=str(uuid.uuid4()),
            dashboard_id=dashboard_id,
            name=name,
            unit="%",
            created_at=datetime.now(timezone.utc),
        )

    def _make_metric(self, value=42.0):
        from models import MetricPoint
        return MetricPoint(
            value=value,
            timestamp=datetime.now(timezone.utc),
            labels={"host": "srv-1"},
        )

    def test_dashboard_survives_store_reload(self):
        from db_store import SQLiteStore

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            s1 = SQLiteStore(db_path=db_path)
            d = self._make_dashboard("Persistent")
            s1.create_dashboard(d)

            s2 = SQLiteStore(db_path=db_path)
            result = s2.get_dashboard(d.id)
            assert result is not None
            assert result.name == "Persistent"
            assert result.description == "desc"
        finally:
            os.unlink(db_path)

    def test_widget_survives_store_reload(self):
        from db_store import SQLiteStore

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            s1 = SQLiteStore(db_path=db_path)
            d = self._make_dashboard()
            s1.create_dashboard(d)
            w = self._make_widget(d.id)
            s1.create_widget(w)

            s2 = SQLiteStore(db_path=db_path)
            result = s2.get_widget(w.id)
            assert result is not None
            assert result.name == "CPU"
            assert result.unit == "%"
            assert result.dashboard_id == d.id
        finally:
            os.unlink(db_path)

    def test_metric_history_survives_store_reload(self):
        from db_store import SQLiteStore

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            s1 = SQLiteStore(db_path=db_path)
            d = self._make_dashboard()
            s1.create_dashboard(d)
            w = self._make_widget(d.id)
            s1.create_widget(w)

            # Add two metric points
            for val in [10.0, 20.0]:
                pt = self._make_metric(val)
                w.history.append(pt)
                w.latest_value = pt.value
                w.latest_timestamp = pt.timestamp
            s1.update_widget(w)

            s2 = SQLiteStore(db_path=db_path)
            loaded = s2.get_widget(w.id)
            assert loaded is not None
            assert loaded.latest_value == 20.0
            assert len(loaded.history) == 2
            assert [p.value for p in loaded.history] == [10.0, 20.0]
        finally:
            os.unlink(db_path)

    def test_metric_labels_survive_reload(self):
        from db_store import SQLiteStore

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            s1 = SQLiteStore(db_path=db_path)
            d = self._make_dashboard()
            s1.create_dashboard(d)
            w = self._make_widget(d.id)
            s1.create_widget(w)

            pt = self._make_metric(5.0)
            w.history.append(pt)
            w.latest_value = pt.value
            w.latest_timestamp = pt.timestamp
            s1.update_widget(w)

            s2 = SQLiteStore(db_path=db_path)
            loaded = s2.get_widget(w.id)
            assert loaded.history[0].labels == {"host": "srv-1"}
        finally:
            os.unlink(db_path)

    def test_list_dashboards_after_reload(self):
        from db_store import SQLiteStore

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            s1 = SQLiteStore(db_path=db_path)
            s1.create_dashboard(self._make_dashboard("A"))
            s1.create_dashboard(self._make_dashboard("B"))

            s2 = SQLiteStore(db_path=db_path)
            names = {d.name for d in s2.list_dashboards()}
            assert names == {"A", "B"}
        finally:
            os.unlink(db_path)

    def test_list_widgets_after_reload(self):
        from db_store import SQLiteStore

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            s1 = SQLiteStore(db_path=db_path)
            d = self._make_dashboard()
            s1.create_dashboard(d)
            s1.create_widget(self._make_widget(d.id, "CPU"))
            s1.create_widget(self._make_widget(d.id, "RAM"))

            s2 = SQLiteStore(db_path=db_path)
            widgets = s2.list_widgets(d.id)
            assert len(widgets) == 2
            assert {w.name for w in widgets} == {"CPU", "RAM"}
        finally:
            os.unlink(db_path)
