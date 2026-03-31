"""
main.py — composition root.

This is the ONLY file that:
  - knows about concrete types (SqliteDashboardRepository, DashboardController, UiRouter)
  - wires dependencies together
  - handles framework concerns (HTTPException, HTMLResponse, logging setup)

Domain and adaptor classes remain framework-agnostic.
"""
import logging
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from domain.dashboard.core.adaptors.dashboard_controller       import DashboardController
from domain.dashboard.core.adaptors.ui_router                  import UiRouter
from domain.dashboard.core.ports.sqlite_dashboard_repository   import SqliteDashboardRepository

# ---------------------------------------------------------------------------
# Application boundary — logging is configured here, never inside classes.
# ---------------------------------------------------------------------------
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dependency wiring — composition root assembles concrete types.
# ---------------------------------------------------------------------------
_repository  = SqliteDashboardRepository(db_path="dashboards.db")
_controller  = DashboardController(repository=_repository)
_ui_router   = UiRouter(controller=_controller)

app = FastAPI(
    title       = "Metrics Dashboard API",
    description = "Hexagonal architecture — ports & adaptors pattern",
    version     = "0.1.0",
)

# ---------------------------------------------------------------------------
# Request models (Pydantic — lives at the route boundary only)
# ---------------------------------------------------------------------------

class CreateDashboardRequest(BaseModel):
    name: str

class AddWidgetRequest(BaseModel):
    name: str
    unit: str

class PostMetricRequest(BaseModel):
    value:     float
    timestamp: str

# ---------------------------------------------------------------------------
# REST API routes
# ---------------------------------------------------------------------------

@app.post("/dashboards", status_code=201)
def create_dashboard(body: CreateDashboardRequest):
    try:
        dashboard = _controller.create_dashboard(name=body.name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    logger.info("Created dashboard id=%s name=%s", dashboard.id, dashboard.name)
    return asdict(dashboard)


@app.get("/dashboards")
def list_dashboards():
    dashboards = _controller.list_dashboards()
    return [asdict(d) for d in dashboards]


@app.post("/dashboards/{dashboard_id}/widgets", status_code=201)
def add_widget(dashboard_id: str, body: AddWidgetRequest):
    try:
        widget = _controller.add_widget(
            dashboard_id = dashboard_id,
            name         = body.name,
            unit         = body.unit,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    logger.info("Added widget id=%s to dashboard id=%s", widget.id, dashboard_id)
    return JSONResponse(status_code=201, content=asdict(widget))


@app.post("/dashboards/{dashboard_id}/widgets/{widget_id}/metrics", status_code=201)
def post_metric(dashboard_id: str, widget_id: str, body: PostMetricRequest):
    try:
        mv = _controller.post_metric(
            dashboard_id = dashboard_id,
            widget_id    = widget_id,
            value        = body.value,
            timestamp    = body.timestamp,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    logger.info(
        "Posted metric value=%s timestamp=%s to widget id=%s",
        mv.value, mv.timestamp, widget_id,
    )
    return JSONResponse(status_code=201, content=asdict(mv))


@app.get("/dashboards/{dashboard_id}/widgets/{widget_id}")
def get_widget(dashboard_id: str, widget_id: str):
    try:
        widget = _controller.get_widget(
            dashboard_id = dashboard_id,
            widget_id    = widget_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    return asdict(widget)


# ---------------------------------------------------------------------------
# HTML UI routes (inbound adaptor: UiRouter)
# ---------------------------------------------------------------------------

@app.get("/ui", response_class=HTMLResponse)
def ui_dashboard_list():
    return _ui_router.render_dashboard_list()


@app.get("/ui/dashboards/{dashboard_id}", response_class=HTMLResponse)
def ui_dashboard_detail(dashboard_id: str):
    try:
        return _ui_router.render_dashboard_detail(dashboard_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
