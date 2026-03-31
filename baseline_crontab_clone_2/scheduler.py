import subprocess
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

import database
from models import Job, RunHistory

_scheduler = BackgroundScheduler()


def _cron_trigger(expr: str) -> CronTrigger:
    minute, hour, day, month, day_of_week = expr.split()
    return CronTrigger(
        minute=minute,
        hour=hour,
        day=day,
        month=month,
        day_of_week=day_of_week,
    )


def execute_job(job_id: str, triggered_manually: bool = False, db: Optional[Session] = None) -> None:
    """Run a job's command and persist the result to run history.

    When *db* is None a new session is created and closed internally (used by
    APScheduler).  When *db* is supplied (e.g. from an API endpoint) the caller
    owns the session lifecycle.
    """
    owns_session = db is None
    if owns_session:
        db = database.SessionLocal()

    try:
        job: Optional[Job] = db.query(Job).filter(Job.id == job_id).first()
        if not job or not job.is_active:
            return

        run = RunHistory(
            job_id=job_id,
            started_at=datetime.utcnow(),
            triggered_manually=triggered_manually,
            stdout="",
            stderr="",
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        try:
            result = subprocess.run(
                job.command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=3600,
            )
            run.exit_code = result.returncode
            run.stdout = result.stdout[:65535]
            run.stderr = result.stderr[:65535]
        except subprocess.TimeoutExpired:
            run.exit_code = -1
            run.stderr = "Job timed out after 3600 seconds"
        except Exception as exc:
            run.exit_code = -1
            run.stderr = str(exc)
        finally:
            run.finished_at = datetime.utcnow()
            db.commit()
    finally:
        if owns_session:
            db.close()


def add_job(job: Job) -> None:
    try:
        _scheduler.add_job(
            execute_job,
            trigger=_cron_trigger(job.cron_expression),
            id=job.id,
            args=[job.id],
            replace_existing=True,
        )
    except Exception:
        pass


def remove_job(job_id: str) -> None:
    try:
        _scheduler.remove_job(job_id)
    except Exception:
        pass


def start_scheduler(db: Session) -> None:
    for job in db.query(Job).filter(Job.is_active == True).all():
        add_job(job)
    _scheduler.start()


def stop_scheduler() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
