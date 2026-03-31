"""
Composition root — the only place that knows about concrete types.

Wires repositories → commands → adaptors → FastAPI app.
logging.basicConfig() is called here (application boundary only).
"""
import logging
import sqlite3

import uvicorn
from fastapi import FastAPI

from domain.core.adaptors.fastapi_router import MetricsDashboardAdaptor, create_router
from domain.core.adaptors.web_ui_router import WebUIAdaptor, create_web_ui_router
from domain.core.commands import (
    AddWidgetCommand,
    CreateDashboardCommand,
    ListDashboardsCommand,
    ListWidgetsCommand,
    PostMetricValueCommand,
    ReadWidgetValuesCommand,
)
from domain.core.ports.sqlite_dashboard_repository import SqliteDashboardRepository
from domain.core.ports.sqlite_metric_value_repository import SqliteMetricValueRepository
from domain.core.ports.sqlite_widget_repository import SqliteWidgetRepository

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

# ---- SQLite connection (single shared connection for the process) -----------
_db = sqlite3.connect("dashboards.db", check_same_thread=False)

# ---- Repositories ----------------------------------------------------------
_dash_repo   = SqliteDashboardRepository(_db)
_widget_repo = SqliteWidgetRepository(_db)
_value_repo  = SqliteMetricValueRepository(_db)

# ---- Commands --------------------------------------------------------------
_create_cmd       = CreateDashboardCommand(dashboards=_dash_repo)
_list_cmd         = ListDashboardsCommand(dashboards=_dash_repo)
_add_widget_cmd   = AddWidgetCommand(dashboards=_dash_repo, widgets=_widget_repo)
_post_value_cmd   = PostMetricValueCommand(widgets=_widget_repo, metric_values=_value_repo)
_read_values_cmd  = ReadWidgetValuesCommand(widgets=_widget_repo, metric_values=_value_repo)
_list_widgets_cmd = ListWidgetsCommand(widgets=_widget_repo)

# ---- REST adaptor ----------------------------------------------------------
_rest_adaptor = MetricsDashboardAdaptor(
    create_cmd=_create_cmd,
    list_cmd=_list_cmd,
    add_widget_cmd=_add_widget_cmd,
    post_value_cmd=_post_value_cmd,
    read_values_cmd=_read_values_cmd,
)

# ---- Web UI adaptor --------------------------------------------------------
_web_ui_adaptor = WebUIAdaptor(
    list_dashboards_cmd=_list_cmd,
    list_widgets_cmd=_list_widgets_cmd,
    read_values_cmd=_read_values_cmd,
)

# ---- FastAPI app -----------------------------------------------------------
app = FastAPI(
    title="Metrics Dashboard API",
    description="REST API for creating dashboards, adding widgets, and recording metric values.",
    version="0.1.0",
)
app.include_router(create_router(_rest_adaptor))
app.include_router(create_web_ui_router(_web_ui_adaptor))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)
