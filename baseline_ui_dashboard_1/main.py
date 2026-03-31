from datetime import datetime, timezone
from typing import List
import uuid

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from models import (
    Dashboard,
    DashboardCreate,
    MetricValue,
    MetricValueCreate,
    Widget,
    WidgetCreate,
)
from db import store

app = FastAPI(title="Metrics Dashboard API", version="1.0.0")


def _now() -> datetime:
    return datetime.now(timezone.utc)


@app.post("/dashboards", response_model=Dashboard, status_code=status.HTTP_201_CREATED)
def create_dashboard(payload: DashboardCreate) -> Dashboard:
    dashboard = Dashboard(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        created_at=_now(),
    )
    return store.add_dashboard(dashboard)


@app.get("/dashboards", response_model=List[Dashboard])
def list_dashboards() -> List[Dashboard]:
    return store.list_dashboards()


@app.get("/dashboards/{dashboard_id}", response_model=Dashboard)
def get_dashboard(dashboard_id: str) -> Dashboard:
    dashboard = store.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@app.post(
    "/dashboards/{dashboard_id}/widgets",
    response_model=Widget,
    status_code=status.HTTP_201_CREATED,
)
def add_widget(dashboard_id: str, payload: WidgetCreate) -> Widget:
    dashboard = store.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = Widget(
        id=str(uuid.uuid4()),
        name=payload.name,
        unit=payload.unit,
        created_at=_now(),
    )
    dashboard.widgets.append(widget)
    store.save_dashboard(dashboard)
    return widget


@app.get("/dashboards/{dashboard_id}/widgets/{widget_id}", response_model=Widget)
def get_widget(dashboard_id: str, widget_id: str) -> Widget:
    dashboard = store.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = next((w for w in dashboard.widgets if w.id == widget_id), None)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget


@app.post(
    "/dashboards/{dashboard_id}/widgets/{widget_id}/metrics",
    response_model=MetricValue,
    status_code=status.HTTP_201_CREATED,
)
def post_metric(
    dashboard_id: str, widget_id: str, payload: MetricValueCreate
) -> MetricValue:
    dashboard = store.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = next((w for w in dashboard.widgets if w.id == widget_id), None)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    metric = MetricValue(
        id=str(uuid.uuid4()),
        value=payload.value,
        timestamp=payload.timestamp or _now(),
    )
    widget.metrics.append(metric)
    store.save_dashboard(dashboard)
    return metric


@app.get(
    "/dashboards/{dashboard_id}/widgets/{widget_id}/metrics",
    response_model=List[MetricValue],
)
def list_metrics(dashboard_id: str, widget_id: str) -> List[MetricValue]:
    dashboard = store.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    widget = next((w for w in dashboard.widgets if w.id == widget_id), None)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    return widget.metrics


_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Metrics Dashboards</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background: #f5f5f5; }
    h1 { color: #333; }
    .card { background: #fff; border-radius: 8px; padding: 1rem 1.5rem; margin: 0.75rem 0; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
    .card h2 { margin: 0 0 .25rem; font-size: 1.1rem; }
    .card p { margin: 0; color: #666; font-size: .9rem; }
    a { color: #0066cc; text-decoration: none; }
    a:hover { text-decoration: underline; }
    #error { color: red; }
  </style>
</head>
<body>
  <h1>Metrics Dashboards</h1>
  <p id="error"></p>
  <div id="list"></div>
  <script>
    async function load() {
      try {
        const res = await fetch('/dashboards');
        if (!res.ok) throw new Error('Failed to load dashboards');
        const dashboards = await res.json();
        const el = document.getElementById('list');
        if (dashboards.length === 0) {
          el.innerHTML = '<p>No dashboards yet. Use the API to create one.</p>';
          return;
        }
        el.innerHTML = dashboards.map(d => `
          <div class="card">
            <h2><a href="/ui/dashboards/${d.id}">${d.name}</a></h2>
            <p>${d.description || ''} &mdash; ${d.widgets.length} widget(s)</p>
          </div>`).join('');
      } catch (e) {
        document.getElementById('error').textContent = e.message;
      }
    }
    load();
  </script>
</body>
</html>"""

_DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Dashboard</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background: #f5f5f5; }
    h1, h2, h3 { color: #333; }
    .card { background: #fff; border-radius: 8px; padding: 1rem 1.5rem; margin: 0.75rem 0; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
    .metric-row { display: flex; justify-content: space-between; padding: .25rem 0; border-bottom: 1px solid #eee; font-size: .9rem; }
    .metric-row:last-child { border-bottom: none; }
    .value { font-weight: bold; color: #0066cc; }
    .timestamp { color: #888; }
    a { color: #0066cc; text-decoration: none; }
    a:hover { text-decoration: underline; }
    #error { color: red; }
    .no-data { color: #999; font-style: italic; }
  </style>
</head>
<body>
  <p><a href="/">&larr; All Dashboards</a></p>
  <h1 id="dash-name">Loading&hellip;</h1>
  <p id="dash-desc"></p>
  <p id="error"></p>
  <div id="widgets"></div>
  <script>
    const dashId = window.location.pathname.split('/').pop();
    async function load() {
      try {
        const res = await fetch('/dashboards/' + dashId);
        if (res.status === 404) { document.getElementById('error').textContent = 'Dashboard not found.'; return; }
        if (!res.ok) throw new Error('Failed to load dashboard');
        const d = await res.json();
        document.title = d.name;
        document.getElementById('dash-name').textContent = d.name;
        document.getElementById('dash-desc').textContent = d.description || '';
        const el = document.getElementById('widgets');
        if (d.widgets.length === 0) {
          el.innerHTML = '<div class="card"><p class="no-data">No widgets on this dashboard.</p></div>';
          return;
        }
        el.innerHTML = d.widgets.map(w => {
          const unit = w.unit ? ' ' + w.unit : '';
          const rows = w.metrics.length === 0
            ? '<p class="no-data">No readings yet.</p>'
            : w.metrics.slice().reverse().map(m =>
                `<div class="metric-row">
                  <span class="value">${m.value}${unit}</span>
                  <span class="timestamp">${new Date(m.timestamp).toLocaleString()}</span>
                </div>`).join('');
          const latest = w.metrics.length > 0
            ? w.metrics[w.metrics.length - 1].value + unit
            : 'n/a';
          return `<div class="card">
            <h3>${w.name} &mdash; latest: <span class="value">${latest}</span></h3>
            ${rows}
          </div>`;
        }).join('');
      } catch (e) {
        document.getElementById('error').textContent = e.message;
      }
    }
    load();
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui_index() -> HTMLResponse:
    return HTMLResponse(content=_INDEX_HTML)


@app.get("/ui/dashboards/{dashboard_id}", response_class=HTMLResponse, include_in_schema=False)
def ui_dashboard(dashboard_id: str) -> HTMLResponse:
    dashboard = store.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return HTMLResponse(content=_DASHBOARD_HTML)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
