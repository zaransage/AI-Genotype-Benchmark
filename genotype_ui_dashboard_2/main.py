"""
Composition root — the only place that knows about concrete types (ADR-0008, AI_CONTRACT.md §8).

Wires:
  SqliteDashboardRepo  →  commands  →  REST routes  →  FastAPI app
                                    →  Web UI routes  →  FastAPI app

logging.basicConfig() belongs here, not inside any class constructor (ADR-0006).
"""

import logging

import uvicorn
from fastapi import FastAPI

from domain.dashboard.core.adaptors.rest_routes import build_router
from domain.dashboard.core.adaptors.web_ui_routes import build_web_ui_router
from domain.dashboard.core.ports.sqlite_dashboard_repo import (
    DEFAULT_DB_PATH,
    SqliteDashboardRepo,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

logger = logging.getLogger(__name__)


def create_app(db_path: str = DEFAULT_DB_PATH) -> FastAPI:
    repo = SqliteDashboardRepo(db_path=db_path)
    app = FastAPI(
        title       = "Metrics Dashboard API",
        description = "REST API for managing dashboards and metric widgets.",
        version     = "1.0.0",
    )
    app.include_router(build_router(repo=repo))
    app.include_router(build_web_ui_router())
    return app


app = create_app()

if __name__ == "__main__":
    logger.info("Starting Metrics Dashboard API")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
