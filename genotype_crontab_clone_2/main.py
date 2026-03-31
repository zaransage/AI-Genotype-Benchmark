"""
Composition root — wires concrete types and starts the application.

Rules (ADR 0008, AI_CONTRACT §8, §9):
- The only place that knows about concrete types.
- logging.basicConfig called here, nowhere else.
- Dependencies injected into commands; commands injected into the router.
"""
import logging

from fastapi import FastAPI

from domain.scheduler.adaptors.rest_adaptor import build_router
from domain.scheduler.adaptors.web_ui_adaptor import build_ui_router
from domain.scheduler.core.commands import (
    CreateJobCommand,
    DeleteJobCommand,
    GetRunHistoryCommand,
    ListJobsCommand,
    TriggerJobCommand,
)
from domain.scheduler.ports.sqlite_job_repository import SQLiteJobRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="Crontab Clone — Job Scheduler API",
    description="Schedule, list, trigger, and inspect named jobs via a REST API.",
    version="0.1.0",
)

_repo = SQLiteJobRepository(db_path="jobs.db")

app.include_router(
    build_router(
        create_cmd=CreateJobCommand(repo=_repo),
        list_cmd=ListJobsCommand(repo=_repo),
        delete_cmd=DeleteJobCommand(repo=_repo),
        trigger_cmd=TriggerJobCommand(repo=_repo),
        history_cmd=GetRunHistoryCommand(repo=_repo),
    )
)

app.include_router(
    build_ui_router(
        list_cmd=ListJobsCommand(repo=_repo),
        history_cmd=GetRunHistoryCommand(repo=_repo),
    )
)
