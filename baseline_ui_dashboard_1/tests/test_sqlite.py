"""Tests for the SQLiteStore persistence layer."""
import os
import sys
import uuid
from datetime import datetime, timezone

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import SQLiteStore
from models import Dashboard, MetricValue, Widget


def _now() -> datetime:
    return datetime.now(timezone.utc)


@pytest.fixture
def db(tmp_path):
    """Fresh SQLiteStore backed by a temp file for each test."""
    return SQLiteStore(db_path=str(tmp_path / "test.db"))


def _make_dashboard(name="Test", description=None) -> Dashboard:
    return Dashboard(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        widgets=[],
        created_at=_now(),
    )


def _make_widget(name="CPU", unit="%") -> Widget:
    return Widget(
        id=str(uuid.uuid4()),
        name=name,
        unit=unit,
        metrics=[],
        created_at=_now(),
    )


def _make_metric(value=42.0) -> MetricValue:
    return MetricValue(id=str(uuid.uuid4()), value=value, timestamp=_now())


# ── add_dashboard / get_dashboard ──────────────────────────────────────────────

class TestAddAndGetDashboard:
    def test_roundtrip(self, db):
        d = _make_dashboard("Board A", "desc")
        db.add_dashboard(d)
        fetched = db.get_dashboard(d.id)
        assert fetched is not None
        assert fetched.id == d.id
        assert fetched.name == "Board A"
        assert fetched.description == "desc"

    def test_missing_returns_none(self, db):
        assert db.get_dashboard("nonexistent") is None

    def test_empty_widgets_list(self, db):
        d = _make_dashboard()
        db.add_dashboard(d)
        assert db.get_dashboard(d.id).widgets == []

    def test_timestamps_preserved(self, db):
        d = _make_dashboard()
        db.add_dashboard(d)
        fetched = db.get_dashboard(d.id)
        assert fetched.created_at.isoformat() == d.created_at.isoformat()


# ── list_dashboards ────────────────────────────────────────────────────────────

class TestListDashboards:
    def test_empty_initially(self, db):
        assert db.list_dashboards() == []

    def test_returns_all_dashboards(self, db):
        db.add_dashboard(_make_dashboard("A"))
        db.add_dashboard(_make_dashboard("B"))
        names = {d.name for d in db.list_dashboards()}
        assert names == {"A", "B"}

    def test_count(self, db):
        for i in range(4):
            db.add_dashboard(_make_dashboard(f"D{i}"))
        assert len(db.list_dashboards()) == 4


# ── save_dashboard (widget + metric persistence) ───────────────────────────────

class TestSaveDashboard:
    def test_widget_persisted(self, db):
        d = _make_dashboard()
        db.add_dashboard(d)
        w = _make_widget("Memory", "MB")
        d.widgets.append(w)
        db.save_dashboard(d)

        fetched = db.get_dashboard(d.id)
        assert len(fetched.widgets) == 1
        assert fetched.widgets[0].id == w.id
        assert fetched.widgets[0].name == "Memory"
        assert fetched.widgets[0].unit == "MB"

    def test_metric_persisted(self, db):
        d = _make_dashboard()
        db.add_dashboard(d)
        w = _make_widget()
        m = _make_metric(99.5)
        w.metrics.append(m)
        d.widgets.append(w)
        db.save_dashboard(d)

        fetched = db.get_dashboard(d.id)
        assert len(fetched.widgets[0].metrics) == 1
        assert fetched.widgets[0].metrics[0].value == 99.5

    def test_multiple_metrics_order(self, db):
        d = _make_dashboard()
        db.add_dashboard(d)
        w = _make_widget()
        for v in [1.0, 2.0, 3.0]:
            w.metrics.append(_make_metric(v))
        d.widgets.append(w)
        db.save_dashboard(d)

        fetched = db.get_dashboard(d.id)
        values = [m.value for m in fetched.widgets[0].metrics]
        assert set(values) == {1.0, 2.0, 3.0}

    def test_upsert_idempotent(self, db):
        d = _make_dashboard()
        db.add_dashboard(d)
        db.save_dashboard(d)  # second save should not duplicate
        assert len(db.list_dashboards()) == 1

    def test_widget_without_unit(self, db):
        d = _make_dashboard()
        db.add_dashboard(d)
        w = Widget(
            id=str(uuid.uuid4()), name="NoUnit", unit=None, metrics=[], created_at=_now()
        )
        d.widgets.append(w)
        db.save_dashboard(d)

        fetched = db.get_dashboard(d.id)
        assert fetched.widgets[0].unit is None

    def test_dashboard_description_none(self, db):
        d = _make_dashboard(description=None)
        db.add_dashboard(d)
        fetched = db.get_dashboard(d.id)
        assert fetched.description is None


# ── isolation between separate store instances ─────────────────────────────────

class TestStoreIsolation:
    def test_two_stores_same_file(self, tmp_path):
        path = str(tmp_path / "shared.db")
        s1 = SQLiteStore(db_path=path)
        s2 = SQLiteStore(db_path=path)

        d = _make_dashboard("Shared")
        s1.add_dashboard(d)
        fetched = s2.get_dashboard(d.id)
        assert fetched is not None
        assert fetched.name == "Shared"

    def test_different_files_isolated(self, tmp_path):
        s1 = SQLiteStore(db_path=str(tmp_path / "a.db"))
        s2 = SQLiteStore(db_path=str(tmp_path / "b.db"))

        d = _make_dashboard("Only in A")
        s1.add_dashboard(d)
        assert s2.get_dashboard(d.id) is None
