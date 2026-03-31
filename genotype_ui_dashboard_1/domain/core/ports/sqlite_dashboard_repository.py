"""SQLite outbound-port implementation of IDashboardRepository.

Receives a sqlite3.Connection from the composition root (main.py).
Creates the dashboards table on first use.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from domain.core.models import Dashboard
from domain.core.ports.i_dashboard_repository import IDashboardRepository


class SqliteDashboardRepository(IDashboardRepository):
    """Persists Dashboard objects in a SQLite database table."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS dashboards (
                id         TEXT PRIMARY KEY,
                name       TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def save(self, dashboard: Dashboard) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO dashboards (id, name, created_at) VALUES (?, ?, ?)",
            (dashboard.id, dashboard.name, dashboard.created_at.isoformat()),
        )
        self._conn.commit()

    def get(self, dashboard_id: str) -> Dashboard | None:
        row = self._conn.execute(
            "SELECT id, name, created_at FROM dashboards WHERE id = ?",
            (dashboard_id,),
        ).fetchone()
        if row is None:
            return None
        return Dashboard(id=row[0], name=row[1], created_at=datetime.fromisoformat(row[2]))

    def list_all(self) -> list[Dashboard]:
        rows = self._conn.execute(
            "SELECT id, name, created_at FROM dashboards ORDER BY created_at"
        ).fetchall()
        return [
            Dashboard(id=r[0], name=r[1], created_at=datetime.fromisoformat(r[2]))
            for r in rows
        ]
