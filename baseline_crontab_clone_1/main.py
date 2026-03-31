"""FastAPI application – crontab-clone job scheduler."""

import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

import database
from database import Base, SessionLocal, engine, get_db
from jobs import execute_command
from models import JobCreate, JobORM, JobResponse, JobRunORM, JobRunResponse
from scheduler import add_scheduled_job, remove_scheduled_job, scheduler

_TEMPLATE_DIR = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)

    scheduler.start()

    # Re-register any jobs that were persisted from a previous run.
    db = database.SessionLocal()
    try:
        for job in db.query(JobORM).filter(JobORM.enabled.is_(True)).all():
            add_scheduled_job(job.id, job.cron_expression, database.SessionLocal)
    finally:
        db.close()

    yield

    scheduler.shutdown(wait=False)


app = FastAPI(
    title="Job Scheduler API",
    description="A crontab-clone REST API for scheduling and managing jobs.",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def web_ui():
    """Serve the web UI for browsing jobs and run history."""
    return (_TEMPLATE_DIR / "index.html").read_text()


@app.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    """Create a new scheduled job."""
    try:
        CronTrigger.from_crontab(payload.cron_expression)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid cron expression")

    job = JobORM(
        id=str(uuid.uuid4()),
        name=payload.name,
        command=payload.command,
        cron_expression=payload.cron_expression,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    add_scheduled_job(job.id, job.cron_expression, database.SessionLocal)
    return job


@app.get("/jobs", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    """Return all registered jobs."""
    return db.query(JobORM).all()


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job and its run history."""
    job = db.query(JobORM).filter(JobORM.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    remove_scheduled_job(job_id)
    db.delete(job)
    db.commit()


@app.get("/jobs/{job_id}/history", response_model=List[JobRunResponse])
def job_history(job_id: str, db: Session = Depends(get_db)):
    """Return the run history for a job, most recent first."""
    job = db.query(JobORM).filter(JobORM.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    runs = (
        db.query(JobRunORM)
        .filter(JobRunORM.job_id == job_id)
        .order_by(JobRunORM.started_at.desc())
        .all()
    )
    return runs


@app.post("/jobs/{job_id}/trigger", response_model=JobRunResponse)
def trigger_job(job_id: str, db: Session = Depends(get_db)):
    """Manually trigger a job and wait for it to finish."""
    job = db.query(JobORM).filter(JobORM.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    run = execute_command(job, db, triggered_manually=True)
    return run
