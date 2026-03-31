"""
main.py — composition root

The only place that knows about concrete types.
Wires SqliteJobRepository → SchedulerService → FastAPI routers.

Rules (ADR-0006):
- logging.basicConfig() belongs here, not inside any class constructor.
- All concrete dependencies are instantiated and injected here.
"""

import logging
import os

from fastapi import FastAPI

from domain.scheduler.core.ports.sqlite_job_repository  import SqliteJobRepository
from domain.scheduler.core.scheduler_service            import SchedulerService
from domain.scheduler.core.adaptors.scheduler_routes    import build_router
from domain.scheduler.core.adaptors.ui_routes           import build_ui_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

# -- wire concrete types ----------------------------------------------------
_db_path = os.environ.get("SCHEDULER_DB_PATH", "scheduler.sqlite3")
_repo    = SqliteJobRepository(db_path=_db_path)
_service = SchedulerService(repo=_repo)
_router  = build_router(service=_service)
_ui      = build_ui_router(service=_service)

# -- application ------------------------------------------------------------
app = FastAPI(
    title="Crontab Clone — Job Scheduler API",
    description="REST API for creating, listing, triggering, and deleting scheduled jobs.",
    version="1.0.0",
)
app.include_router(_router)
app.include_router(_ui)
