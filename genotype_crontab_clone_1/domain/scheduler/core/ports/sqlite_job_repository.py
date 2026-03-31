"""
domain/scheduler/core/ports/sqlite_job_repository.py

SQLite-backed implementation of IJobRepository.
Persists jobs and run records across restarts.
Config (db_path) is passed in at construction; the composition root owns it.
"""
from __future__ import annotations

import sqlite3
import threading
from datetime import datetime, timezone

from domain.scheduler.core.job import Job, RunRecord
from domain.scheduler.core.ports.i_job_repository import IJobRepository

_ISO_FMT = "%Y-%m-%dT%H:%M:%S.%f%z"


def _parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 string produced by datetime.isoformat()."""
    return datetime.fromisoformat(value)


class SqliteJobRepository(IJobRepository):
    """Thread-safe SQLite-backed store for jobs and run records.

    A single connection is kept open for the lifetime of the repository.
    WAL mode and check_same_thread=False are enabled so that multiple
    FastAPI worker threads may share the connection safely via the
    per-operation lock.
    """

    def __init__(self, db_path: str) -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            db_path,
            check_same_thread=False,
            isolation_level=None,   # autocommit; we manage transactions explicitly
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _create_tables(self) -> None:
        with self._lock:
            self._conn.executescript("""
                BEGIN;
                CREATE TABLE IF NOT EXISTS jobs (
                    id              TEXT PRIMARY KEY,
                    name            TEXT NOT NULL,
                    command         TEXT NOT NULL,
                    cron_expression TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    enabled         INTEGER NOT NULL DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS run_records (
                    id           TEXT PRIMARY KEY,
                    job_id       TEXT NOT NULL,
                    triggered_at TEXT NOT NULL,
                    status       TEXT NOT NULL,
                    output       TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_run_records_job_id
                    ON run_records(job_id);
                COMMIT;
            """)

    # ------------------------------------------------------------------
    # IJobRepository
    # ------------------------------------------------------------------

    def save(self, job: Job) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO jobs (id, name, command, cron_expression, created_at, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name            = excluded.name,
                    command         = excluded.command,
                    cron_expression = excluded.cron_expression,
                    created_at      = excluded.created_at,
                    enabled         = excluded.enabled
                """,
                (
                    job.id,
                    job.name,
                    job.command,
                    job.cron_expression,
                    job.created_at.isoformat(),
                    int(job.enabled),
                ),
            )

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, name, command, cron_expression, created_at, enabled "
                "FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def list(self) -> list[Job]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, name, command, cron_expression, created_at, enabled "
                "FROM jobs ORDER BY created_at"
            ).fetchall()
        return [self._row_to_job(r) for r in rows]

    def delete(self, job_id: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

    def save_run(self, run: RunRecord) -> None:
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO run_records (id, job_id, triggered_at, status, output)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO NOTHING
                """,
                (
                    run.id,
                    run.job_id,
                    run.triggered_at.isoformat(),
                    run.status,
                    run.output,
                ),
            )

    def get_runs(self, job_id: str) -> list[RunRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT id, job_id, triggered_at, status, output "
                "FROM run_records WHERE job_id = ? ORDER BY triggered_at",
                (job_id,),
            ).fetchall()
        return [self._row_to_run(r) for r in rows]

    # ------------------------------------------------------------------
    # Row → canonical model helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _row_to_job(row: tuple) -> Job:
        id_, name, command, cron_expression, created_at_str, enabled_int = row
        return Job(
            id              = id_,
            name            = name,
            command         = command,
            cron_expression = cron_expression,
            created_at      = _parse_dt(created_at_str),
            enabled         = bool(enabled_int),
        )

    @staticmethod
    def _row_to_run(row: tuple) -> RunRecord:
        id_, job_id, triggered_at_str, status, output = row
        return RunRecord(
            id           = id_,
            job_id       = job_id,
            triggered_at = _parse_dt(triggered_at_str),
            status       = status,
            output       = output,
        )
