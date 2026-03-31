"""
domain/scheduler/core/adaptors/scheduler_routes.py

Inbound FastAPI adaptor — translates HTTP requests into SchedulerService calls
and serialises canonical domain models back to JSON responses.

Rules (ADR-0006):
- HTTPException lives here, never in domain or service classes.
- No business logic here; all delegation goes to SchedulerService.
- Router is built via factory function so the service can be injected.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from domain.scheduler.core.scheduler_service import SchedulerService


# -- request/response schemas (Pydantic, boundary only) ---------------------

class CreateJobRequest(BaseModel):
    name:            str
    command:         str
    cron_expression: str


class JobResponse(BaseModel):
    id:              str
    name:            str
    command:         str
    cron_expression: str
    created_at:      str


class JobRunResponse(BaseModel):
    id:           str
    job_id:       str
    triggered_at: str
    exit_code:    int
    output:       str
    trigger_type: str


# -- router factory ---------------------------------------------------------

def build_router(service: SchedulerService) -> APIRouter:
    router = APIRouter()

    @router.post("/jobs", response_model=JobResponse, status_code=201)
    def create_job(body: CreateJobRequest) -> JobResponse:
        job = service.create_job(
            name=body.name,
            command=body.command,
            cron_expression=body.cron_expression,
        )
        return JobResponse(**job.to_dict())

    @router.get("/jobs", response_model=list[JobResponse])
    def list_jobs() -> list[JobResponse]:
        jobs = service.list_jobs()
        return [JobResponse(**j.to_dict()) for j in jobs]

    @router.delete("/jobs/{job_id}", status_code=204)
    def delete_job(job_id: str) -> None:
        deleted = service.delete_job(job_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    @router.get("/jobs/{job_id}/runs", response_model=list[JobRunResponse])
    def get_run_history(job_id: str) -> list[JobRunResponse]:
        runs = service.get_run_history(job_id)
        return [JobRunResponse(**r.to_dict()) for r in runs]

    @router.post("/jobs/{job_id}/trigger", response_model=JobRunResponse)
    def trigger_job(job_id: str) -> JobRunResponse:
        try:
            run = service.trigger_job(job_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        return JobRunResponse(**run.to_dict())

    return router
