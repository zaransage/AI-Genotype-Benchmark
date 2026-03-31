"""
RestAdaptor — FastAPI router for the scheduler.

Rules (ADR 0006, AI_CONTRACT §9):
- HTTPException lives here, never in commands or domain.
- Translates canonical dataclasses to JSON-serialisable dicts.
- Receives pre-built command objects (injected by composition root).
"""
import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from domain.scheduler.core.commands import (
    CreateJobCommand,
    DeleteJobCommand,
    GetRunHistoryCommand,
    ListJobsCommand,
    TriggerJobCommand,
)
from domain.scheduler.core.job import Job
from domain.scheduler.core.run_record import RunRecord

logger = logging.getLogger(__name__)


# ── Request / Response schemas (Pydantic — boundary only) ────────────────────

class CreateJobRequest(BaseModel):
    name:            str
    command:         str
    cron_expression: str


# ── Serialisers (canonical model → dict) ─────────────────────────────────────

def _job_to_dict(job: Job) -> Dict[str, Any]:
    return {
        "id":              job.id,
        "name":            job.name,
        "command":         job.command,
        "cron_expression": job.cron_expression,
        "created_at":      job.created_at.strftime(job.DATE_FORMAT),
        "enabled":         job.enabled,
    }


def _run_record_to_dict(rr: RunRecord) -> Dict[str, Any]:
    return {
        "id":           rr.id,
        "job_id":       rr.job_id,
        "triggered_at": rr.triggered_at.strftime(rr.DATE_FORMAT),
        "status":       rr.status,
        "output":       rr.output,
        "duration_s":   rr.duration_s,
    }


# ── Router factory (injected commands) ───────────────────────────────────────

def build_router(
    create_cmd:  CreateJobCommand,
    list_cmd:    ListJobsCommand,
    delete_cmd:  DeleteJobCommand,
    trigger_cmd: TriggerJobCommand,
    history_cmd: GetRunHistoryCommand,
) -> APIRouter:

    router = APIRouter()

    @router.post("/jobs", status_code=201)
    def create_job(body: CreateJobRequest) -> Dict[str, Any]:
        try:
            job = create_cmd.execute(
                name=body.name,
                command=body.command,
                cron_expression=body.cron_expression,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        return _job_to_dict(job)

    @router.get("/jobs")
    def list_jobs() -> List[Dict[str, Any]]:
        return [_job_to_dict(j) for j in list_cmd.execute()]

    @router.delete("/jobs/{job_id}", status_code=204)
    def delete_job(job_id: str) -> Response:
        try:
            delete_cmd.execute(job_id=job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return Response(status_code=204)

    @router.post("/jobs/{job_id}/trigger", status_code=201)
    def trigger_job(job_id: str) -> Dict[str, Any]:
        try:
            rr = trigger_cmd.execute(job_id=job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return _run_record_to_dict(rr)

    @router.get("/jobs/{job_id}/history")
    def get_run_history(job_id: str) -> List[Dict[str, Any]]:
        try:
            records = history_cmd.execute(job_id=job_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return [_run_record_to_dict(r) for r in records]

    return router
