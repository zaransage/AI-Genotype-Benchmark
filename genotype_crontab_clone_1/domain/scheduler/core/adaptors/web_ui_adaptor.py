"""
domain/scheduler/core/adaptors/web_ui_adaptor.py

Inbound web-UI adaptor: serves a single-page HTML dashboard that displays
scheduled jobs and their run history by calling the existing REST API.

HTTPException belongs here — never in domain or service classes.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from domain.scheduler.core.adaptors.i_web_ui_adaptor import IWebUiAdaptor

_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Crontab Clone — Job Scheduler</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f172a; color: #e2e8f0; min-height: 100vh; padding: 2rem;
    }
    h1 { font-size: 1.6rem; color: #38bdf8; margin-bottom: 1.5rem; }
    h2 { font-size: 1.1rem; color: #94a3b8; margin-bottom: 0.75rem; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
    @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
    .panel {
      background: #1e293b; border-radius: 0.5rem; padding: 1.25rem;
      border: 1px solid #334155;
    }
    table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
    th {
      text-align: left; padding: 0.5rem 0.75rem; color: #64748b;
      border-bottom: 1px solid #334155; font-weight: 600;
    }
    td { padding: 0.5rem 0.75rem; border-bottom: 1px solid #1e293b; }
    tr:last-child td { border-bottom: none; }
    tr.clickable:hover { background: #263347; cursor: pointer; }
    tr.selected { background: #1d3a5f; }
    .badge {
      display: inline-block; padding: 0.15rem 0.55rem; border-radius: 9999px;
      font-size: 0.75rem; font-weight: 600;
    }
    .badge-success { background: #14532d; color: #4ade80; }
    .badge-failure { background: #450a0a; color: #f87171; }
    .badge-enabled  { background: #164e63; color: #38bdf8; }
    .badge-disabled { background: #27272a; color: #71717a; }
    .empty { color: #475569; font-style: italic; padding: 0.75rem 0; }
    .refresh { font-size: 0.75rem; color: #475569; margin-top: 0.5rem; }
    pre {
      background: #0f172a; border: 1px solid #334155; border-radius: 0.375rem;
      padding: 0.75rem; font-size: 0.78rem; overflow-x: auto;
      white-space: pre-wrap; word-break: break-all; max-height: 12rem;
      color: #94a3b8;
    }
    .output-cell { max-width: 220px; }
  </style>
</head>
<body>
  <h1>Crontab Clone — Job Scheduler</h1>
  <div class="grid">
    <div class="panel" id="jobs-panel">
      <h2>Scheduled Jobs <span id="job-count"></span></h2>
      <div id="jobs-table-container"><p class="empty">Loading…</p></div>
      <p class="refresh" id="jobs-refresh"></p>
    </div>
    <div class="panel" id="history-panel">
      <h2>Run History <span id="history-job-name" style="color:#38bdf8"></span></h2>
      <div id="history-table-container">
        <p class="empty">Select a job on the left to view its run history.</p>
      </div>
      <p class="refresh" id="history-refresh"></p>
    </div>
  </div>

  <script>
    "use strict";

    let _selectedJobId   = null;
    let _selectedJobName = null;

    // ----------------------------------------------------------------
    // Formatting helpers
    // ----------------------------------------------------------------
    function fmtDt(iso) {
      if (!iso) return "";
      return new Date(iso).toLocaleString(undefined, {
        year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", second: "2-digit",
      });
    }

    function badge(text, type) {
      return `<span class="badge badge-${type}">${text}</span>`;
    }

    // ----------------------------------------------------------------
    // Jobs table
    // ----------------------------------------------------------------
    async function loadJobs() {
      let jobs;
      try {
        const res = await fetch("/jobs");
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        jobs = await res.json();
      } catch (err) {
        document.getElementById("jobs-table-container").innerHTML =
          `<p class="empty">Error loading jobs: ${err.message}</p>`;
        return;
      }

      document.getElementById("job-count").textContent =
        `(${jobs.length})`;

      if (jobs.length === 0) {
        document.getElementById("jobs-table-container").innerHTML =
          '<p class="empty">No jobs registered yet.</p>';
        return;
      }

      let rows = jobs.map(j => {
        const sel = j.id === _selectedJobId ? " selected" : "";
        const statusBadge = j.enabled
          ? badge("enabled", "enabled")
          : badge("disabled", "disabled");
        return `
          <tr class="clickable${sel}" data-id="${j.id}" data-name="${escHtml(j.name)}">
            <td>${escHtml(j.name)}</td>
            <td><code>${escHtml(j.cron_expression)}</code></td>
            <td><code>${escHtml(j.command)}</code></td>
            <td>${statusBadge}</td>
            <td>${fmtDt(j.created_at)}</td>
          </tr>`;
      }).join("");

      document.getElementById("jobs-table-container").innerHTML = `
        <table>
          <thead>
            <tr>
              <th>Name</th><th>Schedule</th><th>Command</th>
              <th>Status</th><th>Created</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>`;

      document.querySelectorAll("#jobs-table-container tr.clickable").forEach(tr => {
        tr.addEventListener("click", () => {
          _selectedJobId   = tr.dataset.id;
          _selectedJobName = tr.dataset.name;
          document.querySelectorAll("#jobs-table-container tr.clickable")
            .forEach(r => r.classList.remove("selected"));
          tr.classList.add("selected");
          loadHistory(_selectedJobId, _selectedJobName);
        });
      });

      document.getElementById("jobs-refresh").textContent =
        "Last refreshed: " + new Date().toLocaleTimeString();
    }

    // ----------------------------------------------------------------
    // Run-history table
    // ----------------------------------------------------------------
    async function loadHistory(jobId, jobName) {
      document.getElementById("history-job-name").textContent =
        jobName ? `— ${jobName}` : "";

      let runs;
      try {
        const res = await fetch(`/jobs/${encodeURIComponent(jobId)}/runs`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        runs = await res.json();
      } catch (err) {
        document.getElementById("history-table-container").innerHTML =
          `<p class="empty">Error loading history: ${err.message}</p>`;
        return;
      }

      if (runs.length === 0) {
        document.getElementById("history-table-container").innerHTML =
          '<p class="empty">No runs recorded for this job yet.</p>';
        return;
      }

      const rows = [...runs].reverse().map(r => {
        const statusBadge = r.status === "success"
          ? badge("success", "success")
          : badge("failure", "failure");
        return `
          <tr>
            <td>${fmtDt(r.triggered_at)}</td>
            <td>${statusBadge}</td>
            <td class="output-cell"><pre>${escHtml(r.output)}</pre></td>
          </tr>`;
      }).join("");

      document.getElementById("history-table-container").innerHTML = `
        <table>
          <thead>
            <tr><th>Triggered At</th><th>Status</th><th>Output</th></tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>`;

      document.getElementById("history-refresh").textContent =
        "Last refreshed: " + new Date().toLocaleTimeString();
    }

    // ----------------------------------------------------------------
    // XSS guard
    // ----------------------------------------------------------------
    function escHtml(str) {
      return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    // ----------------------------------------------------------------
    // Auto-refresh
    // ----------------------------------------------------------------
    async function refresh() {
      await loadJobs();
      if (_selectedJobId) {
        await loadHistory(_selectedJobId, _selectedJobName);
      }
    }

    refresh();
    setInterval(refresh, 30_000);
  </script>
</body>
</html>
"""


class WebUiAdaptor(IWebUiAdaptor):
    """Serves the single-page HTML dashboard at GET /ui."""

    # ------------------------------------------------------------------
    # IWebUiAdaptor implementation
    # ------------------------------------------------------------------

    def register_routes(self, app: FastAPI) -> None:
        @app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
        async def _dashboard() -> HTMLResponse:
            return HTMLResponse(content=_HTML)
