from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

import scheduler as sched_module
from models import Job, JobCreate, RunRecord
from runner import run_job
from storage import storage

_TEMPLATE = Path(__file__).parent / "templates" / "index.html"


@asynccontextmanager
async def lifespan(app: FastAPI):
    sched_module.scheduler.start()
    yield
    sched_module.scheduler.shutdown(wait=False)


app = FastAPI(title="Job Scheduler API", version="1.0.0", lifespan=lifespan)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse(_TEMPLATE.read_text())


@app.post("/jobs", response_model=Job, status_code=201)
def create_job(payload: JobCreate):
    try:
        sched_module.validate_cron(payload.cron_expression)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    job = Job(
        name=payload.name,
        command=payload.command,
        cron_expression=payload.cron_expression,
    )
    storage.add_job(job)
    sched_module.add_job(job)
    return job


@app.get("/jobs", response_model=List[Job])
def list_jobs():
    return storage.list_jobs()


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str):
    removed = storage.delete_job(job_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Job not found")
    sched_module.remove_job(job_id)


@app.get("/jobs/{job_id}/history", response_model=List[RunRecord])
def job_history(job_id: str):
    history = storage.get_history(job_id)
    if history is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return history


@app.post("/jobs/{job_id}/trigger", response_model=RunRecord, status_code=202)
def trigger_job(job_id: str):
    job = storage.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return run_job(job, triggered_manually=True)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
