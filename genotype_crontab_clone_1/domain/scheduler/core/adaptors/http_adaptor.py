"""
domain/scheduler/core/adaptors/http_adaptor.py

Inbound HTTP adaptor: FastAPI router that translates HTTP requests into
SchedulerService calls and serialises canonical models back to JSON.

HTTPException belongs here — never in domain or service classes.
"""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from domain.scheduler.core.adaptors.i_http_adaptor import IHttpAdaptor
from domain.scheduler.core.scheduler_service import SchedulerService


# ---------------------------------------------------------------------------
# Request / response Pydantic models (boundary only — not canonical models)
# ---------------------------------------------------------------------------

class CreateJobRequest(BaseModel):
    name:            str
    command:         str
    cron_expression: str


# ---------------------------------------------------------------------------
# Adaptor
# ---------------------------------------------------------------------------

class HttpAdaptor(IHttpAdaptor):
    """FastAPI-backed inbound adaptor for the scheduler domain."""

    def __init__(self, service: SchedulerService) -> None:
        self._service = service
        self.router   = APIRouter()
        self._register_routes()

    # ------------------------------------------------------------------
    # IHttpAdaptor implementation
    # ------------------------------------------------------------------

    def create_job(self, name: str, command: str, cron_expression: str) -> dict:
        try:
            job = self._service.create_job(
                name            = name,
                command         = command,
                cron_expression = cron_expression,
            )
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return self._job_to_dict(job)

    def list_jobs(self) -> list[dict]:
        return [self._job_to_dict(j) for j in self._service.list_jobs()]

    def delete_job(self, job_id: str) -> None:
        if self._service.get_job(job_id) is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
        self._service.delete_job(job_id)

    def get_run_history(self, job_id: str) -> list[dict]:
        if self._service.get_job(job_id) is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
        return [self._run_to_dict(r) for r in self._service.get_run_history(job_id)]

    def trigger_job(self, job_id: str) -> dict:
        if self._service.get_job(job_id) is None:
            raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
        try:
            run = self._service.trigger_job(job_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        return self._run_to_dict(run)

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def _register_routes(self) -> None:
        router = self.router

        @router.post("/jobs", status_code=201)
        async def _create_job(body: CreateJobRequest) -> dict:
            return self.create_job(
                name            = body.name,
                command         = body.command,
                cron_expression = body.cron_expression,
            )

        @router.get("/jobs", status_code=200)
        async def _list_jobs() -> list:
            return self.list_jobs()

        @router.delete("/jobs/{job_id}", status_code=204)
        async def _delete_job(job_id: str) -> None:
            self.delete_job(job_id)

        @router.get("/jobs/{job_id}/runs", status_code=200)
        async def _get_run_history(job_id: str) -> list:
            return self.get_run_history(job_id)

        @router.post("/jobs/{job_id}/trigger", status_code=200)
        async def _trigger_job(job_id: str) -> dict:
            return self.trigger_job(job_id)

    # ------------------------------------------------------------------
    # Serialisation helpers (canonical model → dict)
    # ------------------------------------------------------------------

    @staticmethod
    def _job_to_dict(job) -> dict:
        return {
            "id":              job.id,
            "name":            job.name,
            "command":         job.command,
            "cron_expression": job.cron_expression,
            "created_at":      job.created_at.isoformat(),
            "enabled":         job.enabled,
        }

    @staticmethod
    def _run_to_dict(run) -> dict:
        return {
            "id":           run.id,
            "job_id":       run.job_id,
            "triggered_at": run.triggered_at.isoformat(),
            "status":       run.status,
            "output":       run.output,
        }
