"""SQLite-backed store with the same interface as InMemoryStore."""
import os
import sqlite3
from datetime import datetime
from typing import Optional

from models import Dashboard, MetricValue, Widget

DB_PATH = os.environ.get("DB_PATH", "dashboards.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dashboards (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT,
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS widgets (
    id           TEXT PRIMARY KEY,
    dashboard_id TEXT NOT NULL,
    name         TEXT NOT NULL,
    unit         TEXT,
    created_at   TEXT NOT NULL,
    FOREIGN KEY (dashboard_id) REFERENCES dashboards(id)
);
CREATE TABLE IF NOT EXISTS metrics (
    id        TEXT PRIMARY KEY,
    widget_id TEXT NOT NULL,
    value     REAL NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (widget_id) REFERENCES widgets(id)
);
"""


class SQLiteStore:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        conn = self._connect()
        conn.executescript(_SCHEMA)
        conn.commit()
        conn.close()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _build_dashboard(self, conn: sqlite3.Connection, row: sqlite3.Row) -> Dashboard:
        widget_rows = conn.execute(
            "SELECT * FROM widgets WHERE dashboard_id = ? ORDER BY created_at",
            (row["id"],),
        ).fetchall()
        widgets = []
        for w in widget_rows:
            metric_rows = conn.execute(
                "SELECT * FROM metrics WHERE widget_id = ? ORDER BY timestamp",
                (w["id"],),
            ).fetchall()
            metrics = [
                MetricValue(
                    id=m["id"],
                    value=m["value"],
                    timestamp=datetime.fromisoformat(m["timestamp"]),
                )
                for m in metric_rows
            ]
            widgets.append(
                Widget(
                    id=w["id"],
                    name=w["name"],
                    unit=w["unit"],
                    metrics=metrics,
                    created_at=datetime.fromisoformat(w["created_at"]),
                )
            )
        return Dashboard(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            widgets=widgets,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def add_dashboard(self, dashboard: Dashboard) -> Dashboard:
        conn = self._connect()
        try:
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
        finally:
            conn.close()
        return dashboard

    def get_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM dashboards WHERE id = ?", (dashboard_id,)
            ).fetchone()
            if row is None:
                return None
            return self._build_dashboard(conn, row)
        finally:
            conn.close()

    def list_dashboards(self) -> list[Dashboard]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM dashboards ORDER BY created_at"
            ).fetchall()
            return [self._build_dashboard(conn, row) for row in rows]
        finally:
            conn.close()

    def save_dashboard(self, dashboard: Dashboard) -> Dashboard:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO dashboards (id, name, description, created_at) VALUES (?, ?, ?, ?)",
                (
                    dashboard.id,
                    dashboard.name,
                    dashboard.description,
                    dashboard.created_at.isoformat(),
                ),
            )
            for widget in dashboard.widgets:
                conn.execute(
                    "INSERT OR REPLACE INTO widgets (id, dashboard_id, name, unit, created_at) VALUES (?, ?, ?, ?, ?)",
                    (
                        widget.id,
                        dashboard.id,
                        widget.name,
                        widget.unit,
                        widget.created_at.isoformat(),
                    ),
                )
                for metric in widget.metrics:
                    conn.execute(
                        "INSERT OR REPLACE INTO metrics (id, widget_id, value, timestamp) VALUES (?, ?, ?, ?)",
                        (
                            metric.id,
                            widget.id,
                            metric.value,
                            metric.timestamp.isoformat(),
                        ),
                    )
            conn.commit()
        finally:
            conn.close()
        return dashboard


store = SQLiteStore()
