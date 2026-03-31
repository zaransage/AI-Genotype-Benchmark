"""
SQLite outbound port implementation: SqliteDashboardRepo.

Persists dashboards, widgets, and metric readings to a SQLite database.
Config (db_path) is co-located with the port; composition root passes the value in
(AI_CONTRACT.md §9).

Schema:
  dashboards           — one row per dashboard
  dashboard_widget_ids — ordered list of widget IDs per dashboard
  widgets              — one row per widget
  metric_values        — ordered metric readings per widget
"""

import sqlite3

from domain.dashboard.core.models import Dashboard, MetricValue, Widget
from domain.dashboard.core.ports.i_dashboard_repo import IDashboardRepo

# Default path used by the composition root.  Tests should pass ":memory:".
DEFAULT_DB_PATH: str = "./dashboard.db"


class SqliteDashboardRepo(IDashboardRepo):
    """SQLite-backed implementation of IDashboardRepo.

    A single persistent connection is held for the lifetime of the repo so
    that in-memory databases (db_path=":memory:") share state across all
    method calls.  check_same_thread=False is required when used under
    multi-threaded servers such as uvicorn.
    """

    def __init__(self, db_path: str = DEFAULT_DB_PATH) -> None:
        self._db_path = db_path
        self._conn    = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._init_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        return self._conn

    def _init_schema(self) -> None:
        with self._conn as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS dashboards (
                    id   TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS dashboard_widget_ids (
                    dashboard_id TEXT    NOT NULL,
                    widget_id    TEXT    NOT NULL,
                    position     INTEGER NOT NULL,
                    PRIMARY KEY (dashboard_id, widget_id)
                );

                CREATE TABLE IF NOT EXISTS widgets (
                    id           TEXT PRIMARY KEY,
                    dashboard_id TEXT NOT NULL,
                    name         TEXT NOT NULL,
                    metric_name  TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS metric_values (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    widget_id   TEXT    NOT NULL,
                    value       REAL    NOT NULL,
                    recorded_at TEXT    NOT NULL
                );
            """)

    # ------------------------------------------------------------------
    # IDashboardRepo implementation
    # ------------------------------------------------------------------

    def save_dashboard(self, dashboard: Dashboard) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO dashboards (id, name) VALUES (?, ?)",
                (dashboard.id, dashboard.name),
            )
            conn.execute(
                "DELETE FROM dashboard_widget_ids WHERE dashboard_id = ?",
                (dashboard.id,),
            )
            for pos, widget_id in enumerate(dashboard.widget_ids):
                conn.execute(
                    "INSERT INTO dashboard_widget_ids (dashboard_id, widget_id, position)"
                    " VALUES (?, ?, ?)",
                    (dashboard.id, widget_id, pos),
                )

    def get_dashboard(self, dashboard_id: str) -> Dashboard | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name FROM dashboards WHERE id = ?",
                (dashboard_id,),
            ).fetchone()
            if row is None:
                return None
            widget_ids = [
                r["widget_id"]
                for r in conn.execute(
                    "SELECT widget_id FROM dashboard_widget_ids"
                    " WHERE dashboard_id = ? ORDER BY position",
                    (dashboard_id,),
                ).fetchall()
            ]
        return Dashboard(id=row["id"], name=row["name"], widget_ids=widget_ids)

    def list_dashboards(self) -> list:
        with self._connect() as conn:
            rows = conn.execute("SELECT id FROM dashboards").fetchall()
        return [self.get_dashboard(row["id"]) for row in rows]

    def save_widget(self, widget: Widget) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO widgets (id, dashboard_id, name, metric_name)"
                " VALUES (?, ?, ?, ?)",
                (widget.id, widget.dashboard_id, widget.name, widget.metric_name),
            )
            conn.execute(
                "DELETE FROM metric_values WHERE widget_id = ?",
                (widget.id,),
            )
            for mv in widget.values:
                conn.execute(
                    "INSERT INTO metric_values (widget_id, value, recorded_at)"
                    " VALUES (?, ?, ?)",
                    (widget.id, mv.value, mv.recorded_at),
                )

    def get_widget(self, widget_id: str) -> Widget | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, dashboard_id, name, metric_name FROM widgets WHERE id = ?",
                (widget_id,),
            ).fetchone()
            if row is None:
                return None
            values = [
                MetricValue(value=r["value"], recorded_at=r["recorded_at"])
                for r in conn.execute(
                    "SELECT value, recorded_at FROM metric_values"
                    " WHERE widget_id = ? ORDER BY id",
                    (widget_id,),
                ).fetchall()
            ]
        return Widget(
            id           = row["id"],
            dashboard_id = row["dashboard_id"],
            name         = row["name"],
            metric_name  = row["metric_name"],
            values       = values,
        )
