"""
domain/scheduler/core/adaptors/ui_routes.py

Inbound adaptor — serves a browser UI that displays scheduled jobs and their
run history. The page fetches data from the existing REST endpoints via JS fetch().

Rules (ADR-0006):
- No business logic here; all data comes through SchedulerService.
- HTTPException stays at route level if needed.
- Router is built via factory so the service can be injected.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from domain.scheduler.core.scheduler_service import SchedulerService

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Scheduler</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body   { font-family: monospace; background: #0d0d0d; color: #e0e0e0; padding: 2rem; }
    h1     { color: #7ab4ff; margin-bottom: 0.5rem; }
    h2     { color: #7ab4ff; margin: 1.5rem 0 0.5rem; }
    p      { margin: 0.25rem 0; }
    table  { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #333; padding: 0.4rem 0.75rem; text-align: left; white-space: nowrap; }
    th     { background: #1a1a1a; color: #aac; }
    td.wrap { white-space: pre-wrap; word-break: break-all; max-width: 24rem; }
    tr.clickable:hover   { background: #1a1a2e; cursor: pointer; }
    tr.selected          { background: #1a2a4a !important; }
    button {
      background: #1a2a4a; color: #7ab4ff; border: 1px solid #335577;
      padding: 0.3rem 0.9rem; cursor: pointer; font-family: monospace;
    }
    button:hover { background: #243a5a; }
    #status { color: #f0a030; min-height: 1.2rem; margin: 0.5rem 0; }
    #runs-section { display: none; margin-top: 1.5rem; }
    .exit-ok  { color: #4caf50; }
    .exit-err { color: #f44336; }
  </style>
</head>
<body>
  <h1>Crontab Clone &mdash; Job Scheduler</h1>
  <p id="status"></p>
  <button onclick="loadJobs()">&#x21bb; Refresh</button>

  <h2>Scheduled Jobs</h2>
  <table>
    <thead>
      <tr>
        <th>ID</th><th>Name</th><th>Command</th>
        <th>Cron</th><th>Created At</th>
      </tr>
    </thead>
    <tbody id="jobs-body"></tbody>
  </table>

  <div id="runs-section">
    <h2>Run History &mdash; <span id="runs-job-name"></span></h2>
    <table>
      <thead>
        <tr>
          <th>Run ID</th><th>Triggered At</th>
          <th>Exit</th><th>Type</th><th>Output</th>
        </tr>
      </thead>
      <tbody id="runs-body"></tbody>
    </table>
  </div>

  <script>
    function esc(s) {
      return String(s)
        .replace(/&/g,"&amp;").replace(/</g,"&lt;")
        .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
    }

    async function loadJobs() {
      const status = document.getElementById("status");
      status.textContent = "Loading jobs\u2026";
      try {
        const resp = await fetch("/jobs");
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        const jobs = await resp.json();
        const tbody = document.getElementById("jobs-body");
        tbody.innerHTML = "";
        jobs.forEach(job => {
          const tr = document.createElement("tr");
          tr.className = "clickable";
          tr.innerHTML =
            "<td>" + esc(job.id) + "</td>" +
            "<td>" + esc(job.name) + "</td>" +
            "<td class='wrap'>" + esc(job.command) + "</td>" +
            "<td>" + esc(job.cron_expression) + "</td>" +
            "<td>" + esc(job.created_at) + "</td>";
          tr.addEventListener("click", () => loadRuns(job.id, job.name, tr));
          tbody.appendChild(tr);
        });
        status.textContent = jobs.length + " job(s).";
        document.getElementById("runs-section").style.display = "none";
      } catch (e) {
        status.textContent = "Error loading jobs: " + e.message;
      }
    }

    async function loadRuns(jobId, jobName, row) {
      document.querySelectorAll("#jobs-body tr").forEach(r => r.classList.remove("selected"));
      row.classList.add("selected");
      const status = document.getElementById("status");
      status.textContent = "Loading run history\u2026";
      try {
        const resp = await fetch("/jobs/" + encodeURIComponent(jobId) + "/runs");
        if (!resp.ok) throw new Error("HTTP " + resp.status);
        const runs = await resp.json();
        document.getElementById("runs-job-name").textContent = jobName;
        const tbody = document.getElementById("runs-body");
        tbody.innerHTML = "";
        runs.forEach(run => {
          const exitCls = run.exit_code === 0 ? "exit-ok" : "exit-err";
          const tr = document.createElement("tr");
          tr.innerHTML =
            "<td>" + esc(run.id) + "</td>" +
            "<td>" + esc(run.triggered_at) + "</td>" +
            "<td class='" + exitCls + "'>" + esc(run.exit_code) + "</td>" +
            "<td>" + esc(run.trigger_type) + "</td>" +
            "<td class='wrap'>" + esc(run.output) + "</td>";
          tbody.appendChild(tr);
        });
        document.getElementById("runs-section").style.display = "block";
        status.textContent = runs.length + " run(s) for " + jobName + ".";
      } catch (e) {
        status.textContent = "Error loading runs: " + e.message;
      }
    }

    loadJobs();
  </script>
</body>
</html>"""


def build_ui_router(service: SchedulerService) -> APIRouter:  # noqa: ARG001
    router = APIRouter()

    @router.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    def ui_dashboard() -> HTMLResponse:
        return HTMLResponse(content=_HTML, status_code=200)

    return router
