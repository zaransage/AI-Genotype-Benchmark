from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from models import Job
from runner import run_job

scheduler = BackgroundScheduler()

_CRON_FIELD_NAMES = ("minute", "hour", "day", "month", "day_of_week")


def _build_trigger(expression: str) -> CronTrigger:
    parts = expression.strip().split()
    if len(parts) != 5:
        raise ValueError(
            f"Invalid cron expression '{expression}': expected 5 fields "
            "(minute hour day month day_of_week), got {len(parts)}"
        )
    return CronTrigger(**dict(zip(_CRON_FIELD_NAMES, parts)))


def validate_cron(expression: str) -> None:
    """Raise ValueError if *expression* is not a valid 5-field cron string."""
    _build_trigger(expression)


def add_job(job: Job) -> None:
    trigger = _build_trigger(job.cron_expression)
    scheduler.add_job(
        func=run_job,
        trigger=trigger,
        args=[job],
        id=job.id,
        name=job.name,
        replace_existing=True,
    )


def remove_job(job_id: str) -> None:
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
