"""APScheduler wrapper for background cron job execution."""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

scheduler = BackgroundScheduler()


def _run_scheduled_job(job_id: str, db_factory):
    from models import JobORM
    from jobs import execute_command

    db = db_factory()
    try:
        job = db.query(JobORM).filter(JobORM.id == job_id).first()
        if job and job.enabled:
            execute_command(job, db, triggered_manually=False)
    finally:
        db.close()


def add_scheduled_job(job_id: str, cron_expression: str, db_factory):
    """Register (or replace) a cron job in the scheduler."""
    trigger = CronTrigger.from_crontab(cron_expression)
    scheduler.add_job(
        _run_scheduled_job,
        trigger=trigger,
        id=job_id,
        args=[job_id, db_factory],
        replace_existing=True,
    )


def remove_scheduled_job(job_id: str):
    """Remove a job from the scheduler (silent if not present)."""
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
