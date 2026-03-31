"""
main.py — Composition root.

The only module that knows about concrete types.
Wires together: SqliteJobRepository, SubprocessJobExecutor,
SchedulerService, HttpAdaptor, WebUiAdaptor, and FastAPI.
"""
import logging
import os

from fastapi import FastAPI

from domain.scheduler.core.adaptors.http_adaptor    import HttpAdaptor
from domain.scheduler.core.adaptors.web_ui_adaptor  import WebUiAdaptor
from domain.scheduler.core.ports.sqlite_job_repository import SqliteJobRepository
from domain.scheduler.core.ports.subprocess_job_executor import SubprocessJobExecutor
from domain.scheduler.core.scheduler_service        import SchedulerService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

# ------------------------------------------------------------------
# Wire concrete implementations
# ------------------------------------------------------------------
_db_path    = os.environ.get("SCHEDULER_DB_PATH", "scheduler.db")
_repository = SqliteJobRepository(db_path=_db_path)
_executor   = SubprocessJobExecutor()
_service    = SchedulerService(repository=_repository, executor=_executor)
_adaptor    = HttpAdaptor(service=_service)
_web_ui     = WebUiAdaptor()

# ------------------------------------------------------------------
# FastAPI application
# ------------------------------------------------------------------
app = FastAPI(
    title       = "Crontab Clone — Job Scheduler API",
    description = "REST API for managing and triggering scheduled jobs.",
    version     = "0.0.1",
)
app.include_router(_adaptor.router)
_web_ui.register_routes(app)
