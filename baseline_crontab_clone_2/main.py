import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

import database
from database import Base, engine, get_db
from models import Job, JobCreate, JobResponse, RunHistory, RunHistoryResponse
from scheduler import add_job, execute_job, remove_job, start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if not os.getenv("TESTING"):
        db = database.SessionLocal()
        try:
            start_scheduler(db)
        finally:
            db.close()
    yield
    if not os.getenv("TESTING"):
        stop_scheduler()


app = FastAPI(title="Job Scheduler API", version="1.0.0", lifespan=lifespan)

_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Job Scheduler</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f5f5f5; color: #333; padding: 24px; }
    h1 { font-size: 1.6rem; margin-bottom: 20px; }
    h2 { font-size: 1.1rem; margin: 20px 0 10px; }
    table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 6px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    th { background: #2c3e50; color: #fff; padding: 10px 14px; text-align: left; font-weight: 600; font-size: 0.85rem; }
    td { padding: 9px 14px; border-bottom: 1px solid #eee; font-size: 0.9rem; vertical-align: top; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #f9f9f9; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: 600; }
    .badge-on { background: #d4edda; color: #155724; }
    .badge-off { background: #f8d7da; color: #721c24; }
    .badge-ok { background: #d4edda; color: #155724; }
    .badge-fail { background: #f8d7da; color: #721c24; }
    .badge-run { background: #fff3cd; color: #856404; }
    button { padding: 5px 12px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.82rem; }
    .btn-view { background: #3498db; color: #fff; }
    .btn-view:hover { background: #2980b9; }
    .btn-trigger { background: #27ae60; color: #fff; margin-left: 6px; }
    .btn-trigger:hover { background: #219150; }
    .btn-refresh { background: #2c3e50; color: #fff; padding: 7px 16px; font-size: 0.88rem; margin-bottom: 16px; border-radius: 4px; }
    .btn-refresh:hover { background: #1a252f; }
    #history-section { margin-top: 28px; }
    #history-title { font-size: 1.05rem; color: #2c3e50; }
    pre { white-space: pre-wrap; word-break: break-all; font-size: 0.78rem; max-height: 80px; overflow-y: auto; background: #f0f0f0; padding: 4px 6px; border-radius: 3px; }
    .empty { color: #888; font-style: italic; padding: 12px 0; }
    #status { font-size: 0.82rem; color: #888; margin-bottom: 14px; }
  </style>
</head>
<body>
  <h1>Job Scheduler</h1>
  <button class="btn-refresh" onclick="loadJobs()">Refresh</button>
  <div id="status"></div>
  <table id="jobs-table">
    <thead>
      <tr>
        <th>Name</th>
        <th>Command</th>
        <th>Schedule</th>
        <th>Active</th>
        <th>Created</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody id="jobs-body">
      <tr><td colspan="6" class="empty">Loading...</td></tr>
    </tbody>
  </table>

  <div id="history-section" style="display:none">
    <h2 id="history-title"></h2>
    <table id="history-table">
      <thead>
        <tr>
          <th>Started</th>
          <th>Finished</th>
          <th>Exit Code</th>
          <th>Triggered Manually</th>
          <th>stdout</th>
          <th>stderr</th>
        </tr>
      </thead>
      <tbody id="history-body"></tbody>
    </table>
  </div>

  <script>
    let _currentJobId = null;

    async function api(method, path, body) {
      const opts = { method, headers: { 'Content-Type': 'application/json' } };
      if (body !== undefined) opts.body = JSON.stringify(body);
      const r = await fetch(path, opts);
      if (r.status === 204) return null;
      return r.json();
    }

    function fmtDate(iso) {
      if (!iso) return '—';
      return new Date(iso).toLocaleString();
    }

    async function loadJobs() {
      const tbody = document.getElementById('jobs-body');
      const status = document.getElementById('status');
      status.textContent = 'Loading...';
      try {
        const jobs = await api('GET', '/jobs');
        status.textContent = `${jobs.length} job(s) — last refreshed ${new Date().toLocaleTimeString()}`;
        if (jobs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="empty">No jobs yet. Use POST /jobs to create one.</td></tr>';
          return;
        }
        tbody.innerHTML = jobs.map(j => `
          <tr>
            <td>${esc(j.name)}</td>
            <td><code>${esc(j.command)}</code></td>
            <td><code>${esc(j.cron_expression)}</code></td>
            <td><span class="badge ${j.is_active ? 'badge-on' : 'badge-off'}">${j.is_active ? 'active' : 'inactive'}</span></td>
            <td>${fmtDate(j.created_at)}</td>
            <td>
              <button class="btn-view" onclick="loadHistory('${esc(j.id)}', '${esc(j.name)}')">History</button>
              <button class="btn-trigger" onclick="triggerJob('${esc(j.id)}', '${esc(j.name)}')">Run Now</button>
            </td>
          </tr>`).join('');
      } catch (e) {
        status.textContent = 'Error loading jobs: ' + e.message;
      }
    }

    async function loadHistory(jobId, jobName) {
      _currentJobId = jobId;
      const section = document.getElementById('history-section');
      const title = document.getElementById('history-title');
      const tbody = document.getElementById('history-body');
      section.style.display = '';
      title.textContent = 'Run history: ' + jobName;
      tbody.innerHTML = '<tr><td colspan="6" class="empty">Loading...</td></tr>';
      try {
        const runs = await api('GET', `/jobs/${jobId}/history`);
        if (runs.length === 0) {
          tbody.innerHTML = '<tr><td colspan="6" class="empty">No runs yet.</td></tr>';
          return;
        }
        tbody.innerHTML = runs.map(r => {
          const code = r.exit_code === null ? '<span class="badge badge-run">running</span>'
            : r.exit_code === 0 ? `<span class="badge badge-ok">0</span>`
            : `<span class="badge badge-fail">${r.exit_code}</span>`;
          return `<tr>
            <td>${fmtDate(r.started_at)}</td>
            <td>${fmtDate(r.finished_at)}</td>
            <td>${code}</td>
            <td>${r.triggered_manually ? 'yes' : 'no'}</td>
            <td>${r.stdout ? '<pre>' + esc(r.stdout) + '</pre>' : '—'}</td>
            <td>${r.stderr ? '<pre>' + esc(r.stderr) + '</pre>' : '—'}</td>
          </tr>`;
        }).join('');
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" class="empty">Error: ${esc(e.message)}</td></tr>`;
      }
    }

    async function triggerJob(jobId, jobName) {
      const status = document.getElementById('status');
      status.textContent = `Triggering ${jobName}...`;
      try {
        await api('POST', `/jobs/${jobId}/trigger`);
        status.textContent = `Job "${jobName}" triggered.`;
        if (_currentJobId === jobId) loadHistory(jobId, jobName);
      } catch (e) {
        status.textContent = 'Error triggering job: ' + e.message;
      }
    }

    function esc(s) {
      return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }

    loadJobs();
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui():
    """Serve the web UI."""
    return _UI_HTML


@app.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    if db.query(Job).filter(Job.name == payload.name).first():
        raise HTTPException(status_code=409, detail="A job with that name already exists")

    job = Job(name=payload.name, command=payload.command, cron_expression=payload.cron_expression)
    db.add(job)
    db.commit()
    db.refresh(job)

    if not os.getenv("TESTING"):
        add_job(job)

    return job


@app.get("/jobs", response_model=List[JobResponse])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(Job).all()


@app.delete("/jobs/{job_id}", status_code=204)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    remove_job(job_id)
    db.delete(job)
    db.commit()


@app.get("/jobs/{job_id}/history", response_model=List[RunHistoryResponse])
def get_job_history(job_id: str, db: Session = Depends(get_db)):
    if not db.query(Job).filter(Job.id == job_id).first():
        raise HTTPException(status_code=404, detail="Job not found")
    return (
        db.query(RunHistory)
        .filter(RunHistory.job_id == job_id)
        .order_by(RunHistory.started_at.desc())
        .all()
    )


@app.post("/jobs/{job_id}/trigger", response_model=RunHistoryResponse, status_code=202)
def trigger_job(job_id: str, db: Session = Depends(get_db)):
    if not db.query(Job).filter(Job.id == job_id).first():
        raise HTTPException(status_code=404, detail="Job not found")

    execute_job(job_id, triggered_manually=True, db=db)

    run = (
        db.query(RunHistory)
        .filter(RunHistory.job_id == job_id, RunHistory.triggered_manually == True)
        .order_by(RunHistory.started_at.desc())
        .first()
    )
    return run
