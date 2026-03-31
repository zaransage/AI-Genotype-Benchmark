"""SQLite outbound-port implementation of IMetricValueRepository.

Receives a sqlite3.Connection from the composition root (main.py).
Creates the metric_values table on first use.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

from domain.core.models import MetricValue
from domain.core.ports.i_metric_value_repository import IMetricValueRepository


class SqliteMetricValueRepository(IMetricValueRepository):
    """Persists MetricValue objects in a SQLite database table."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._conn = connection
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS metric_values (
                id          TEXT PRIMARY KEY,
                widget_id   TEXT NOT NULL,
                value       REAL NOT NULL,
                recorded_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def append(self, metric_value: MetricValue) -> None:
        self._conn.execute(
            "INSERT INTO metric_values (id, widget_id, value, recorded_at) VALUES (?, ?, ?, ?)",
            (
                metric_value.id,
                metric_value.widget_id,
                metric_value.value,
                metric_value.recorded_at.isoformat(),
            ),
        )
        self._conn.commit()

    def list_by_widget(self, widget_id: str) -> list[MetricValue]:
        rows = self._conn.execute(
            "SELECT id, widget_id, value, recorded_at FROM metric_values WHERE widget_id = ? ORDER BY recorded_at",
            (widget_id,),
        ).fetchall()
        return [
            MetricValue(
                id=r[0],
                widget_id=r[1],
                value=r[2],
                recorded_at=datetime.fromisoformat(r[3]),
            )
            for r in rows
        ]
