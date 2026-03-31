from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Generator

from models import Dashboard, MetricValue, Widget

_SCHEMA = """
CREATE TABLE IF NOT EXISTS dashboards (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS widgets (
    id           TEXT PRIMARY KEY,
    dashboard_id TEXT NOT NULL REFERENCES dashboards(id),
    name         TEXT NOT NULL,
    unit         TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS metric_values (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    widget_id TEXT NOT NULL REFERENCES widgets(id),
    value     REAL NOT NULL,
    timestamp TEXT NOT NULL
);
"""


class SQLiteStore:
    """Persistent store backed by a SQLite database."""

    def __init__(self, db_path: str = "dashboards.db") -> None:
        self._lock = threading.Lock()
        self._db = sqlite3.connect(db_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA foreign_keys = ON")
        self._init_db()

    def _init_db(self) -> None:
        with self._tx() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _tx(self) -> Generator[sqlite3.Connection, None, None]:
        with self._lock:
            try:
                yield self._db
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    # ------------------------------------------------------------------
    # Public interface (mirrors InMemoryStore)
    # ------------------------------------------------------------------

    def get_all_dashboards(self) -> list[Dashboard]:
        with self._tx() as conn:
            rows = conn.execute("SELECT * FROM dashboards").fetchall()
            return [self._load_dashboard(conn, row) for row in rows]

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        with self._tx() as conn:
            row = conn.execute(
                "SELECT * FROM dashboards WHERE id = ?", (dashboard_id,)
            ).fetchone()
            if row is None:
                return None
            return self._load_dashboard(conn, row)

    def save_dashboard(self, dashboard: Dashboard) -> Dashboard:
        with self._tx() as conn:
            conn.execute(
                """
                INSERT INTO dashboards (id, name, description, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name        = excluded.name,
                    description = excluded.description,
                    created_at  = excluded.created_at
                """,
                (
                    dashboard.id,
                    dashboard.name,
                    dashboard.description,
                    dashboard.created_at.isoformat(),
                ),
            )
            for widget in dashboard.widgets.values():
                conn.execute(
                    """
                    INSERT INTO widgets (id, dashboard_id, name, unit)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name,
                        unit = excluded.unit
                    """,
                    (widget.id, widget.dashboard_id, widget.name, widget.unit),
                )
                # Re-sync metric values by replacing them entirely
                conn.execute(
                    "DELETE FROM metric_values WHERE widget_id = ?", (widget.id,)
                )
                conn.executemany(
                    "INSERT INTO metric_values (widget_id, value, timestamp) VALUES (?, ?, ?)",
                    [
                        (widget.id, mv.value, mv.timestamp.isoformat())
                        for mv in widget.values
                    ],
                )
        return dashboard

    def delete_dashboard(self, dashboard_id: str) -> bool:
        with self._tx() as conn:
            conn.execute(
                """
                DELETE FROM metric_values WHERE widget_id IN (
                    SELECT id FROM widgets WHERE dashboard_id = ?
                )
                """,
                (dashboard_id,),
            )
            conn.execute("DELETE FROM widgets WHERE dashboard_id = ?", (dashboard_id,))
            result = conn.execute(
                "DELETE FROM dashboards WHERE id = ?", (dashboard_id,)
            )
            return result.rowcount > 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_dashboard(self, conn: sqlite3.Connection, row: sqlite3.Row) -> Dashboard:
        widget_rows = conn.execute(
            "SELECT * FROM widgets WHERE dashboard_id = ?", (row["id"],)
        ).fetchall()
        widgets: dict[str, Widget] = {}
        for w_row in widget_rows:
            mv_rows = conn.execute(
                "SELECT value, timestamp FROM metric_values WHERE widget_id = ? ORDER BY id",
                (w_row["id"],),
            ).fetchall()
            values = [
                MetricValue(
                    value=mv["value"],
                    timestamp=datetime.fromisoformat(mv["timestamp"]),
                )
                for mv in mv_rows
            ]
            widget = Widget(
                id=w_row["id"],
                dashboard_id=w_row["dashboard_id"],
                name=w_row["name"],
                unit=w_row["unit"],
                values=values,
            )
            widgets[widget.id] = widget
        return Dashboard(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=datetime.fromisoformat(row["created_at"]),
            widgets=widgets,
        )


sqlite_store = SQLiteStore()
