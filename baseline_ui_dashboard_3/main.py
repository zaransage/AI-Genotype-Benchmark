from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from db import SQLiteStore, sqlite_store
from models import (
    Dashboard,
    DashboardCreate,
    DashboardDetail,
    DashboardResponse,
    MetricValue,
    MetricValueCreate,
    Widget,
    WidgetCreate,
    WidgetResponse,
)
from storage import InMemoryStore

app = FastAPI(title="Metrics Dashboard API", version="1.0.0")

_TEMPLATE = Path(__file__).parent / "templates" / "index.html"


def get_store() -> SQLiteStore:
    return sqlite_store


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------


@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse(_TEMPLATE.read_text())


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------


@app.post("/dashboards", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
def create_dashboard(body: DashboardCreate, db: InMemoryStore = Depends(get_store)):
    dashboard = Dashboard(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        created_at=datetime.now(timezone.utc),
    )
    db.save_dashboard(dashboard)
    return DashboardResponse(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        created_at=dashboard.created_at,
        widget_count=0,
    )


@app.get("/dashboards", response_model=list[DashboardResponse])
def list_dashboards(db: InMemoryStore = Depends(get_store)):
    return [
        DashboardResponse(
            id=d.id,
            name=d.name,
            description=d.description,
            created_at=d.created_at,
            widget_count=len(d.widgets),
        )
        for d in db.get_all_dashboards()
    ]


@app.get("/dashboards/{dashboard_id}", response_model=DashboardDetail)
def get_dashboard(dashboard_id: str, db: InMemoryStore = Depends(get_store)):
    dashboard = _require_dashboard(db, dashboard_id)
    return _dashboard_detail(dashboard)


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------


@app.post(
    "/dashboards/{dashboard_id}/widgets",
    response_model=WidgetResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_widget(
    dashboard_id: str,
    body: WidgetCreate,
    db: InMemoryStore = Depends(get_store),
):
    dashboard = _require_dashboard(db, dashboard_id)
    widget = Widget(
        id=str(uuid.uuid4()),
        dashboard_id=dashboard_id,
        name=body.name,
        unit=body.unit,
    )
    dashboard.widgets[widget.id] = widget
    db.save_dashboard(dashboard)
    return _widget_response(widget)


@app.get("/dashboards/{dashboard_id}/widgets", response_model=list[WidgetResponse])
def list_widgets(dashboard_id: str, db: InMemoryStore = Depends(get_store)):
    dashboard = _require_dashboard(db, dashboard_id)
    return [_widget_response(w) for w in dashboard.widgets.values()]


@app.get("/dashboards/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
def get_widget(dashboard_id: str, widget_id: str, db: InMemoryStore = Depends(get_store)):
    dashboard = _require_dashboard(db, dashboard_id)
    widget = _require_widget(dashboard, widget_id)
    return _widget_response(widget)


# ---------------------------------------------------------------------------
# Metric values
# ---------------------------------------------------------------------------


@app.post(
    "/dashboards/{dashboard_id}/widgets/{widget_id}/values",
    response_model=WidgetResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_metric_value(
    dashboard_id: str,
    widget_id: str,
    body: MetricValueCreate,
    db: InMemoryStore = Depends(get_store),
):
    dashboard = _require_dashboard(db, dashboard_id)
    widget = _require_widget(dashboard, widget_id)
    widget.values.append(MetricValue(value=body.value, timestamp=body.timestamp))
    db.save_dashboard(dashboard)
    return _widget_response(widget)


@app.get(
    "/dashboards/{dashboard_id}/widgets/{widget_id}/values",
    response_model=list[MetricValue],
)
def get_metric_values(
    dashboard_id: str,
    widget_id: str,
    db: InMemoryStore = Depends(get_store),
):
    dashboard = _require_dashboard(db, dashboard_id)
    widget = _require_widget(dashboard, widget_id)
    return widget.values


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_dashboard(db: InMemoryStore, dashboard_id: str) -> Dashboard:
    dashboard = db.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


def _require_widget(dashboard: Dashboard, widget_id: str) -> Widget:
    widget = dashboard.widgets.get(widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget


def _widget_response(widget: Widget) -> WidgetResponse:
    return WidgetResponse(
        id=widget.id,
        dashboard_id=widget.dashboard_id,
        name=widget.name,
        unit=widget.unit,
        current_value=widget.current_value,
    )


def _dashboard_detail(dashboard: Dashboard) -> DashboardDetail:
    return DashboardDetail(
        id=dashboard.id,
        name=dashboard.name,
        description=dashboard.description,
        created_at=dashboard.created_at,
        widgets=[_widget_response(w) for w in dashboard.widgets.values()],
    )
