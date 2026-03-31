"""
WebUIAdaptor — FastAPI router serving the HTML dashboard.

Rules (ADR 0006, AI_CONTRACT §9):
- HTTPException lives here, never in domain.
- Receives pre-built command objects (injected by composition root).
- Builds HTML via string concatenation to avoid conflict with CSS braces.
"""
import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from domain.scheduler.core.commands import GetRunHistoryCommand, ListJobsCommand

logger = logging.getLogger(__name__)

_CSS = """
body  { font-family: sans-serif; margin: 2rem; background: #fafafa; color: #333; }
h1    { border-bottom: 2px solid #ccc; padding-bottom: 0.5rem; }
h2    { margin-top: 2rem; color: #555; }
h3    { margin-top: 1rem; font-size: 0.95rem; color: #666; }
table { border-collapse: collapse; width: 100%; margin-bottom: 1rem; font-size: 0.9rem; }
th, td { border: 1px solid #ddd; padding: 0.4rem 0.8rem; text-align: left; }
th    { background: #f0f0f0; font-weight: bold; }
code  { background: #eee; padding: 0.1rem 0.3rem; border-radius: 3px; }
pre   { margin: 0; white-space: pre-wrap; word-break: break-all; }
.success { color: #2a7a2a; font-weight: bold; }
.failure { color: #c0392b; font-weight: bold; }
.running { color: #e67e22; font-weight: bold; }
.no-runs  { color: #999; font-style: italic; }
"""


def _page(body: str) -> str:
    return (
        "<!DOCTYPE html>"
        "<html lang='en'>"
        "<head>"
        "<meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1.0'>"
        "<title>Crontab Clone — Dashboard</title>"
        f"<style>{_CSS}</style>"
        "</head>"
        f"<body><h1>Scheduled Jobs</h1>{body}</body>"
        "</html>"
    )


def _job_table(job: Any) -> str:
    enabled_label = "yes" if job.enabled else "no"
    created = job.created_at.strftime(job.DATE_FORMAT)
    return (
        "<table>"
        "<thead><tr>"
        "<th>ID</th><th>Name</th><th>Command</th>"
        "<th>Cron</th><th>Created</th><th>Enabled</th>"
        "</tr></thead>"
        "<tbody><tr>"
        f"<td>{job.id}</td>"
        f"<td>{job.name}</td>"
        f"<td><code>{job.command}</code></td>"
        f"<td>{job.cron_expression}</td>"
        f"<td>{created}</td>"
        f"<td>{enabled_label}</td>"
        "</tr></tbody>"
        "</table>"
    )


def _history_table(records: list) -> str:
    if not records:
        return "<p class='no-runs'>No runs yet.</p>"
    rows = ""
    for r in records:
        triggered = r.triggered_at.strftime(r.DATE_FORMAT)
        output_text = r.output or "(no output)"
        rows += (
            "<tr>"
            f"<td>{triggered}</td>"
            f"<td class='{r.status}'>{r.status}</td>"
            f"<td>{r.duration_s}s</td>"
            f"<td><pre>{output_text}</pre></td>"
            "</tr>"
        )
    return (
        "<h3>Run History</h3>"
        "<table>"
        "<thead><tr>"
        "<th>Triggered</th><th>Status</th><th>Duration</th><th>Output</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table>"
    )


def build_ui_router(
    list_cmd:    ListJobsCommand,
    history_cmd: GetRunHistoryCommand,
) -> APIRouter:

    router = APIRouter()

    @router.get("/ui", response_class=HTMLResponse)
    def jobs_page() -> Any:
        jobs = list_cmd.execute()
        if not jobs:
            return HTMLResponse(_page("<p>No jobs scheduled.</p>"))

        sections = ""
        for job in jobs:
            try:
                records = history_cmd.execute(job_id=job.id)
            except KeyError:
                records = []
            sections += (
                f"<h2>{job.name}</h2>"
                + _job_table(job)
                + _history_table(records)
            )
        return HTMLResponse(_page(sections))

    return router
