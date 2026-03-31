"""
domain/game/core/adaptors/web_ui_adaptor.py

Inbound adaptor: serves the browser-based tic-tac-toe UI as a FastAPI router.
The HTML file path is injected by the composition root so the adaptor remains
independent of the filesystem layout (AI_CONTRACT §8, ADR 0006).
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


class WebUIAdaptor:
    """Returns an APIRouter with a single GET / route that serves the game HTML."""

    def __init__(self, html_path: str) -> None:
        self._html_path = html_path

    def create_router(self) -> APIRouter:
        router    = APIRouter()
        html_path = self._html_path

        @router.get("/", response_class=HTMLResponse, include_in_schema=False)
        def game_ui() -> str:
            with open(html_path, encoding="utf-8") as fh:
                return fh.read()

        return router
