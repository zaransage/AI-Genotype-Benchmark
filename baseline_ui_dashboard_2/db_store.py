"""SQLite-backed store that mirrors the InMemoryStore interface.

Data is persisted to a SQLite file (default: dashboard.db).  An in-memory
mirror (self._dashboards / self._widgets) is kept for fast synchronous reads,
which also preserves compatibility with the existing test fixture that resets
the store by calling  _store._dashboards.clear()  and  _store._widgets.clear().

On startup the store loads all rows from SQLite into the in-memory dicts so
that data survives server restarts.
"""

import json
import sqlite3
from datetime import datetime

from models import Dashboard, MetricPoint, Widget

DEFAULT_DB_PATH = "dashboard.db"


class SQLiteStore:
    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._dashboards: dict[str, Dashboard] = {}
        self._widgets: dict[str, Widget] = {}
        self._init_db()
        self._load_from_db()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dashboards (
                    id          TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    description TEXT,
                    created_at  TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS widgets (
                    id               TEXT PRIMARY KEY,
                    dashboard_id     TEXT NOT NULL,
                    name             TEXT NOT NULL,
                    unit             TEXT,
                    created_at       TEXT NOT NULL,
                    latest_value     REAL,
                    latest_timestamp TEXT,
                    history          TEXT NOT NULL DEFAULT '[]'
                )
                """
            )
            conn.commit()

    def _load_from_db(self) -> None:
        with self._connect() as conn:
            for row in conn.execute("SELECT * FROM dashboards"):
                d = Dashboard(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                self._dashboards[d.id] = d

            for row in conn.execute("SELECT * FROM widgets"):
                history: list[MetricPoint] = []
                for mp in json.loads(row["history"]):
                    history.append(
                        MetricPoint(
                            value=mp["value"],
                            timestamp=datetime.fromisoformat(mp["timestamp"]),
                            labels=mp.get("labels"),
                        )
                    )
                w = Widget(
                    id=row["id"],
                    dashboard_id=row["dashboard_id"],
                    name=row["name"],
                    unit=row["unit"],
                    created_at=datetime.fromisoformat(row["created_at"]),
                    latest_value=row["latest_value"],
                    latest_timestamp=(
                        datetime.fromisoformat(row["latest_timestamp"])
                        if row["latest_timestamp"]
                        else None
                    ),
                    history=history,
                )
                self._widgets[w.id] = w

    @staticmethod
    def _history_to_json(history: list[MetricPoint]) -> str:
        return json.dumps(
            [
                {
                    "value": mp.value,
                    "timestamp": mp.timestamp.isoformat(),
                    "labels": mp.labels,
                }
                for mp in history
            ]
        )

    # ------------------------------------------------------------------
    # Dashboards
    # ------------------------------------------------------------------

    def create_dashboard(self, dashboard: Dashboard) -> Dashboard:
        self._dashboards[dashboard.id] = dashboard
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO dashboards (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                (
                    dashboard.id,
                    dashboard.name,
                    dashboard.description,
                    dashboard.created_at.isoformat(),
                ),
            )
            conn.commit()
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        return self._dashboards.get(dashboard_id)

    def list_dashboards(self) -> list[Dashboard]:
        return list(self._dashboards.values())

    # ------------------------------------------------------------------
    # Widgets
    # ------------------------------------------------------------------

    def create_widget(self, widget: Widget) -> Widget:
        self._widgets[widget.id] = widget
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO widgets
                    (id, dashboard_id, name, unit, created_at,
                     latest_value, latest_timestamp, history)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    widget.id,
                    widget.dashboard_id,
                    widget.name,
                    widget.unit,
                    widget.created_at.isoformat(),
                    widget.latest_value,
                    widget.latest_timestamp.isoformat()
                    if widget.latest_timestamp
                    else None,
                    self._history_to_json(widget.history),
                ),
            )
            conn.commit()
        return widget

    def get_widget(self, widget_id: str) -> Widget | None:
        return self._widgets.get(widget_id)

    def list_widgets(self, dashboard_id: str) -> list[Widget]:
        return [w for w in self._widgets.values() if w.dashboard_id == dashboard_id]

    def update_widget(self, widget: Widget) -> Widget:
        self._widgets[widget.id] = widget
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE widgets
                SET latest_value=?, latest_timestamp=?, history=?
                WHERE id=?
                """,
                (
                    widget.latest_value,
                    widget.latest_timestamp.isoformat()
                    if widget.latest_timestamp
                    else None,
                    self._history_to_json(widget.history),
                    widget.id,
                ),
            )
            conn.commit()
        return widget
