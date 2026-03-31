"""
SqliteDashboardRepository — SQLite-backed implementation of IDashboardRepository.

Creates the schema on first connect. db_path is injected at construction time;
the composition root (main.py) passes the concrete path.
Aligned column formatting is intentional; excluded from auto-formatters via pyproject.toml.
"""
from __future__ import annotations

import sqlite3

from domain.dashboard.core.models                        import Dashboard, MetricValue, Widget
from domain.dashboard.core.ports.i_dashboard_repository import IDashboardRepository


class SqliteDashboardRepository(IDashboardRepository):

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        # In-memory databases do not persist across connect() calls; cache the
        # connection so that schema and data survive the object's lifetime.
        self._cached_conn: sqlite3.Connection | None = (
            self._open_connection() if db_path == ":memory:" else None
        )
        self._ensure_schema()

    # ------------------------------------------------------------------
    # IDashboardRepository implementation
    # ------------------------------------------------------------------

    def save(self, dashboard: Dashboard) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO dashboards (id, name, created_at) VALUES (?, ?, ?)",
                (dashboard.id, dashboard.name, dashboard.created_at),
            )
            # Remove widgets that are no longer part of this dashboard.
            existing_ids = {
                row[0]
                for row in conn.execute(
                    "SELECT id FROM widgets WHERE dashboard_id = ?", (dashboard.id,)
                )
            }
            current_ids = {w.id for w in dashboard.widgets}
            for stale_id in existing_ids - current_ids:
                conn.execute("DELETE FROM metric_values WHERE widget_id = ?", (stale_id,))
                conn.execute("DELETE FROM widgets WHERE id = ?",              (stale_id,))

            for widget in dashboard.widgets:
                conn.execute(
                    "INSERT OR REPLACE INTO widgets (id, name, unit, dashboard_id)"
                    " VALUES (?, ?, ?, ?)",
                    (widget.id, widget.name, widget.unit, dashboard.id),
                )
                # Replace metric values wholesale — delete then re-insert preserves order.
                conn.execute("DELETE FROM metric_values WHERE widget_id = ?", (widget.id,))
                for mv in widget.values:
                    conn.execute(
                        "INSERT INTO metric_values (widget_id, timestamp, value)"
                        " VALUES (?, ?, ?)",
                        (widget.id, mv.timestamp, mv.value),
                    )

    def get(self, dashboard_id: str) -> Dashboard | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, created_at FROM dashboards WHERE id = ?",
                (dashboard_id,),
            ).fetchone()
            if row is None:
                return None
            return self._build_dashboard(conn, row)

    def list_all(self) -> list[Dashboard]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, created_at FROM dashboards"
            ).fetchall()
            return [self._build_dashboard(conn, row) for row in rows]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _open_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _connect(self) -> sqlite3.Connection:
        if self._cached_conn is not None:
            return self._cached_conn
        return self._open_connection()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS dashboards (
                    id         TEXT PRIMARY KEY,
                    name       TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS widgets (
                    id           TEXT PRIMARY KEY,
                    name         TEXT NOT NULL,
                    unit         TEXT NOT NULL,
                    dashboard_id TEXT NOT NULL REFERENCES dashboards(id)
                );
                CREATE TABLE IF NOT EXISTS metric_values (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    widget_id TEXT    NOT NULL REFERENCES widgets(id),
                    timestamp TEXT    NOT NULL,
                    value     REAL    NOT NULL
                );
            """)

    def _build_dashboard(self, conn: sqlite3.Connection, row: sqlite3.Row) -> Dashboard:
        widget_rows = conn.execute(
            "SELECT id, name, unit, dashboard_id FROM widgets WHERE dashboard_id = ?",
            (row["id"],),
        ).fetchall()
        widgets: list[Widget] = []
        for wr in widget_rows:
            mv_rows = conn.execute(
                "SELECT timestamp, value FROM metric_values"
                " WHERE widget_id = ? ORDER BY id",
                (wr["id"],),
            ).fetchall()
            values = [
                MetricValue(timestamp=r["timestamp"], value=r["value"])
                for r in mv_rows
            ]
            widgets.append(Widget(
                id           = wr["id"],
                name         = wr["name"],
                unit         = wr["unit"],
                dashboard_id = wr["dashboard_id"],
                values       = values,
            ))
        return Dashboard(
            id         = row["id"],
            name       = row["name"],
            created_at = row["created_at"],
            widgets    = widgets,
        )
