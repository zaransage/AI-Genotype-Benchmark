"""
domain/scheduler/core/ports/sqlite_job_repository.py

SQLite-backed implementation of IJobRepository.
Persists jobs and run history across process restarts.

Config: db_path is injected by the composition root (main.py).
logging.basicConfig() must NOT be called here (ADR-0006).
"""

import sqlite3
from typing import Optional

from domain.scheduler.core.job                    import Job
from domain.scheduler.core.job_run                import JobRun
from domain.scheduler.core.ports.i_job_repository import IJobRepository


class SqliteJobRepository(IJobRepository):

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._init_db()

    # -- schema bootstrap -------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id              TEXT PRIMARY KEY,
                    name            TEXT NOT NULL,
                    command         TEXT NOT NULL,
                    cron_expression TEXT NOT NULL,
                    created_at      TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_runs (
                    id           TEXT PRIMARY KEY,
                    job_id       TEXT NOT NULL,
                    triggered_at TEXT NOT NULL,
                    exit_code    INTEGER NOT NULL,
                    output       TEXT NOT NULL,
                    trigger_type TEXT NOT NULL
                )
            """)

    # -- IJobRepository implementation ------------------------------------------

    def save(self, job: Job) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO jobs (id, name, command, cron_expression, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (job.id, job.name, job.command, job.cron_expression, job.created_at),
            )

    def find_by_id(self, job_id: str) -> Optional[Job]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, name, command, cron_expression, created_at FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return Job(
            id=row["id"],
            name=row["name"],
            command=row["command"],
            cron_expression=row["cron_expression"],
            created_at=row["created_at"],
        )

    def find_all(self) -> list[Job]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, name, command, cron_expression, created_at FROM jobs "
                "ORDER BY created_at ASC"
            ).fetchall()
        return [
            Job(
                id=r["id"],
                name=r["name"],
                command=r["command"],
                cron_expression=r["cron_expression"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def delete(self, job_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        return cursor.rowcount > 0

    def save_run(self, run: JobRun) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO job_runs "
                "(id, job_id, triggered_at, exit_code, output, trigger_type) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (run.id, run.job_id, run.triggered_at, run.exit_code, run.output, run.trigger_type),
            )

    def find_runs(self, job_id: str) -> list[JobRun]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, job_id, triggered_at, exit_code, output, trigger_type "
                "FROM job_runs WHERE job_id = ? ORDER BY triggered_at ASC",
                (job_id,),
            ).fetchall()
        return [
            JobRun(
                id=r["id"],
                job_id=r["job_id"],
                triggered_at=r["triggered_at"],
                exit_code=r["exit_code"],
                output=r["output"],
                trigger_type=r["trigger_type"],
            )
            for r in rows
        ]
