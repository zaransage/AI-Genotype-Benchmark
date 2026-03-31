from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional

from models import Job, RunRecord


class Storage:
    """Thread-safe store for jobs and their run history, backed by SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, Job] = {}
        self._history: Dict[str, List[RunRecord]] = {}
        _path = db_path or os.environ.get("JOBS_DB_PATH", "jobs.db")
        self._db = sqlite3.connect(_path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._init_db()
        self._load_from_db()

    # ── schema ────────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        self._db.execute(
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
        self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS run_records (
                id                  TEXT PRIMARY KEY,
                job_id              TEXT NOT NULL,
                started_at          TEXT NOT NULL,
                finished_at         TEXT,
                exit_code           INTEGER,
                stdout              TEXT NOT NULL DEFAULT '',
                stderr              TEXT NOT NULL DEFAULT '',
                triggered_manually  INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        self._db.commit()

    # ── bootstrap ─────────────────────────────────────────────────────────────

    def _load_from_db(self) -> None:
        for row in self._db.execute("SELECT * FROM jobs"):
            job = Job(
                id=row["id"],
                name=row["name"],
                command=row["command"],
                cron_expression=row["cron_expression"],
                created_at=datetime.fromisoformat(row["created_at"]),
                enabled=bool(row["enabled"]),
            )
            self._jobs[job.id] = job
            self._history[job.id] = []
        for row in self._db.execute(
            "SELECT * FROM run_records ORDER BY started_at"
        ):
            if row["job_id"] not in self._history:
                continue
            run = RunRecord(
                id=row["id"],
                job_id=row["job_id"],
                started_at=datetime.fromisoformat(row["started_at"]),
                finished_at=(
                    datetime.fromisoformat(row["finished_at"])
                    if row["finished_at"]
                    else None
                ),
                exit_code=row["exit_code"],
                stdout=row["stdout"] or "",
                stderr=row["stderr"] or "",
                triggered_manually=bool(row["triggered_manually"]),
            )
            self._history[run.job_id].append(run)

    # ── public API ────────────────────────────────────────────────────────────

    def add_job(self, job: Job) -> None:
        with self._lock:
            self._jobs[job.id] = job
            self._history[job.id] = []
            self._db.execute(
                "INSERT OR REPLACE INTO jobs VALUES (?,?,?,?,?,?)",
                (
                    job.id,
                    job.name,
                    job.command,
                    job.cron_expression,
                    job.created_at.isoformat(),
                    int(job.enabled),
                ),
            )
            self._db.commit()

    def get_job(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list_jobs(self) -> List[Job]:
        with self._lock:
            return list(self._jobs.values())

    def delete_job(self, job_id: str) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            del self._jobs[job_id]
            del self._history[job_id]
            self._db.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            self._db.execute("DELETE FROM run_records WHERE job_id = ?", (job_id,))
            self._db.commit()
            return True

    def add_run(self, run: RunRecord) -> None:
        with self._lock:
            if run.job_id in self._history:
                self._history[run.job_id].append(run)
                self._db.execute(
                    "INSERT OR REPLACE INTO run_records VALUES (?,?,?,?,?,?,?,?)",
                    (
                        run.id,
                        run.job_id,
                        run.started_at.isoformat(),
                        run.finished_at.isoformat() if run.finished_at else None,
                        run.exit_code,
                        run.stdout,
                        run.stderr,
                        int(run.triggered_manually),
                    ),
                )
                self._db.commit()

    def get_history(self, job_id: str) -> Optional[List[RunRecord]]:
        with self._lock:
            if job_id not in self._jobs:
                return None
            return list(self._history.get(job_id, []))

    def clear(self) -> None:
        """Remove all data from both memory and database (used in tests)."""
        with self._lock:
            self._jobs.clear()
            self._history.clear()
            self._db.execute("DELETE FROM jobs")
            self._db.execute("DELETE FROM run_records")
            self._db.commit()


storage = Storage()
