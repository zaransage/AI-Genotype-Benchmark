"""SQLiteJobRepository — persistent SQLite implementation of IJobRepository."""
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

from domain.scheduler.core.job import Job
from domain.scheduler.core.run_record import RunRecord
from domain.scheduler.ports.i_job_repository import IJobRepository

_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


class SQLiteJobRepository(IJobRepository):

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_schema()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id              TEXT PRIMARY KEY,
                    name            TEXT NOT NULL,
                    command         TEXT NOT NULL,
                    cron_expression TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    enabled         INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS run_records (
                    id           TEXT PRIMARY KEY,
                    job_id       TEXT NOT NULL,
                    triggered_at TEXT NOT NULL,
                    status       TEXT NOT NULL,
                    output       TEXT NOT NULL,
                    duration_s   REAL NOT NULL
                )
                """
            )

    @staticmethod
    def _row_to_job(row: sqlite3.Row) -> Job:
        return Job(
            id=row["id"],
            name=row["name"],
            command=row["command"],
            cron_expression=row["cron_expression"],
            created_at=datetime.strptime(row["created_at"], _DATE_FORMAT).replace(tzinfo=timezone.utc),
            enabled=bool(row["enabled"]),
        )

    @staticmethod
    def _row_to_run_record(row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            id=row["id"],
            job_id=row["job_id"],
            triggered_at=datetime.strptime(row["triggered_at"], _DATE_FORMAT).replace(tzinfo=timezone.utc),
            status=row["status"],
            output=row["output"],
            duration_s=row["duration_s"],
        )

    # ── IJobRepository ────────────────────────────────────────────────────────

    def save(self, job: Job) -> None:
        with self._connect() as conn:
            conn.execute(
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
                    job.created_at.strftime(_DATE_FORMAT),
                    1 if job.enabled else 0,
                ),
            )

    def find_by_id(self, job_id: str) -> Optional[Job]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_job(row)

    def find_all(self) -> List[Job]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM jobs").fetchall()
        return [self._row_to_job(r) for r in rows]

    def delete(self, job_id: str) -> None:
        with self._connect() as conn:
            cur = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            if cur.rowcount == 0:
                raise KeyError(f"Job not found: {job_id!r}")

    def save_run_record(self, record: RunRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO run_records (id, job_id, triggered_at, status, output, duration_s)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.job_id,
                    record.triggered_at.strftime(_DATE_FORMAT),
                    record.status,
                    record.output,
                    record.duration_s,
                ),
            )

    def find_run_records(self, job_id: str) -> List[RunRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM run_records WHERE job_id = ?", (job_id,)
            ).fetchall()
        return [self._row_to_run_record(r) for r in rows]
