"""
Inbound web UI adaptor: serves the browser-playable game interface.

Reads and returns the static HTML page; all game interaction is handled
by client-side JavaScript calling the REST API at /api/v1/.
"""

from __future__ import annotations

import pathlib

from fastapi           import APIRouter
from fastapi.responses import HTMLResponse

router: APIRouter = APIRouter()

_STATIC_DIR = pathlib.Path(__file__).parent / "static"


@router.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the single-page Tic-Tac-Toe web UI."""
    return (_STATIC_DIR / "index.html").read_text(encoding="utf-8")
