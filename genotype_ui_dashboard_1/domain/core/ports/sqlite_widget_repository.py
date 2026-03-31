"""SQLite outbound-port implementation of IWidgetRepository.

Receives a sqlite3.Connection from the composition root (main.py).
Creates the metric_widgets table on first use.
"""
from __future__ import annotations

import sqlite3

from domain.core.models import MetricWidget
from domain.core.ports.i_widget_repository import IWidgetRepository


class SqliteWidgetRepository(IWidgetRepository):
    """Persists MetricWidget objects in a SQLite database table."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_widgets (
                id           TEXT PRIMARY KEY,
                dashboard_id TEXT NOT NULL,
                name         TEXT NOT NULL,
                unit         TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, widget: MetricWidget) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO metric_widgets (id, dashboard_id, name, unit) VALUES (?, ?, ?, ?)",
            (widget.id, widget.dashboard_id, widget.name, widget.unit),
        )
        self._conn.commit()

    def get(self, widget_id: str) -> MetricWidget | None:
        row = self._conn.execute(
            "SELECT id, dashboard_id, name, unit FROM metric_widgets WHERE id = ?",
            (widget_id,),
        ).fetchone()
        if row is None:
            return None
        return MetricWidget(id=row[0], dashboard_id=row[1], name=row[2], unit=row[3])

    def list_by_dashboard(self, dashboard_id: str) -> list[MetricWidget]:
        rows = self._conn.execute(
            "SELECT id, dashboard_id, name, unit FROM metric_widgets WHERE dashboard_id = ?",
            (dashboard_id,),
        ).fetchall()
        return [MetricWidget(id=r[0], dashboard_id=r[1], name=r[2], unit=r[3]) for r in rows]
