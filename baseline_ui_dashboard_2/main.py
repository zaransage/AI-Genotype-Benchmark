import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse

from models import (
    Dashboard,
    DashboardCreate,
    MetricPoint,
    MetricPointCreate,
    Widget,
    WidgetCreate,
)
from db_store import SQLiteStore

app = FastAPI(title="Metrics Dashboard API", version="1.0.0")
store = SQLiteStore()

_TEMPLATES = Path(__file__).parent / "templates"


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Web UI
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def ui():
    return HTMLResponse((_TEMPLATES / "index.html").read_text())


# ---------------------------------------------------------------------------
# Dashboards
# ---------------------------------------------------------------------------


@app.post("/dashboards", response_model=Dashboard, status_code=status.HTTP_201_CREATED)
def create_dashboard(body: DashboardCreate):
    dashboard = Dashboard(
        id=str(uuid.uuid4()),
        name=body.name,
        description=body.description,
        created_at=_now(),
    )
    return store.create_dashboard(dashboard)


@app.get("/dashboards", response_model=list[Dashboard])
def list_dashboards():
    return store.list_dashboards()


@app.get("/dashboards/{dashboard_id}", response_model=Dashboard)
def get_dashboard(dashboard_id: str):
    dashboard = store.get_dashboard(dashboard_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------


@app.post(
    "/dashboards/{dashboard_id}/widgets",
    response_model=Widget,
    status_code=status.HTTP_201_CREATED,
)
def create_widget(dashboard_id: str, body: WidgetCreate):
    if store.get_dashboard(dashboard_id) is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    widget = Widget(
        id=str(uuid.uuid4()),
        dashboard_id=dashboard_id,
        name=body.name,
        unit=body.unit,
        created_at=_now(),
    )
    return store.create_widget(widget)


@app.get("/dashboards/{dashboard_id}/widgets", response_model=list[Widget])
def list_widgets(dashboard_id: str):
    if store.get_dashboard(dashboard_id) is None:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return store.list_widgets(dashboard_id)


@app.get("/dashboards/{dashboard_id}/widgets/{widget_id}", response_model=Widget)
def get_widget(dashboard_id: str, widget_id: str):
    widget = store.get_widget(widget_id)
    if widget is None or widget.dashboard_id != dashboard_id:
        raise HTTPException(status_code=404, detail="Widget not found")
    return widget


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


@app.post(
    "/dashboards/{dashboard_id}/widgets/{widget_id}/metrics",
    response_model=MetricPoint,
    status_code=status.HTTP_201_CREATED,
)
def post_metric(dashboard_id: str, widget_id: str, body: MetricPointCreate):
    widget = store.get_widget(widget_id)
    if widget is None or widget.dashboard_id != dashboard_id:
        raise HTTPException(status_code=404, detail="Widget not found")

    point = MetricPoint(value=body.value, timestamp=_now(), labels=body.labels)
    widget.history.append(point)
    widget.latest_value = point.value
    widget.latest_timestamp = point.timestamp
    store.update_widget(widget)
    return point
